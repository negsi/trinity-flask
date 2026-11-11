"""Workflow Application Service Module."""

from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import queue
import threading
from typing import Any
import uuid

from flask import current_app

from app.domain.enums import ActorType
from app.domain.errors import ValidationError
from app.domain.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from app.domain.repositories.workflow_repository import WorkflowRepository
from app.services.agent.agent_orchestrator import AgentOrchestrator
from app.services.agent.constants import (
    PROTOCOL_ATTACHMENTS,
    PROTOCOL_TASK_CHAIN,
    PROTOCOL_THOUGHT,
)
from app.services.messaging.messaging_service import MessagingService

logger = logging.getLogger(__name__)

MAX_PARALLEL_WORKFLOW_NODES = 4


class WorkflowService:
    """Service managing Workflow lifecycle, persistence, and parallel real-time execution."""

    def __init__(
        self,
        workflow_repo: WorkflowRepository,
        agent_orchestrator: AgentOrchestrator | None = None,
        messaging_service: MessagingService | None = None,
    ) -> None:
        self.workflow_repo = workflow_repo
        self.agent_orchestrator = agent_orchestrator
        self.messaging_service = messaging_service

    def save_workflow(
        self,
        name: str,
        nodes_data: list[dict[str, Any]],
        edges_data: list[dict[str, Any]],
        workflow_id: str | None = None,
        description: str | None = None,
    ) -> Workflow:
        """Creates or updates (upserts) a workflow along with its nodes and edges."""
        nodes = [
            WorkflowNode(
                id=n.get("id") or str(uuid.uuid4()),
                agent_id=n["agentId"],
                agent_name=n["agentName"],
                agent_description=n.get("agentDescription"),
                x=float(n.get("x", 0.0)),
                y=float(n.get("y", 0.0)),
                prompt=n.get("prompt", ""),
            )
            for n in nodes_data
        ]

        node_ids = {node.id for node in nodes}
        edges = [
            WorkflowEdge(
                id=e.get("id") or str(uuid.uuid4()),
                source_node_id=e["sourceNodeId"],
                target_node_id=e["targetNodeId"],
            )
            for e in edges_data
            if e.get("sourceNodeId") in node_ids and e.get("targetNodeId") in node_ids
        ]

        workflow = Workflow(
            id=workflow_id or str(uuid.uuid4()),
            name=name.strip() if name else "Unbenannter Workflow",
            description=description,
            nodes=nodes,
            edges=edges,
        )

        saved = self.workflow_repo.save(workflow)
        logger.info("Saved Workflow '%s' (ID: '%s')", saved.name, saved.id)
        return saved

    def get_workflow(self, workflow_id: str) -> Workflow:
        """Retrieves a single workflow by ID or raises ValidationError."""
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise ValidationError(f"Workflow with ID '{workflow_id}' was not found.")
        return workflow

    def get_all_workflows(self) -> list[Workflow]:
        """Retrieves all workflows."""
        return self.workflow_repo.get_all()

    def delete_workflow(self, workflow_id: str) -> None:
        """Deletes an existing workflow."""
        self.get_workflow(workflow_id)
        self.workflow_repo.delete(workflow_id)
        logger.info("Deleted Workflow with ID '%s'", workflow_id)

    def stream_workflow_execution(
        self,
        workflow_id: str,
        user_id: str = "system",
    ) -> Generator[dict[str, Any], None, None]:
        """
        Executes a workflow layer by layer. Nodes within the same topological layer
        are executed concurrently in background threads while streaming SSE events
        in real-time to the caller.
        """
        if not self.agent_orchestrator or not self.messaging_service:
            raise ValidationError("Workflow execution dependencies are not configured.")

        workflow = self.get_workflow(workflow_id)
        if not workflow.nodes:
            raise ValidationError("Cannot execute an empty workflow without nodes.")

        layers = self._compute_execution_layers(workflow.nodes, workflow.edges)
        first_agent_id = layers[0][0].agent_id

        # Create a shared conversation workspace so all workflow nodes share files
        init_msg = self.messaging_service.send_message(
            conversation_id=None,
            sender_id=user_id,
            sender_type=ActorType.USER,
            sender_name="Workflow Runner",
            text=f"Workflow Start: {workflow.name}",
            recipient_id=first_agent_id,
        )
        conversation_id = init_msg.conversation_id

        yield {
            "type": "workflow_start",
            "workflow_id": workflow.id,
            "conversation_id": conversation_id,
        }

        node_outputs: dict[str, str] = {}
        node_outputs_lock = threading.Lock()
        nodes_by_id: dict[str, WorkflowNode] = {n.id: n for n in workflow.nodes}

        # Capture the real Flask app instance for worker threads
        app_obj = current_app._get_current_object()  # type: ignore[attr-defined]

        for layer_idx, layer_nodes in enumerate(layers):
            step_number = layer_idx + 1
            event_queue: queue.Queue[dict[str, Any] | None] = queue.Queue()

            def run_single_node(
                node: WorkflowNode,
                step_num: int,
                q: queue.Queue[dict[str, Any] | None],
            ) -> None:
                """Worker function executing a single workflow node inside a Flask app context."""
                with app_obj.app_context():
                    try:
                        q.put(
                            {
                                "type": "node_start",
                                "node_id": node.id,
                                "agent_id": node.agent_id,
                                "agent_name": node.agent_name,
                                "step": step_num,
                            }
                        )

                        effective_prompt = self._build_node_prompt(
                            node=node,
                            edges=workflow.edges,
                            nodes_by_id=nodes_by_id,
                            node_outputs=node_outputs,
                        )

                        stream_gen = self.agent_orchestrator.stream_agent_response(
                            user_text=effective_prompt,
                            conversation_id=conversation_id,
                            agent_id=node.agent_id,
                            agent_name=node.agent_name,
                            user_id=user_id,
                            call_depth=1,
                        )

                        collected_chunks: list[str] = []

                        for chunk in stream_gen:
                            if not chunk:
                                continue

                            parsed_events = self._parse_orchestrator_chunk(
                                node_id=node.id,
                                chunk=chunk,
                            )
                            for ev in parsed_events:
                                if ev["type"] == "node_chunk":
                                    collected_chunks.append(ev.get("content", ""))
                                q.put(ev)

                        final_output = "".join(collected_chunks).strip()
                        with node_outputs_lock:
                            node_outputs[node.id] = final_output

                        q.put(
                            {
                                "type": "node_complete",
                                "node_id": node.id,
                                "agent_id": node.agent_id,
                                "output": final_output,
                            }
                        )
                    except Exception as exc:
                        logger.error(
                            "Error executing workflow node '%s' (agent '%s'): %s",
                            node.id,
                            node.agent_id,
                            exc,
                            exc_info=True,
                        )
                        q.put(
                            {
                                "type": "node_error",
                                "node_id": node.id,
                                "agent_id": node.agent_id,
                                "error": str(exc),
                            }
                        )
                    finally:
                        q.put(None)

            max_workers = min(len(layer_nodes), MAX_PARALLEL_WORKFLOW_NODES)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for node in layer_nodes:
                    executor.submit(run_single_node, node, step_number, event_queue)

                finished_workers = 0
                total_workers = len(layer_nodes)
                while finished_workers < total_workers:
                    item = event_queue.get()
                    if item is None:
                        finished_workers += 1
                    else:
                        yield item

        yield {
            "type": "workflow_complete",
            "workflow_id": workflow.id,
            "conversation_id": conversation_id,
        }

    def _build_node_prompt(
        self,
        node: WorkflowNode,
        edges: list[WorkflowEdge],
        nodes_by_id: dict[str, WorkflowNode],
        node_outputs: dict[str, str],
    ) -> str:
        """Builds the contextual prompt for a node including predecessor outputs."""
        incoming_edges = [e for e in edges if e.target_node_id == node.id]
        predecessor_blocks: list[str] = []

        for edge in incoming_edges:
            pred_id = edge.source_node_id
            pred_node = nodes_by_id.get(pred_id)
            pred_output = node_outputs.get(pred_id, "").strip()
            if pred_node and pred_output:
                predecessor_blocks.append(
                    f"--- Ausgabe von '{pred_node.agent_name}' ---\n{pred_output}"
                )

        base_prompt = (
            node.prompt.strip()
            if node.prompt and node.prompt.strip()
            else "Führe deine Aufgabe gemäß deiner Rolle und den vorliegenden Informationen aus."
        )

        if not predecessor_blocks:
            return base_prompt

        context_section = "\n\n".join(predecessor_blocks)
        return (
            f"### ERGEBNISSE VORHERIGER WORKFLOW-AGENTEN:\n"
            f"{context_section}\n\n"
            f"### DEINE AUFGABE:\n"
            f"{base_prompt}"
        )

    def _parse_orchestrator_chunk(
        self,
        node_id: str,
        chunk: str,
    ) -> list[dict[str, Any]]:
        """Translates internal AgentOrchestrator protocol chunks into structured node SSE events."""
        events: list[dict[str, Any]] = []

        # 1. Explicit PROTOCOL_THOUGHT markers
        if PROTOCOL_THOUGHT in chunk:
            idx = chunk.find(PROTOCOL_THOUGHT)
            before = chunk[:idx]
            if before.strip():
                events.append(
                    {"type": "node_chunk", "node_id": node_id, "content": before}
                )
            thought_raw = chunk[idx + len(PROTOCOL_THOUGHT) :].strip()
            try:
                parsed = json.loads(thought_raw)
                delta = (
                    parsed.get("delta")
                    or parsed.get("content")
                    or parsed.get("thought")
                    or ""
                )
            except Exception:
                delta = thought_raw
            if delta:
                events.append(
                    {
                        "type": "node_thought",
                        "node_id": node_id,
                        "thought": delta,
                        "delta": delta,
                    }
                )
            return events

        # 2. Pre-formatted JSON thought strings
        stripped = chunk.strip()
        if stripped.startswith('{"type": "thought"') or stripped.startswith(
            '{"type":"thought"'
        ):
            try:
                parsed = json.loads(stripped)
                delta = (
                    parsed.get("delta")
                    or parsed.get("content")
                    or parsed.get("thought")
                    or ""
                )
                if delta:
                    events.append(
                        {
                            "type": "node_thought",
                            "node_id": node_id,
                            "thought": delta,
                            "delta": delta,
                        }
                    )
                return events
            except Exception:
                pass

        # 3. Task Chain protocol events
        if PROTOCOL_TASK_CHAIN in chunk:
            idx = chunk.find(PROTOCOL_TASK_CHAIN)
            before = chunk[:idx]
            if before.strip():
                events.append(
                    {"type": "node_chunk", "node_id": node_id, "content": before}
                )
            tc_raw = chunk[idx + len(PROTOCOL_TASK_CHAIN) :].strip()
            try:
                tc_payload = json.loads(tc_raw)
                events.append(
                    {
                        "type": "node_task_chain",
                        "node_id": node_id,
                        "payload": tc_payload,
                    }
                )
            except Exception:
                logger.warning(
                    "Failed to parse task chain JSON in workflow node '%s': %s",
                    node_id,
                    tc_raw,
                )
            return events

        # 4. Attachments protocol events
        if PROTOCOL_ATTACHMENTS in chunk:
            idx = chunk.find(PROTOCOL_ATTACHMENTS)
            before = chunk[:idx]
            if before.strip():
                events.append(
                    {"type": "node_chunk", "node_id": node_id, "content": before}
                )
            att_raw = chunk[idx + len(PROTOCOL_ATTACHMENTS) :].strip()
            try:
                att_payload = json.loads(att_raw)
                events.append(
                    {
                        "type": "node_attachments",
                        "node_id": node_id,
                        "files": att_payload.get("files", []),
                    }
                )
            except Exception:
                pass
            return events

        # 5. Standard text chunks
        events.append(
            {
                "type": "node_chunk",
                "node_id": node_id,
                "content": chunk,
                "delta": chunk,
            }
        )
        return events

    def _compute_execution_layers(
        self,
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
    ) -> list[list[WorkflowNode]]:
        """Groups workflow nodes topologically into parallel execution layers (Kahn's algorithm)."""
        in_degree: dict[str, int] = {n.id: 0 for n in nodes}
        adjacency: dict[str, list[str]] = {n.id: [] for n in nodes}
        nodes_by_id: dict[str, WorkflowNode] = {n.id: n for n in nodes}

        for edge in edges:
            if edge.source_node_id in adjacency and edge.target_node_id in in_degree:
                adjacency[edge.source_node_id].append(edge.target_node_id)
                in_degree[edge.target_node_id] += 1

        def sort_key(n: WorkflowNode) -> tuple[float, float]:
            return (n.x, n.y)

        current_wave = sorted(
            [n for n in nodes if in_degree[n.id] == 0],
            key=sort_key,
        )

        layers: list[list[WorkflowNode]] = []
        visited: set[str] = set()

        while current_wave:
            layers.append(current_wave)
            next_wave: list[WorkflowNode] = []

            for node in current_wave:
                visited.add(node.id)
                for target_id in adjacency.get(node.id, []):
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0 and target_id not in visited:
                        target_node = nodes_by_id.get(target_id)
                        if target_node:
                            next_wave.append(target_node)

            current_wave = sorted(next_wave, key=sort_key)

        if len(visited) < len(nodes):
            remaining = sorted(
                [n for n in nodes if n.id not in visited],
                key=sort_key,
            )
            layers.append(remaining)

        return layers