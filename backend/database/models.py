import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    documents = relationship("ConversationDocument", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    input_modality = Column(String(32), default="text")  # 'text', 'image', 'audio', 'document'
    output_modality = Column(String(32), default="text")  # 'text', 'audio'
    media_url = Column(Text, nullable=True)  # path or url to uploaded/generated media
    sources_json = Column(Text, nullable=True)  # serialized JSON of RAG sources
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # 'pdf', 'docx', 'txt'
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    chunk_count = Column(Integer, default=0)
    processing_status = Column(String(32), default="completed")  # 'pending', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("ConversationDocument", back_populates="document", cascade="all, delete-orphan")


class ConversationDocument(Base):
    __tablename__ = "conversation_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    conversation = relationship("Conversation", back_populates="documents")
    document = relationship("Document", back_populates="conversations")
