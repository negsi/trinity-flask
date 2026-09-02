"""
Stream Response Parser Module.

Extracts regular text, structured JSON schemas, and decoupled content payloads
from streaming token chunks, preventing boundary markers and payload blocks
from leaking into user-visible streams.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class StreamResponseParser:
    """
    Parses streaming LLM chunks and isolates embedded JSON blocks as well as
    external content payload blocks delineated by marker tags.
    """

    JSON_START_MARKER = "###START_JSON_RESPONSE###"
    JSON_END_MARKER = "###END_JSON_RESPONSE###"

    PAYLOAD_START_MARKER = "###START_CONTENT_PAYLOADS###"
    PAYLOAD_END_MARKER = "###END_CONTENT_PAYLOADS###"

    PAYLOAD_TAG_REGEX = re.compile(
        r"<<<([A-Za-z0-9_]+)>>>\n?(.*?)\n?<<<END_\1>>>",
        re.DOTALL
    )

    def __init__(self) -> None:
        self.buffer: str = ""
        self.is_inside_json: bool = False
        self.is_inside_payload: bool = False
        self.pending_json_response: dict[str, Any] | None = None
        self.accumulated_payload_text: str = ""

    def process_chunk(self, chunk: str) -> tuple[str, dict[str, Any] | None]:
        """
        Processes an incoming text chunk and extracts display text, JSON schemas,
        and linked decoupled payloads.

        Args:
            chunk: Newly received text token chunk.

        Returns:
            tuple[str, dict[str, Any] | None]: Displayable text and parsed Task Chain payload (if ready).
        """
        self.buffer += chunk
        display_text = ""
        completed_response: dict[str, Any] | None = None

        while self.buffer:
            # 1. State: Gathering Payload Block
            if self.is_inside_payload:
                if self.PAYLOAD_END_MARKER in self.buffer:
                    payload_content, post_end = self.buffer.split(self.PAYLOAD_END_MARKER, 1)
                    self.accumulated_payload_text += payload_content
                    self.buffer = post_end
                    self.is_inside_payload = False

                    # Merge payloads into the previously parsed JSON task chain
                    payloads = self._extract_payloads(self.accumulated_payload_text)
                    if self.pending_json_response is not None:
                        completed_response = self._attach_payloads_to_response(
                            self.pending_json_response, payloads
                        )
                        self.pending_json_response = None
                    self.accumulated_payload_text = ""
                    continue

                # Buffer check for partial payload end marker
                match_len = self._get_partial_match_length(self.buffer, self.PAYLOAD_END_MARKER)
                if match_len > 0:
                    self.accumulated_payload_text += self.buffer[:-match_len]
                    self.buffer = self.buffer[-match_len:]
                else:
                    self.accumulated_payload_text += self.buffer
                    self.buffer = ""
                break

            # 2. State: Gathering JSON Response Block
            elif self.is_inside_json:
                if self.JSON_END_MARKER in self.buffer:
                    json_str, post_end = self.buffer.split(self.JSON_END_MARKER, 1)
                    parsed_json = self._parse_json(json_str)
                    self.buffer = post_end
                    self.is_inside_json = False
                    
                    if self.PAYLOAD_START_MARKER in self.buffer or self._is_potential_marker_start(self.buffer):
                        self.pending_json_response = parsed_json
                    else:
                        completed_response = parsed_json
                    continue

                # Buffer check for partial JSON end marker
                match_len = self._get_partial_match_length(self.buffer, self.JSON_END_MARKER)
                if match_len > 0:
                    break
                break

            # 3. State: Regular Text & Marker Interception
            else:
                # Check for Payload Start Marker
                if self.PAYLOAD_START_MARKER in self.buffer:
                    pre_text, post_start = self.buffer.split(self.PAYLOAD_START_MARKER, 1)
                    display_text += pre_text
                    self.buffer = post_start
                    self.is_inside_payload = True
                    self.accumulated_payload_text = ""
                    continue

                # Check for JSON Start Marker
                if self.JSON_START_MARKER in self.buffer:
                    pre_text, post_start = self.buffer.split(self.JSON_START_MARKER, 1)
                    display_text += pre_text
                    self.buffer = post_start
                    self.is_inside_json = True
                    continue

                # Check partial matches for start markers to prevent leaking partial tokens
                match_len_json = self._get_partial_match_length(self.buffer, self.JSON_START_MARKER)
                match_len_payload = self._get_partial_match_length(self.buffer, self.PAYLOAD_START_MARKER)
                max_match = max(match_len_json, match_len_payload)

                if max_match > 0:
                    display_text += self.buffer[:-max_match]
                    self.buffer = self.buffer[-max_match:]
                    break

                # If no markers matched, emit text normally
                # If we have a pending JSON response without an incoming payload block, emit it now
                if self.pending_json_response is not None and not self._is_potential_marker_start(self.buffer):
                    completed_response = self.pending_json_response
                    self.pending_json_response = None

                display_text += self.buffer
                self.buffer = ""
                break

        return display_text, completed_response

    def finalize(self) -> tuple[str, dict[str, Any] | None]:
        """
        Flushes remaining buffered text and emits pending responses when stream closes.
        """
        remaining_text = ""
        completed_response = self.pending_json_response

        if self.is_inside_payload and self.accumulated_payload_text:
            payloads = self._extract_payloads(self.accumulated_payload_text + self.buffer)
            if completed_response is not None:
                completed_response = self._attach_payloads_to_response(completed_response, payloads)
        elif not self.is_inside_json and not self.is_inside_payload:
            remaining_text = self.buffer

        self.buffer = ""
        self.is_inside_json = False
        self.is_inside_payload = False
        self.pending_json_response = None
        self.accumulated_payload_text = ""

        return remaining_text, completed_response

    @classmethod
    def _extract_payloads(cls, payload_block: str) -> dict[str, str]:
        """Extracts individual payloads defined by <<<ID>>>...<<<END_ID>>> tags."""
        payloads: dict[str, str] = {}
        for match in cls.PAYLOAD_TAG_REGEX.finditer(payload_block):
            payload_id = match.group(1).strip()
            content = match.group(2)
            # Remove single leading/trailing newline if present
            if content.startswith("\r\n"):
                content = content[2:]
            elif content.startswith("\n"):
                content = content[1:]
            if content.endswith("\r\n"):
                content = content[:-2]
            elif content.endswith("\n"):
                content = content[:-1]

            payloads[payload_id] = content
        return payloads

    @staticmethod
    def _attach_payloads_to_response(
        response: dict[str, Any],
        payloads: dict[str, str]
    ) -> dict[str, Any]:
        """Attaches extracted payloads dictionary to the parsed response structure."""
        if "response" in response and isinstance(response["response"], dict):
            response["response"]["payloads"] = payloads
        else:
            response["payloads"] = payloads
        return response

    @classmethod
    def _is_potential_marker_start(cls, text: str) -> bool:
        """Checks if the string starts with characters matching any start marker."""
        stripped = text.lstrip()
        return (
            cls.JSON_START_MARKER.startswith(stripped) or
            cls.PAYLOAD_START_MARKER.startswith(stripped) or
            stripped.startswith("#")
        )

    @staticmethod
    def _get_partial_match_length(text: str, marker: str) -> int:
        """Determines if the tail end of text partially matches the prefix of marker."""
        max_possible = min(len(text), len(marker) - 1)
        for length in range(max_possible, 0, -1):
            if marker.startswith(text[-length:]):
                return length
        return 0

    @staticmethod
    def _parse_json(raw_json: str) -> dict[str, Any] | None:
        """Safely parses raw JSON payload strings."""
        try:
            return json.loads(raw_json.strip())
        except json.JSONDecodeError as exc:
            logger.error("[StreamResponseParser] JSONDecodeError: %s", exc)
            return None