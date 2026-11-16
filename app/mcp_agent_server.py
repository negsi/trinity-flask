"""
Agent-Specific Low-Level MCP Server Factory and Session Management (MCP SDK v2).

Provides a dynamic factory using `mcp.server.Server` with `on_*` handlers and
bridges synchronous Flask WSGI SSE streams with asynchronous MCP anyio memory streams.
"""

import asyncio
import json
import logging
import queue
import re
import threading
import uuid
from typing import Any, Generator

import anyio
from flask import Flask
import mcp.types as types
from mcp.server import Server, ServerRequestContext
from mcp.shared.message import SessionMessage

from app.domain.errors import ValidationError
from app.services.agent.agent_orchestrator import AgentOrchestrator
from app.services.agent.agent_service import AgentService
from app.services.agent.constants import (
    PROTOCOL_ATTACHMENTS,
    PROTOCOL_TASK_CHAIN,
    PROTOCOL_THOUGHT,
)
from app.services.infrastructure.security_context import SecurityContextService
from app.services.messaging.messaging_service import MessagingService

logger = logging.getLogger(__name__)


def _sanitize_tool_name(name: str) -> str:
    """Converts an agent name into a valid MCP tool identifier."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return f"ask_{sanitized}" if sanitized else "ask_trinity_agent"


class McpSession:
    """
    Represents an active MCP SSE client connection tied to a specific agent
    and a persistent Trinity conversation context.
    """

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        conversation_id: str,
        server: Server,
        flask_app: Flask,
    ) -> None:
        self.session_id = session_id
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.server = server
        self.flask_app = flask_app

        # Outgoing queue yielding formatted SSE events to the Flask response generator
        self.outgoing_queue: queue.Queue[dict[str, str] | None] = queue.Queue()

        # Asyncio event loop & incoming queue running inside the session thread
        self._loop: asyncio.AbstractEventLoop | None = None
        self._incoming_async_queue: asyncio.Queue[dict[str, Any] | None] | None = None
        self._ready_event = threading.Event()
        self._closed = False

    def start(self) -> None:
        """Starts the background thread running the async MCP server session."""
        thread = threading.Thread(
            target=self._run_thread,
            name=f"mcp-session-{self.session_id[:8]}",
            daemon=True,
        )
        thread.start()
        self._ready_event.wait(timeout=5.0)

    def _run_thread(self) -> None:
        """Executes the asyncio event loop inside the Flask application context."""
        with self.flask_app.app_context():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._async_session_runner())
            except Exception as exc:
                logger.error(
                    "Unhandled error in MCP session '%s': %s",
                    self.session_id,
                    exc,
                    exc_info=True,
                )
            finally:
                self.outgoing_queue.put(None)
                self._loop.close()

    async def _async_session_runner(self) -> None:
        """Bridges anyio memory object streams between Flask HTTP requests and `mcp.server.Server`."""
        self._incoming_async_queue = asyncio.Queue()
        self._ready_event.set()

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        async def _pump_incoming() -> None:
            """Reads JSON-RPC payloads posted via HTTP and feeds them into the MCP server."""
            assert self._incoming_async_queue is not None
            async with read_stream_writer:
                while not self._closed:
                    raw_payload = await self._incoming_async_queue.get()
                    if raw_payload is None:
                        break
                    try:
                        # MCP v2: JSONRPCMessage is a union validated via jsonrpc_message_adapter
                        rpc_message = types.jsonrpc_message_adapter.validate_python(
                            raw_payload
                        )
                        await read_stream_writer.send(SessionMessage(rpc_message))
                    except Exception as exc:
                        logger.warning(
                            "Invalid JSON-RPC payload in MCP session '%s': %s",
                            self.session_id,
                            exc,
                        )
                        await read_stream_writer.send(exc)

        async def _pump_outgoing() -> None:
            """Reads responses from the MCP server and pushes them to the Flask SSE queue."""
            async with write_stream_reader:
                async for session_msg in write_stream_reader:
                    rpc_obj = (
                        session_msg.message
                        if isinstance(session_msg, SessionMessage)
                        else session_msg
                    )
                    serialized = rpc_obj.model_dump_json(
                        by_alias=True, exclude_none=True
                    )
                    self.outgoing_queue.put({"event": "message", "data": serialized})

        async with anyio.create_task_group() as tg:
            tg.start_soon(_pump_incoming)
            tg.start_soon(_pump_outgoing)
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )
            tg.cancel_scope.cancel()

    def post_message(self, payload: dict[str, Any]) -> None:
        """Thread-safe method to enqueue an incoming JSON-RPC client message."""
        if self._closed or not self._loop or not self._incoming_async_queue:
            raise ValidationError("MCP session is inactive or already closed.")
        self._loop.call_soon_threadsafe(
            self._incoming_async_queue.put_nowait, payload
        )

    def close(self) -> None:
        """Cleanly terminates the MCP session and its background event loop."""
        if self._closed:
            return
        self._closed = True
        if self._loop and self._incoming_async_queue:
            self._loop.call_soon_threadsafe(
                self._incoming_async_queue.put_nowait, None
            )
        self.outgoing_queue.put(None)


class McpAgentServerFactory:
    """
    Factory and registry for creating agent-scoped low-level MCP servers
    and managing active SSE sessions.
    """

    def __init__(
        self,
        agent_service: AgentService,
        messaging_service: MessagingService,
        agent_orchestrator: AgentOrchestrator,
        security_context_service: SecurityContextService,
    ) -> None:
        self.agent_service = agent_service
        self.messaging_service = messaging_service
        self.agent_orchestrator = agent_orchestrator
        self.security_context_service = security_context_service
        self._sessions: dict[str, McpSession] = {}
        self._lock = threading.Lock()

    def create_server(
        self,
        agent_id: str,
        conversation_id: str,
        flask_app: Flask,
    ) -> Server:
        """
        Instantiates a low-level `mcp.server.Server` scoped to a single Trinity agent.
        Uses MCP v2 `on_list_tools` and `on_call_tool` callbacks with pure dictionary
        JSON-schema definitions (no FastMCP / MCPServer or type-hint schema inference).
        """
        agent = self.agent_service.get_agent(agent_id)
        server_name = f"trinity-agent-{agent.name.lower().replace(' ', '-')}"

        async def handle_list_tools(
            ctx: ServerRequestContext,
            params: types.PaginatedRequestParams | None,
        ) -> types.ListToolsResult:
            """Dynamically loads agent metadata and attached datasources from the database."""

            def _load_tools_sync() -> types.ListToolsResult:
                with flask_app.app_context():
                    current_agent = self.agent_service.get_agent(agent_id)
                    tool_name = _sanitize_tool_name(current_agent.name)

                    description_parts = [
                        f"Trinity AI Agent: {current_agent.name}.",
                        current_agent.description
                        or "Executes complex tasks, research, and tool chains autonomously.",
                    ]

                    if current_agent.datasources:
                        ds_names = ", ".join(
                            ds.filename for ds in current_agent.datasources
                        )
                        description_parts.append(
                            f"Attached Knowledge Base Datasources: {ds_names}."
                        )

                    # Pure dictionary JSON Schema definition (must include "type": "object" in v2)
                    input_schema: dict[str, Any] = {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": (
                                    "The prompt, question, or task instruction to send to the "
                                    f"'{current_agent.name}' agent. Conversation memory and "
                                    "attached datasources are automatically maintained."
                                ),
                            }
                        },
                        "required": ["message"],
                        "additionalProperties": False,
                    }

                    return types.ListToolsResult(
                        tools=[
                            types.Tool(
                                name=tool_name,
                                description=" ".join(description_parts),
                                input_schema=input_schema,
                            )
                        ]
                    )

            return await anyio.to_thread.run_sync(_load_tools_sync)

        async def handle_call_tool(
            ctx: ServerRequestContext,
            params: types.CallToolRequestParams,
        ) -> types.CallToolResult:
            """Executes the Trinity agent via AgentOrchestrator using the session's conversation_id."""
            try:
                args = params.arguments or {}
                user_message = str(args.get("message", "")).strip()

                if not user_message:
                    return types.CallToolResult(
                        content=[
                            types.TextContent(
                                type="text",
                                text="Error: Missing required 'message' argument in tool call.",
                            )
                        ],
                        is_error=True,
                    )

                def _execute_agent_sync() -> str:
                    with flask_app.app_context():
                        current_agent = self.agent_service.get_agent(agent_id)
                        expected_tool_name = _sanitize_tool_name(current_agent.name)

                        if params.name not in (
                            expected_tool_name,
                            "ask_agent",
                            current_agent.name,
                        ):
                            raise ValueError(
                                f"Unknown tool '{params.name}' for agent '{current_agent.name}'."
                            )

                        actor = self.security_context_service.get_current_actor()

                        # 1. Persist incoming user message in the fixed session conversation
                        saved_msg = self.messaging_service.send_message(
                            conversation_id=conversation_id,
                            sender_id=actor["id"],
                            sender_type=actor["type"],
                            sender_name=actor["name"],
                            text=user_message,
                            recipient_id=agent_id,
                            files=[],
                        )

                        resolved_conv_id = saved_msg.conversation_id

                        # 2. Run the full AgentOrchestrator (Base Prompt, Datasources, Memory & Task Chains)
                        stream_gen = self.agent_orchestrator.stream_agent_response(
                            user_text=user_message,
                            conversation_id=resolved_conv_id,
                            agent_id=agent_id,
                            agent_name=current_agent.name,
                            user_id=actor["id"],
                        )

                        collected_chunks: list[str] = []
                        created_attachments: list[dict[str, Any]] = []

                        for chunk in stream_gen:
                            if not chunk:
                                continue

                            # Skip internal UI thought and task-chain protocol markers
                            if (
                                PROTOCOL_THOUGHT in chunk
                                or PROTOCOL_TASK_CHAIN in chunk
                            ):
                                continue

                            if PROTOCOL_ATTACHMENTS in chunk:
                                idx = chunk.find(PROTOCOL_ATTACHMENTS)
                                raw_json = chunk[
                                    idx + len(PROTOCOL_ATTACHMENTS) :
                                ].strip()
                                try:
                                    parsed = json.loads(raw_json)
                                    created_attachments.extend(
                                        parsed.get("files", [])
                                    )
                                except Exception:
                                    pass
                                continue

                            stripped = chunk.strip()
                            if (
                                stripped == "[DONE]"
                                or stripped.startswith('{"type": "thought"')
                                or stripped.startswith('{"type":"thought"')
                                or (
                                    stripped.startswith("{")
                                    and '"type":"meta"' in stripped
                                )
                            ):
                                continue

                            collected_chunks.append(chunk)

                        final_response = "".join(collected_chunks).strip()
                        if created_attachments:
                            file_lines = [
                                f"- {f.get('filename')}: {f.get('url')}"
                                for f in created_attachments
                            ]
                            final_response += (
                                "\n\nGenerated Workspace Files:\n"
                                + "\n".join(file_lines)
                            )

                        return final_response or "Task completed."

                result_text = await anyio.to_thread.run_sync(_execute_agent_sync)
                return types.CallToolResult(
                    content=[types.TextContent(type="text", text=result_text)],
                    is_error=False,
                )

            except Exception as exc:
                logger.error(
                    "Error executing MCP tool '%s' for agent '%s': %s",
                    params.name,
                    agent_id,
                    exc,
                    exc_info=True,
                )
                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error executing agent tool: {exc}",
                        )
                    ],
                    is_error=True,
                )

        return Server(
            server_name,
            version="0.4.0",
            on_list_tools=handle_list_tools,
            on_call_tool=handle_call_tool,
        )

    def create_session(self, agent_id: str, flask_app: Flask) -> McpSession:
        """
        Validates the agent, initializes a dedicated conversation for the session,
        and starts the background MCP server loop.
        """
        self.agent_service.get_agent(agent_id)

        session_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        server = self.create_server(
            agent_id=agent_id,
            conversation_id=conversation_id,
            flask_app=flask_app,
        )

        session = McpSession(
            session_id=session_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            server=server,
            flask_app=flask_app,
        )

        with self._lock:
            self._sessions[session_id] = session

        session.start()
        logger.info(
            "Initialized MCP SSE session '%s' for agent '%s' (conversation '%s').",
            session_id,
            agent_id,
            conversation_id,
        )
        return session

    def get_session(self, session_id: str, agent_id: str) -> McpSession | None:
        """Retrieves an active MCP session matching both session_id and agent_id."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.agent_id == agent_id:
                return session
            return None

    def remove_session(self, session_id: str) -> None:
        """Closes and removes an MCP session from the active registry."""
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            logger.info("Closed MCP SSE session '%s'.", session_id)

    def stream_session_events(
        self,
        session: McpSession,
        messages_endpoint_url: str,
    ) -> Generator[str, None, None]:
        """
        Yields W3C-compliant SSE events for `mcp-remote` / MCP SSE clients.
        First emits the `endpoint` event, followed by JSON-RPC `message` events.
        """
        yield f"event: endpoint\ndata: {messages_endpoint_url}\n\n"

        try:
            while True:
                try:
                    event = session.outgoing_queue.get(timeout=15.0)
                    if event is None:
                        break
                    yield f"event: {event['event']}\ndata: {event['data']}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            self.remove_session(session.session_id)