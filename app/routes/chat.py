"""
Chat and File Serving HTTP Endpoints.

Handles conversation sandbox file serving.
"""

import os
from flask import Blueprint, send_from_directory, current_app

bp = Blueprint("chat", __name__, url_prefix="/api/v1/chat")


@bp.route("/conversations/<conversation_id>/files/<path:filename>", methods=["GET"])
def get_conversation_file(
    conversation_id: str,
    filename: str,
):
    """Serves files directly from the conversation sandbox folder."""
    conversations_dir = current_app.config.get(
        "CONVERSATIONS_FOLDER",
        os.path.join(current_app.root_path, "..", "instance", "conversations"),
    )

    target_folder = os.path.abspath(os.path.join(conversations_dir, conversation_id))

    return send_from_directory(
        directory=target_folder,
        path=filename,
        as_attachment=True,
    )
