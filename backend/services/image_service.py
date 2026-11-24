import io
import uuid
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image
from backend.config import UPLOADS_DIR, GEMINI_MODEL
from backend.services.llm_service import LLMService

logger = logging.getLogger("ImageService")

class ImageService:
    """
    Handles image validation, visual analysis, and visual question answering (VQA).
    """

    ALLOWED_FORMATS = {"jpeg", "jpg", "png", "webp"}

    @staticmethod
    def validate_and_save_image(file_bytes: bytes, original_filename: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validates file as a valid image and saves it to the storage/uploads directory.
        """
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image_format = (image.format or "").lower()
            if image_format == "jpeg":
                image_format = "jpg"

            if image_format not in ImageService.ALLOWED_FORMATS:
                return False, f"Image format '{image_format}' is not supported. Use JPG, PNG, or WEBP.", None

            # Generate unique filename
            unique_filename = f"img_{uuid.uuid4().hex[:12]}.{image_format}"
            save_path = UPLOADS_DIR / unique_filename

            # Save file
            image.save(save_path)

            meta = {
                "filename": unique_filename,
                "original_filename": original_filename,
                "file_path": str(save_path),
                "format": image_format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "size_bytes": len(file_bytes),
            }
            return True, f"Image saved successfully as {unique_filename}", meta

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return False, f"Invalid image file: {str(e)}", None

    @staticmethod
    def analyze_image(
        image_path: str,
        question: Optional[str] = None,
        llm_service: Optional[LLMService] = None
    ) -> str:
        """
        Performs visual reasoning using Gemini vision or descriptive fallback.
        """
        llm = llm_service or LLMService()
        path = Path(image_path)
        if not path.exists():
            return "Error: Image file not found."

        prompt_text = question or "Please describe this image in detail and share what you observe."

        try:
            with open(path, "rb") as f:
                img_bytes = f.read()

            ext = path.suffix.lower().lstrip(".")
            mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"

            # If Gemini is configured, pass the image bytes to LLMService
            if llm.is_configured():
                return llm.generate_response(
                    prompt=prompt_text,
                    image_bytes=img_bytes,
                    image_mime=mime_type
                )
        except Exception as e:
            logger.error(f"Gemini vision call failed: {e}")

        # Intelligent fallback description using PIL metadata
        try:
            with Image.open(path) as img:
                return (
                    f"I have inspected the uploaded image ({img.width}x{img.height} pixels, format: {img.format}, color mode: {img.mode}). "
                    f"To enable deep visual question answering, please ensure your GEMINI_API_KEY is configured in your .env file."
                )
        except Exception as e:
            return f"Unable to analyze image: {e}"
