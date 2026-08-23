import hashlib
import math
from typing import List, Tuple
from uuid import UUID
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.change_embedding import ChangeEmbedding

EMBEDDING_DIM = 1536


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """
    Splits text into chunks using a sliding window strategy with overlap.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def _generate_deterministic_vector(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generates a deterministic 1536-dimensional normalized embedding vector using SHA-256 n-gram hashes.
    Guarantees consistent cosine similarity in mock / offline / CI test environments without API cost.
    """
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec

    for idx, word in enumerate(words):
        # Generate 3 hash positions per word
        for seed in range(3):
            h_str = f"{word}_{seed}_{idx}"
            h_val = int(hashlib.sha256(h_str.encode("utf-8")).hexdigest(), 16)
            pos = h_val % dim
            val = ((h_val >> 16) % 200 - 100) / 100.0
            vec[pos] += val

    # L2 normalize vector
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def generate_embedding(text: str) -> List[float]:
    """
    Generates 1536-dimensional embedding using OpenAI text-embedding-3-small if API key is present,
    or falls back to deterministic local Hash-Vectorizer.
    """
    openai_key = getattr(settings, "OPENAI_API_KEY", "").strip()
    provider = getattr(settings, "LLM_PROVIDER", "mock").lower()

    if provider == "openai" and openai_key:
        try:
            res = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={"input": text, "model": "text-embedding-3-small"},
                timeout=10.0,
            )
            if res.status_code == 200:
                return res.json()["data"][0]["embedding"]
        except Exception:
            pass

    return _generate_deterministic_vector(text)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def index_change_text(db: Session, org_id: UUID, change_id: UUID, full_text: str) -> int:
    """
    Chunks change text, generates embeddings, and persists ChangeEmbedding records.
    """
    # Clear any existing embeddings for this change_id
    db.query(ChangeEmbedding).filter(
        ChangeEmbedding.org_id == org_id, ChangeEmbedding.change_id == change_id
    ).delete()

    chunks = chunk_text(full_text)
    for idx, chunk in enumerate(chunks):
        vector = generate_embedding(chunk)
        embedding_record = ChangeEmbedding(
            org_id=org_id,
            change_id=change_id,
            chunk_index=idx,
            chunk_text=chunk,
            embedding_json=vector,
        )
        db.add(embedding_record)

    db.commit()
    return len(chunks)


def search_similar_chunks(
    db: Session, org_id: UUID, query_text: str, top_k: int = 3
) -> List[Tuple[ChangeEmbedding, float]]:
    """
    Semantic vector similarity search STRICTLY SCOPED to requesting organization (org_id).
    Ensures zero cross-tenant vector leakage.
    """
    query_vector = generate_embedding(query_text)

    # Filter embeddings strictly by org_id
    candidates = (
        db.query(ChangeEmbedding)
        .filter(ChangeEmbedding.org_id == org_id)
        .all()
    )

    scored: List[Tuple[ChangeEmbedding, float]] = []
    for candidate in candidates:
        if candidate.embedding_json:
            sim = cosine_similarity(query_vector, candidate.embedding_json)
            scored.append((candidate, sim))

    # Sort descending by cosine similarity
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
