"""Wrapper around ChromaDB for per-agent knowledge collections.

Each agent gets its own collection (named `agent_<agent_id>`) so that
retrieval is automatically scoped and one agent can never leak another
agent's uploaded knowledge into a response.
"""
import chromadb

from app.config import settings

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return _client


def get_agent_collection(agent_id: str):
    """Get (or create) the ChromaDB collection scoped to a single agent."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=f"agent_{agent_id}")


def add_chunks(agent_id: str, file_id: str, chunks: list[str]) -> None:
    """Embeds and stores chunks for a given knowledge file under an agent's collection."""
    if not chunks:
        return
    collection = get_agent_collection(agent_id)
    ids = [f"{file_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"file_id": file_id, "chunk_index": i} for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)


def query_knowledge(agent_id: str, query: str, top_k: int = 4) -> list[str]:
    """Returns the top_k most relevant chunks for a query, scoped to the agent."""
    collection = get_agent_collection(agent_id)
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
    documents = result.get("documents", [[]])
    return documents[0] if documents else []


def delete_file_chunks(agent_id: str, file_id: str) -> None:
    """Removes all chunks belonging to a specific knowledge file."""
    collection = get_agent_collection(agent_id)
    collection.delete(where={"file_id": file_id})
