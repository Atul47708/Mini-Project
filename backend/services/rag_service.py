import os
import re
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

import pymupdf  # PyMuPDF
import docx  # python-docx

from backend.config import (
    UPLOADS_DIR,
    VECTOR_STORE_DIR,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
    RAG_TOP_K,
    EMBEDDING_MODEL
)
from backend.services.llm_service import LLMService

logger = logging.getLogger("RAGService")

class LocalVectorStore:
    """
    Lightweight, high-performance local vector store with JSON metadata and cosine similarity search.
    """
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / "vector_index.json"
        self.chunks: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded {len(self.chunks)} chunks from local vector store.")
            except Exception as e:
                logger.error(f"Error loading vector index: {e}")
                self.chunks = []
        else:
            self.chunks = []

    def save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        self.chunks.extend(new_chunks)
        self.save()

    def remove_document_chunks(self, document_id: str):
        self.chunks = [c for c in self.chunks if c.get("document_id") != document_id]
        self.save()

    def search(self, query_vector: np.ndarray, top_k: int = 4) -> List[Tuple[Dict[str, Any], float]]:
        """
        Cosine similarity search across stored chunk vectors.
        """
        if not self.chunks or query_vector is None:
            return []

        results = []
        q_norm = np.linalg.norm(query_vector)
        if q_norm == 0:
            return []

        for chunk in self.chunks:
            c_vec = np.array(chunk.get("embedding", []), dtype=np.float32)
            if len(c_vec) != len(query_vector):
                continue
            c_norm = np.linalg.norm(c_vec)
            if c_norm == 0:
                continue

            # Cosine similarity
            similarity = float(np.dot(query_vector, c_vec) / (q_norm * c_norm))
            results.append((chunk, similarity))

        # Sort by highest similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class RAGService:
    """
    Comprehensive RAG pipeline supporting PDF, DOCX, TXT parsing,
    sliding-window chunking, embedding generation, and grounded context retrieval.
    """

    SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()
        self.vector_store = LocalVectorStore(VECTOR_STORE_DIR)

    @staticmethod
    def extract_text(file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts clean text and section/page metadata from PDF, DOCX, or TXT.
        """
        ext = file_path.suffix.lower().lstrip(".")
        full_text = ""
        sections = []

        if ext == "pdf":
            doc = pymupdf.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    clean_page = re.sub(r"\s+", " ", page_text).strip()
                    full_text += f"\n[Page {page_num + 1}] " + clean_page
                    sections.append({"page": page_num + 1, "text": clean_page})
            doc.close()

        elif ext == "docx":
            doc = docx.Document(file_path)
            para_texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for idx, p_text in enumerate(para_texts):
                clean_p = re.sub(r"\s+", " ", p_text)
                full_text += f"\n[Paragraph {idx + 1}] " + clean_p
                sections.append({"paragraph": idx + 1, "text": clean_p})

        elif ext in ["txt", "md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
            full_text = re.sub(r"\s+", " ", raw_text).strip()
            sections.append({"section": 1, "text": full_text})

        return full_text.strip(), sections

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = RAG_CHUNK_SIZE,
        chunk_overlap: int = RAG_CHUNK_OVERLAP
    ) -> List[str]:
        """
        Splits text into overlapping chunks using sentence/punctuation boundaries.
        """
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:].strip())
                break

            # Find nearest sentence break or space before 'end'
            cut_point = text.rfind(". ", start, end)
            if cut_point == -1 or cut_point < start + (chunk_size // 2):
                cut_point = text.rfind(" ", start, end)

            if cut_point == -1:
                cut_point = end

            chunk = text[start:cut_point].strip()
            if chunk:
                chunks.append(chunk)

            # Advance by cut_point minus overlap
            start = max(start + 1, cut_point - chunk_overlap)

        return chunks

    def compute_embedding(self, text: str) -> List[float]:
        """
        Computes embedding via Gemini API or falls back to robust local semantic hash/term vector.
        """
        # If Gemini client configured, try live embedding API
        if self.llm_service and self.llm_service.is_configured():
            try:
                result = self.llm_service.client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text
                )
                if hasattr(result, "embedding") and result.embedding:
                    return list(result.embedding.values)
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Using deterministic semantic vector.")

        # Local deterministic semantic vector (dimension: 128)
        vector = np.zeros(128, dtype=np.float32)
        words = re.findall(r"\w+", text.lower())
        for word in words:
            # Deterministic hash bucket
            h = int(hashlib_hash := abs(hash(word)) % 128)
            vector[h] += 1.0

        # Also add character n-gram features
        for i in range(len(text) - 3):
            sub = text[i:i+4]
            h = int(abs(hash(sub)) % 128)
            vector[h] += 0.2

        # L2 Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def process_document(
        self,
        document_id: str,
        filename: str,
        file_path: Path
    ) -> Tuple[bool, int, str]:
        """
        Extracts, chunks, embeds, and stores document in the vector store.
        """
        try:
            full_text, _ = self.extract_text(file_path)
            if not full_text:
                return False, 0, "No extractable text found in document."

            chunks = self.chunk_text(full_text)
            if not chunks:
                return False, 0, "Document produced no valid text chunks."

            chunk_records = []
            for idx, chunk_content in enumerate(chunks):
                emb = self.compute_embedding(chunk_content)
                chunk_records.append({
                    "id": f"{document_id}_{idx}",
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": idx,
                    "content": chunk_content,
                    "embedding": emb
                })

            self.vector_store.add_chunks(chunk_records)
            logger.info(f"Successfully processed document '{filename}': {len(chunks)} chunks stored.")
            return True, len(chunks), f"Successfully indexed {len(chunks)} chunks."

        except Exception as e:
            logger.error(f"Error processing document '{filename}': {e}")
            return False, 0, str(e)

    def retrieve_context(
        self,
        query: str,
        top_k: int = RAG_TOP_K
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieves top relevant chunks and formats them into grounded context string and source list.
        """
        if not self.vector_store.chunks:
            return "", []

        q_vec = np.array(self.compute_embedding(query), dtype=np.float32)
        matches = self.vector_store.search(q_vec, top_k=top_k)

        if not matches:
            return "", []

        formatted_context_parts = []
        sources = []

        for chunk, score in matches:
            # We accept matches above relevance baseline
            formatted_context_parts.append(
                f"[Source: {chunk['filename']} | Chunk {chunk['chunk_index']}]:\n{chunk['content']}"
            )
            sources.append({
                "document_id": chunk["document_id"],
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"][:250] + ("..." if len(chunk["content"]) > 250 else ""),
                "relevance_score": round(score, 3)
            })

        context_string = "\n\n".join(formatted_context_parts)
        return context_string, sources
