import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from backend.database.connection import get_db
from backend.database.models import Conversation, Message
from backend.database.schemas import ChatRequest, ChatResponse, SourceReference
from backend.guardrails.input_guard import InputGuardrail
from backend.guardrails.output_guard import OutputGuardrail
from backend.services.llm_service import LLMService
from backend.services.rag_service import RAGService
from backend.services.audio_service import AudioService
from backend.services.image_service import ImageService
from backend.utils.helpers import serialize_sources, deserialize_sources

router = APIRouter(prefix="", tags=["Chat"])

llm_service = LLMService()
rag_service = RAGService(llm_service=llm_service)

def get_or_create_conversation(db: Session, conversation_id: Optional[str], initial_prompt: str) -> Conversation:
    """Helper to retrieve an existing conversation or create a new one."""
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            return conv

    # Create new conversation with title derived from first message
    title = (initial_prompt[:35] + "...") if len(initial_prompt) > 35 else initial_prompt
    new_conv = Conversation(
        id=str(uuid.uuid4()),
        title=title or "New Conversation"
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv

@router.post("/chat", response_model=ChatResponse)
def chat_text(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Process pure text-based conversation with guardrails, emotional reasoning, and RAG.
    """
    clean_message = InputGuardrail.sanitize_text(payload.message)
    if not clean_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv = get_or_create_conversation(db, payload.conversation_id, clean_message)

    # 1. Guardrail: Crisis Detection
    is_crisis, crisis_response = InputGuardrail.check_crisis(clean_message)
    if is_crisis and crisis_response:
        # Save crisis interaction
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=clean_message,
            input_modality="text"
        )
        asst_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=crisis_response,
            output_modality="text"
        )
        db.add_all([user_msg, asst_msg])
        db.commit()

        return ChatResponse(
            conversation_id=conv.id,
            user_message=clean_message,
            assistant_response=crisis_response,
            is_crisis=True
        )

    # 2. Guardrail: Prompt Injection Detection
    is_injection, injection_block = InputGuardrail.check_prompt_injection(clean_message)
    if is_injection and injection_block:
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=clean_message,
            input_modality="text"
        )
        asst_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=injection_block,
            output_modality="text"
        )
        db.add_all([user_msg, asst_msg])
        db.commit()

        return ChatResponse(
            conversation_id=conv.id,
            user_message=clean_message,
            assistant_response=injection_block,
            warning="Prompt injection pattern mitigated."
        )

    # 3. Context Retrieval via RAG (if enabled)
    rag_context = ""
    source_refs: List[SourceReference] = []
    if payload.use_rag:
        rag_context, sources_data = rag_service.retrieve_context(clean_message)
        for s in sources_data:
            source_refs.append(SourceReference(**s))

    # 4. Fetch Conversation History (last 6 turns for context continuity)
    recent_messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.desc()).limit(6).all()
    recent_messages.reverse()

    history_payload = [{"role": m.role, "content": m.content} for m in recent_messages]

    # 5. LLM Response Generation
    raw_response = llm_service.generate_response(
        prompt=clean_message,
        conversation_history=history_payload,
        rag_context=rag_context
    )

    # 6. Output Guardrail (Leakage & Boundary Check)
    safe_response = OutputGuardrail.sanitize_output(raw_response)
    safe_response = OutputGuardrail.enforce_therapy_boundary(safe_response)

    # 7. Optional Text-to-Speech
    audio_url = None
    if payload.generate_speech:
        success, tts_path = AudioService.text_to_speech(safe_response)
        if success:
            audio_url = f"/storage/audio_cache/{Path(tts_path).name}"

    # 8. Store Messages in Database
    user_record = Message(
        conversation_id=conv.id,
        role="user",
        content=clean_message,
        input_modality="text"
    )
    asst_record = Message(
        conversation_id=conv.id,
        role="assistant",
        content=safe_response,
        output_modality="audio" if audio_url else "text",
        media_url=audio_url,
        sources_json=serialize_sources(source_refs)
    )
    db.add_all([user_record, asst_record])
    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        user_message=clean_message,
        assistant_response=safe_response,
        audio_url=audio_url,
        sources=source_refs
    )

@router.post("/chat/multimodal", response_model=ChatResponse)
async def chat_multimodal(
    message: Optional[str] = Form(""),
    conversation_id: Optional[str] = Form(None),
    use_rag: Optional[bool] = Form(True),
    generate_speech: Optional[bool] = Form(False),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Unified endpoint processing text, image, audio inputs, and RAG retrieval.
    """
    clean_message = InputGuardrail.sanitize_text(message or "")
    input_modality = "text"
    image_meta = None
    image_bytes = None
    image_mime = None

    # Handle image if provided
    if image and image.filename:
        input_modality = "image"
        img_bytes = await image.read()
        success, img_msg, meta = ImageService.validate_and_save_image(img_bytes, image.filename)
        if not success or not meta:
            raise HTTPException(status_code=400, detail=img_msg)
        image_meta = meta
        image_bytes = img_bytes
        ext = meta["format"]
        image_mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
        if not clean_message:
            clean_message = "What do you see in this image?"

    # Handle audio if provided
    if audio and audio.filename:
        input_modality = "audio"
        aud_bytes = await audio.read()
        success, transcription = AudioService.transcribe_audio(aud_bytes, audio.filename, llm_service)
        if not success:
            raise HTTPException(status_code=400, detail=transcription)
        clean_message = f"{transcription} {clean_message}".strip()

    if not clean_message:
        clean_message = "Hello! How can you help me today?"

    conv = get_or_create_conversation(db, conversation_id, clean_message)

    # Guardrails check
    is_crisis, crisis_response = InputGuardrail.check_crisis(clean_message)
    if is_crisis and crisis_response:
        return ChatResponse(
            conversation_id=conv.id,
            user_message=clean_message,
            assistant_response=crisis_response,
            is_crisis=True
        )

    is_injection, injection_block = InputGuardrail.check_prompt_injection(clean_message)
    if is_injection and injection_block:
        return ChatResponse(
            conversation_id=conv.id,
            user_message=clean_message,
            assistant_response=injection_block,
            warning="Prompt injection pattern mitigated."
        )

    # RAG Context Retrieval
    rag_context = ""
    source_refs: List[SourceReference] = []
    if use_rag:
        rag_context, sources_data = rag_service.retrieve_context(clean_message)
        for s in sources_data:
            source_refs.append(SourceReference(**s))

    # LLM Execution
    raw_response = llm_service.generate_response(
        prompt=clean_message,
        rag_context=rag_context,
        image_bytes=image_bytes,
        image_mime=image_mime
    )

    # Guardrail check on output
    safe_response = OutputGuardrail.sanitize_output(raw_response)
    safe_response = OutputGuardrail.enforce_therapy_boundary(safe_response)

    # Text-to-speech if requested
    audio_url = None
    if generate_speech:
        success, tts_path = AudioService.text_to_speech(safe_response)
        if success:
            audio_url = f"/storage/audio_cache/{Path(tts_path).name}"

    # Persist in Database
    user_record = Message(
        conversation_id=conv.id,
        role="user",
        content=clean_message,
        input_modality=input_modality,
        media_url=image_meta.get("file_path") if image_meta else None
    )
    asst_record = Message(
        conversation_id=conv.id,
        role="assistant",
        content=safe_response,
        output_modality="audio" if audio_url else "text",
        media_url=audio_url,
        sources_json=serialize_sources(source_refs)
    )
    db.add_all([user_record, asst_record])
    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        user_message=clean_message,
        assistant_response=safe_response,
        audio_url=audio_url,
        sources=source_refs
    )
