import re
import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from backend.guardrails.safety_rules import (
    CRISIS_KEYWORDS,
    PROMPT_INJECTION_PATTERNS,
    EMERGENCY_RESOURCES,
    AI_COMPANION_DISCLAIMER
)

class InputGuardrail:
    """
    Validates, sanitizes, and evaluates incoming user prompts and files.
    """

    @staticmethod
    def check_crisis(text: str) -> Tuple[bool, Optional[str]]:
        """
        Detects if user expresses crisis, self-harm, or suicidal ideation.
        Returns (is_crisis, emergency_response_or_none).
        """
        lower_text = text.lower()
        for pattern in CRISIS_KEYWORDS:
            if re.search(pattern, lower_text):
                compassionate_crisis_response = (
                    "I hear that you are going through a painful and difficult time, and I care deeply about your safety. "
                    "Because I am an AI, I cannot provide the real-time care or emergency assistance you deserve right now. "
                    "Please consider connecting with someone who can help immediately:"
                    f"{EMERGENCY_RESOURCES}"
                )
                return True, compassionate_crisis_response
        return False, None

    @staticmethod
    def check_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
        """
        Detects adversarial attempts to hijack the system prompt or extract internal keys.
        """
        lower_text = text.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lower_text):
                injection_block_response = (
                    "I want to assist you safely and respectfully, but I cannot modify my core safety guidelines "
                    "or disclose internal system configurations. How else can I help support you today?"
                )
                return True, injection_block_response
        return False, None

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitizes text by stripping null bytes and limiting extreme lengths.
        """
        if not text:
            return ""
        # Remove null characters
        cleaned = text.replace("\x00", "")
        # Normalize whitespace
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
        # Cap excessive length (e.g. max 15,000 characters per message)
        return cleaned[:15000]

    @staticmethod
    def validate_file_upload(
        filename: str,
        file_size_bytes: int,
        allowed_extensions: set,
        max_size_bytes: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates file metadata, path safety, and extension.
        """
        if not filename:
            return False, "Filename cannot be empty."

        # Prevent directory traversal
        sanitized_filename = os.path.basename(filename)
        if sanitized_filename != filename or ".." in filename:
            return False, "Invalid filename or path traversal detected."

        # Extension check
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in allowed_extensions:
            return False, f"Unsupported file type '.{ext}'. Allowed types: {', '.join(sorted(allowed_extensions))}"

        # Size check
        if file_size_bytes > max_size_bytes:
            max_mb = max_size_bytes / (1024 * 1024)
            return False, f"File size exceeds the limit of {max_mb:.1f} MB."

        return True, None
