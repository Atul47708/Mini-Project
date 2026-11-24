from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field

# RAG Source Reference
class SourceReference(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    content: str
    relevance_score: float = Field(default=0.0, description="Similarity score between 0 and 1")

# Message Schemas
class MessageBase(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', 'system'")
    content: str
    input_modality: Optional[str] = "text"
    output_modality: Optional[str] = "text"
    media_url: Optional[str] = None
    sources: Optional[List[SourceReference]] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    input_modality: str
    output_modality: str
    media_url: Optional[str] = None
    sources: Optional[List[SourceReference]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Conversation Schemas
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse] = []

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Request & Response
class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    use_rag: Optional[bool] = True
    generate_speech: Optional[bool] = False

class ChatResponse(BaseModel):
    conversation_id: str
    user_message: str
    assistant_response: str
    audio_url: Optional[str] = None
    sources: List[SourceReference] = []
    is_crisis: bool = False
    warning: Optional[str] = None

# Audio & TTS Schemas
class TTSRequest(BaseModel):
    text: str
    voice_speed: Optional[float] = 1.0

class TTSResponse(BaseModel):
    audio_url: str
    text: str

class AudioTranscriptionResponse(BaseModel):
    transcription: str
    duration_seconds: Optional[float] = None
    confidence: Optional[float] = 1.0

# Health check schema
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    gemini_api_configured: bool
