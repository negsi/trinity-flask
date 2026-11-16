"""
Agent-Specific MCP (Model Context Protocol) SSE & Message Endpoints.

Exposes per-agent SSE transport endpoints compatible with `mcp-remote`,
Claude Desktop, and Cursor.
"""

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from dependency_injector.wiring import Provide, inject

from app.containers import Container
from app.domain.errors import ValidationError
from app.mcp_agent_server import McpAgentServerFactory

bp = Blueprint("mcp", __name__, url_prefix="/api/v1/agents/<agent_id>/mcp")


@bp.route("/sse", methods=["GET"])
@inject
def mcp_sse_connect(
    agent_id: str,
    mcp_factory: McpAgentServerFactory = Provide[Container.mcp_agent_server_factory],
):
    """
    Establishes an agent-specific MCP Server-Sent Events (SSE) stream and binds
    a persistent conversation context for the duration of the connection.
    """
    flask_app = current_app._get_current_object()
    session = mcp_factory.create_session(agent_id=agent_id, flask_app=flask_app)

    messages_endpoint = (
        f"/api/v1/agents/{agent_id}/mcp/messages?session_id={session.session_id}"
    )

    return Response(
        stream_with_context(
            mcp_factory.stream_session_events(
                session=session,
                messages_endpoint_url=messages_endpoint,
            )
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@bp.route("/messages", methods=["POST"])
@inject
def mcp_post_message(
    agent_id: str,
    mcp_factory: McpAgentServerFactory = Provide[Container.mcp_agent_server_factory],
):
    """
    Receives incoming JSON-RPC 2.0 messages from the MCP client and forwards
    them to the active agent MCP session.
    """
    session_id = request.args.get("session_id", "").strip()
    if not session_id:
        raise ValidationError("Missing 'session_id' query parameter.")

    session = mcp_factory.get_session(session_id=session_id, agent_id=agent_id)
    if not session:
        return jsonify({"error": f"Active MCP session '{session_id}' not found."}), 404

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON-RPC payload.")

    session.post_message(payload)
    return jsonify({"status": "accepted"}), 202