import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple, Optional
from backend.config import UPLOADS_DIR, MAX_UPLOAD_SIZE_BYTES
from backend.guardrails.input_guard import InputGuardrail

class FileHandler:
    """
    Manages secure file uploads, validation, and storage.
    """

    @staticmethod
    def save_upload_file(
        file_bytes: bytes,
        filename: str,
        allowed_extensions: set,
        max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Validates and safely persists an uploaded file.
        Returns (success, message, saved_path).
        """
        # Guardrail check
        is_valid, error_msg = InputGuardrail.validate_file_upload(
            filename=filename,
            file_size_bytes=len(file_bytes),
            allowed_extensions=allowed_extensions,
            max_size_bytes=max_size_bytes
        )
        if not is_valid:
            return False, error_msg or "Invalid file upload.", None

        # Clean ext
        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
        destination = UPLOADS_DIR / unique_name

        try:
            with open(destination, "wb") as f:
                f.write(file_bytes)
            return True, f"File saved as {unique_name}", destination
        except Exception as e:
            return False, f"Failed to save file: {str(e)}", None

    @staticmethod
    def cleanup_file(file_path: Path):
        """Safely removes a file if it exists."""
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except Exception:
            pass
