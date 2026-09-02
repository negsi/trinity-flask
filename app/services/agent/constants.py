"""
Agent Domain & Protocol Constants.

Defines protocol markers and event prefixes used across agent streaming lifecycles.
"""

from typing import Final
import re

# Stream Protocol Markers
PROTOCOL_TASK_CHAIN: Final[str] = "__TASK_CHAIN__:"
PROTOCOL_ATTACHMENTS: Final[str] = "__ATTACHMENTS__:"

# JSON Response Block Markers
JSON_START_MARKER: Final[str] = "###START_JSON_RESPONSE###"
JSON_END_MARKER: Final[str] = "###END_JSON_RESPONSE###"

# Content Payload Block Markers (Issue #20)
PAYLOAD_START_MARKER: Final[str] = "###START_CONTENT_PAYLOADS###"
PAYLOAD_END_MARKER: Final[str] = "###END_CONTENT_PAYLOADS###"

# Payload Reference Format & Extractor Pattern
PAYLOAD_REF_PREFIX: Final[str] = "REF:"
PAYLOAD_TAG_REGEX: Final[re.Pattern] = re.compile(
    r"<<<([A-Za-z0-9_]+)>>>\n?(.*?)\n?<<<END_\1>>>", 
    re.DOTALL
)
