import chromadb
from app.config import get_settings
from app.rag.embedder import embed


def _collection():
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_path)
    return client.get_or_create_collection(settings.chroma_collection_name)


def retrieve(query: str) -> tuple[str, list[str]]:
    settings = get_settings()
    collection = _collection()

    if collection.count() == 0:
        return "", []

    query_embedding = embed([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(settings.max_retrieved_chunks, collection.count()),
    )

    docs = results["documents"][0]
    ids = results["ids"][0]

    context = "\n\n---\n\n".join(docs)
    sources = list(dict.fromkeys(
        ids[i].split("_chunk_")[0] for i in range(len(ids))
    ))
    return context, sources
