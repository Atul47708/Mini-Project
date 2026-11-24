import re
from typing import Tuple
from backend.guardrails.safety_rules import SENSITIVE_LEAKAGE_PATTERNS, AI_COMPANION_DISCLAIMER

class OutputGuardrail:
    """
    Scans model-generated output for sensitive data leaks, enforces empathetic boundaries,
    and attaches required disclaimers.
    """

    @staticmethod
    def sanitize_output(response_text: str) -> str:
        """
        Redacts any accidental leakage of API keys, passwords, or database URLs.
        """
        if not response_text:
            return ""

        sanitized = response_text
        for pattern in SENSITIVE_LEAKAGE_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED_SENSITIVE_DATA]", sanitized)

        return sanitized

    @staticmethod
    def enforce_therapy_boundary(response_text: str) -> str:
        """
        If the response sounds like an explicit medical prescription or psychiatric diagnosis,
        ensure the AI companion boundary reminder is present.
        """
        medical_triggers = [
            r"\b(prescribe|medication|diagnos(is|ed|e))\b",
            r"\byou have (depression|bipolar|schizophrenia|anxiety disorder)\b"
        ]

        needs_disclaimer = any(re.search(p, response_text.lower()) for p in medical_triggers)
        if needs_disclaimer and "licensed therapist" not in response_text.lower():
            return f"{response_text}\n\n*Note: {AI_COMPANION_DISCLAIMER}*"

        return response_text
