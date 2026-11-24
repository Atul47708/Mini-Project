import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from backend.database.connection import get_db
from backend.database.models import Document, ConversationDocument, Conversation
from backend.database.schemas import DocumentResponse
from backend.services.rag_service import RAGService
from backend.utils.file_handler import FileHandler

router = APIRouter(prefix="", tags=["Documents"])
rag_service = RAGService()

@router.post("/upload/document", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and index a document (PDF, DOCX, TXT) for RAG retrieval.
    """
    file_bytes = await file.read()
    filename = file.filename or "uploaded_doc"

    # Verify conversation if supplied
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Specified conversation not found.")

    # Save securely
    success, msg, saved_path = FileHandler.save_upload_file(
        file_bytes=file_bytes,
        filename=filename,
        allowed_extensions=RAGService.SUPPORTED_EXTENSIONS
    )
    if not success or not saved_path:
        raise HTTPException(status_code=400, detail=msg)

    doc_id = str(uuid.uuid4())
    ext = saved_path.suffix.lower().lstrip(".")

    # Process and index via RAG
    processed, chunk_count, process_msg = rag_service.process_document(
        document_id=doc_id,
        filename=filename,
        file_path=saved_path
    )
    if not processed:
        FileHandler.cleanup_file(saved_path)
        raise HTTPException(status_code=422, detail=f"Document processing failed: {process_msg}")

    # Create document record in database
    new_doc = Document(
        id=doc_id,
        filename=filename,
        file_type=ext,
        file_path=str(saved_path),
        file_size=len(file_bytes),
        chunk_count=chunk_count,
        processing_status="completed"
    )
    db.add(new_doc)

    if conversation_id:
        link = ConversationDocument(
            conversation_id=conversation_id,
            document_id=doc_id
        )
        db.add(link)

    db.commit()
    db.refresh(new_doc)

    return DocumentResponse(
        id=new_doc.id,
        filename=new_doc.filename,
        file_type=new_doc.file_type,
        file_size=new_doc.file_size,
        chunk_count=new_doc.chunk_count,
        processing_status=new_doc.processing_status,
        created_at=new_doc.created_at
    )

@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all indexed documents available for RAG."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            chunk_count=d.chunk_count,
            processing_status=d.processing_status,
            created_at=d.created_at
        )
        for d in docs
    ]
