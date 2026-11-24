from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from pathlib import Path
from backend.services.image_service import ImageService
from backend.services.audio_service import AudioService
from backend.database.schemas import TTSRequest, TTSResponse, AudioTranscriptionResponse

router = APIRouter(prefix="", tags=["Media"])

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None)
):
    """
    Upload an image (JPG, PNG, WEBP) and optionally analyze it or ask a question.
    """
    file_bytes = await file.read()
    filename = file.filename or "image.jpg"

    success, msg, meta = ImageService.validate_and_save_image(file_bytes, filename)
    if not success or not meta:
        raise HTTPException(status_code=400, detail=msg)

    analysis = None
    if question or meta:
        analysis = ImageService.analyze_image(meta["file_path"], question=question)

    return {
        "status": "success",
        "message": msg,
        "metadata": meta,
        "analysis": analysis
    }

@router.post("/upload/audio", response_model=AudioTranscriptionResponse)
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file (MP3, WAV, M4A, OGG) and receive transcription.
    """
    file_bytes = await file.read()
    filename = file.filename or "audio.mp3"

    success, transcription = AudioService.transcribe_audio(file_bytes, filename)
    if not success:
        raise HTTPException(status_code=400, detail=transcription)

    return AudioTranscriptionResponse(
        transcription=transcription,
        duration_seconds=None,
        confidence=1.0
    )

@router.post("/generate/audio", response_model=TTSResponse)
def generate_speech(payload: TTSRequest):
    """
    Convert text response into spoken audio (TTS).
    """
    success, result_path = AudioService.text_to_speech(payload.text)
    if not success:
        raise HTTPException(status_code=500, detail=result_path)

    audio_filename = Path(result_path).name
    # Web-accessible URL for the audio
    audio_url = f"/storage/audio_cache/{audio_filename}"

    return TTSResponse(
        audio_url=audio_url,
        text=payload.text
    )
