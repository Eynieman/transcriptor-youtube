import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

_embedding_model = None
_client = None


def _get_persist_directory() -> Path:
    path = Path(__file__).resolve().parent.parent / "chroma_db"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_chroma_client():
    global _client
    if _client is None:
        if chromadb is None or Settings is None:
            raise ImportError("chromadb es necesario para retrieval_service.py")
        _client = chromadb.Client(
            Settings(chroma_db_impl="duckdb+parquet", persist_directory=str(_get_persist_directory()))
        )
    return _client


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError("sentence-transformers es necesario para calcular embeddings locales") from exc
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=False, show_progress_bar=False)
    return [list(embedding) for embedding in embeddings]


def _get_collection(name: str = "youtube_transcripts"):
    client = _get_chroma_client()
    try:
        return client.get_collection(name=name)
    except ValueError:
        return client.create_collection(name=name)


def index_chunks(
    chunks: List[Dict[str, Any]],
    collection_name: str = "youtube_transcripts",
    persist: bool = True,
) -> None:
    collection = _get_collection(collection_name)
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "video_id": chunk.get("video_id"),
            "title": chunk.get("title"),
            "start_time": chunk.get("start_time"),
            "end_time": chunk.get("end_time"),
            "word_count": chunk.get("word_count"),
            "segment_count": chunk.get("segment_count"),
        }
        for chunk in chunks
    ]
    embeddings = embed_texts(documents)
    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    if persist:
        _get_chroma_client().persist()


def query(
    query_text: str,
    k: int = 4,
    filter: Optional[Dict[str, Any]] = None,
    collection_name: str = "youtube_transcripts",
) -> List[Dict[str, Any]]:
    collection = _get_collection(collection_name)
    query_kwargs = {
        "query_texts": [query_text],
        "n_results": k,
    }
    if filter:
        query_kwargs["where"] = filter

    results = collection.query(**query_kwargs)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {
            "text": doc,
            "metadata": metadata,
            "distance": distances[index] if index < len(distances) else None,
        }
        for index, (doc, metadata) in enumerate(zip(documents, metadatas))
    ]
