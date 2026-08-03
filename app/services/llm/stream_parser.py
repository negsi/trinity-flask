"""
Stream Response Parser Module.

Extracts regular text and structured JSON payloads from streaming token chunks,
preventing markers from bleeding into output text.
"""

import json
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class StreamResponseParser:
    """Parses streaming text chunks and isolates embedded JSON blocks delineated by marker tags."""

    START_MARKER = "###START_JSON_RESPONSE###"
    END_MARKER = "###END_JSON_RESPONSE###"

    def __init__(self) -> None:
        self.buffer = ""
        self.is_inside_json = False

    def process_chunk(self, chunk: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Processes an incoming chunk and extracts display text and complete JSON payloads.

        Args:
            chunk (str): Newly received text token chunk.

        Returns:
            Tuple[str, Optional[Dict[str, Any]]]: Tuple containing text to display and parsed JSON data (if complete).
        """
        self.buffer += chunk
        display_text = ""
        completed_json = None

        while self.buffer:
            if not self.is_inside_json:
                # 1. Full Start Marker detected
                if self.START_MARKER in self.buffer:
                    pre_text, post_start = self.buffer.split(self.START_MARKER, 1)
                    display_text += pre_text
                    self.buffer = post_start
                    self.is_inside_json = True
                    continue

                # 2. Check for partial start marker match at buffer boundary
                match_len = self._get_partial_match_length(self.buffer, self.START_MARKER)
                if match_len > 0:
                    display_text += self.buffer[:-match_len]
                    self.buffer = self.buffer[-match_len:]
                    break  # Wait for subsequent chunk
                
                # 3. No markers present
                display_text += self.buffer
                self.buffer = ""
                break

            else:
                # 1. Full End Marker detected
                if self.END_MARKER in self.buffer:
                    json_str, post_end = self.buffer.split(self.END_MARKER, 1)
                    completed_json = self._parse_json(json_str)
                    
                    self.buffer = post_end
                    self.is_inside_json = False
                    continue

                # 2. Check for partial end marker match at buffer boundary
                match_len = self._get_partial_match_length(self.buffer, self.END_MARKER)
                if match_len > 0:
                    break  
                
                # 3. Inside JSON block, waiting for completion
                break

        return display_text, completed_json

    def finalize(self) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Flushes buffered text when stream closes."""
        remaining_text = self.buffer if not self.is_inside_json else ""
        self.buffer = ""
        self.is_inside_json = False
        return remaining_text, None

    @staticmethod
    def _get_partial_match_length(text: str, marker: str) -> int:
        """Determines if the tail end of text partially matches the prefix of marker."""
        max_possible = min(len(text), len(marker) - 1)
        for length in range(max_possible, 0, -1):
            if marker.startswith(text[-length:]):
                return length
        return 0

    @staticmethod
    def _parse_json(raw_json: str) -> Optional[Dict[str, Any]]:
        """Safely parses raw JSON payload strings."""
        try:
            return json.loads(raw_json.strip())
        except json.JSONDecodeError as e:
            logger.error(f"[StreamResponseParser] JSONDecodeError: {e}")
            return None
