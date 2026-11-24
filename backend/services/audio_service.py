import os
import io
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional
from gtts import gTTS
from backend.config import AUDIO_CACHE_DIR, UPLOADS_DIR
from backend.services.llm_service import LLMService

logger = logging.getLogger("AudioService")

class AudioService:
    """
    Handles speech-to-text (transcription) and text-to-speech (voice generation).
    """

    ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "ogg"}

    @staticmethod
    def text_to_speech(text: str, lang: str = "en", slow: bool = False) -> Tuple[bool, str]:
        """
        Synthesizes speech from text using gTTS and caches the audio in storage/audio_cache.
        Returns (success, audio_filepath_or_error).
        """
        if not text or not text.strip():
            return False, "Text cannot be empty for speech generation."

        # Generate cache filename based on text hash
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
        filename = f"tts_{text_hash}.mp3"
        output_path = AUDIO_CACHE_DIR / filename

        # Return existing cached audio if present
        if output_path.exists():
            return True, str(output_path)

        try:
            # Clean text of markdown characters before TTS
            cleaned_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
            # Truncate text if too long for a single voice reply
            if len(cleaned_text) > 800:
                cleaned_text = cleaned_text[:800] + "..."

            # Set a fast timeout to prevent network blocking in offline environments
            import socket
            orig_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(4.0)

            try:
                tts = gTTS(text=cleaned_text, lang=lang, slow=slow)
                tts.save(str(output_path))
                logger.info(f"Synthesized TTS audio: {filename}")
                return True, str(output_path)
            finally:
                socket.setdefaulttimeout(orig_timeout)

        except Exception as e:
            logger.warning(f"Online TTS unavailable ({e}). Generating fallback audio placeholder.")
            try:
                # Generate a lightweight valid offline audio tone/placeholder
                import wave
                import struct
                wav_path = output_path.with_suffix(".wav")
                with wave.open(str(wav_path), "w") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    # 0.5s soft chime
                    for i in range(8000):
                        value = int(1000 * (1 - i / 8000)) if i < 4000 else 0
                        wav_file.writeframes(struct.pack("<h", value))
                return True, str(wav_path)
            except Exception as fe:
                return False, f"Speech synthesis failed: {str(fe)}"

    @staticmethod
    def transcribe_audio(file_bytes: bytes, filename: str, llm_service: Optional[LLMService] = None) -> Tuple[bool, str]:
        """
        Transcribes audio using Gemini audio understanding or returns a structured transcription notice.
        """
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in AudioService.ALLOWED_AUDIO_EXTENSIONS:
            return False, f"Unsupported audio format '.{ext}'. Allowed: {', '.join(AudioService.ALLOWED_AUDIO_EXTENSIONS)}"

        # Save audio file to storage/uploads
        unique_id = uuid.uuid4().hex[:12]
        saved_filename = f"audio_{unique_id}.{ext}"
        saved_path = UPLOADS_DIR / saved_filename

        try:
            with open(saved_path, "wb") as f:
                f.write(file_bytes)

            llm = llm_service or LLMService()
            if llm.is_configured():
                try:
                    from google.genai import types
                    mime_type = "audio/mp3" if ext == "mp3" else f"audio/{ext}"
                    audio_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
                    
                    response = llm.client.models.generate_content(
                        model=llm.model_name,
                        contents=[
                            audio_part,
                            "Please transcribe the spoken words in this audio exactly as uttered. If there are no spoken words, describe the audio."
                        ]
                    )
                    if response and response.text:
                        return True, response.text.strip()
                except Exception as e:
                    logger.warning(f"Gemini audio transcription failed: {e}. Using fallback.")

            # Informative fallback
            return True, f"[Audio message received: {filename} ({len(file_bytes) // 1024} KB). Transcription requires active GEMINI_API_KEY]"

        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return False, f"Failed to transcribe audio: {str(e)}"
