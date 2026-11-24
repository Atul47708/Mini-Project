import pytest
from pathlib import Path
from backend.services.rag_service import RAGService, LocalVectorStore

def test_text_chunking():
    rag = RAGService()
    sample_text = (
        "Cognitive Behavioral Therapy is a psycho-social intervention. "
        "It aims to reduce symptoms of various mental health conditions, primarily depression and anxiety disorders. "
        "CBT focuses on challenging and changing cognitive distortions and behaviors, improving emotional regulation, "
        "and the development of personal coping strategies that target solving current problems."
    )
    chunks = rag.chunk_text(sample_text, chunk_size=120, chunk_overlap=30)
    assert len(chunks) >= 2
    assert all(len(c) > 0 for c in chunks)

def test_local_vector_indexing_and_search(tmp_path):
    store = LocalVectorStore(tmp_path)
    rag = RAGService()

    chunks = [
        {
            "id": "doc1_0",
            "document_id": "doc1",
            "filename": "mindfulness.txt",
            "chunk_index": 0,
            "content": "Deep breathing and progressive muscle relaxation help calm the nervous system during stress.",
            "embedding": rag.compute_embedding("Deep breathing and progressive muscle relaxation help calm the nervous system during stress.")
        },
        {
            "id": "doc1_1",
            "document_id": "doc1",
            "filename": "astronomy.txt",
            "chunk_index": 0,
            "content": "The James Webb Space Telescope observes the universe in infrared light to study distant galaxies.",
            "embedding": rag.compute_embedding("The James Webb Space Telescope observes the universe in infrared light to study distant galaxies.")
        }
    ]

    store.add_chunks(chunks)
    assert len(store.chunks) == 2

    # Query about breathing/stress
    q_vec = rag.compute_embedding("How does deep breathing help with stress?")
    import numpy as np
    matches = store.search(np.array(q_vec), top_k=1)

    assert len(matches) == 1
    top_chunk, score = matches[0]
    assert top_chunk["filename"] == "mindfulness.txt"
    assert "nervous system" in top_chunk["content"]
