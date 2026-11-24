from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from backend.database.connection import get_db
from backend.database.models import Conversation, Message
from backend.database.schemas import (
    ConversationResponse,
    ConversationDetail,
    ConversationCreate,
    MessageResponse
)
from backend.utils.helpers import deserialize_sources

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    """Retrieve all conversations ordered by recent update."""
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    result = []
    for c in convs:
        msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
        result.append(
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=msg_count
            )
        )
    return result

@router.post("", response_model=ConversationResponse)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation session."""
    conv_id = str(uuid.uuid4())
    new_conv = Conversation(
        id=conv_id,
        title=payload.title or "New Conversation"
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return ConversationResponse(
        id=new_conv.id,
        title=new_conv.title,
        created_at=new_conv.created_at,
        updated_at=new_conv.updated_at,
        message_count=0
    )

@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve details and all messages for a specific conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    formatted_messages = []
    for m in messages:
        formatted_messages.append(
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                input_modality=m.input_modality,
                output_modality=m.output_modality,
                media_url=m.media_url,
                sources=deserialize_sources(m.sources_json),
                created_at=m.created_at
            )
        )

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(formatted_messages),
        messages=formatted_messages
    )

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return {"status": "success", "message": f"Conversation {conversation_id} deleted."}
