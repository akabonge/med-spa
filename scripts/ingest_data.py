"""
Ingests all data files into ChromaDB for RAG retrieval.
Run once before starting the server: python scripts/ingest_data.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from app.config import get_settings
from app.rag.embedder import embed

DATA_DIR = ROOT / "data"


def load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_treatment(t: dict) -> list[tuple[str, str]]:
    chunks = []
    base_id = f"treatment_{t['id']}"
    overview = (
        f"Treatment: {t['name']}\n"
        f"Category: {t['category']}\n"
        f"Concerns addressed: {', '.join(t['concerns_addressed'])}\n"
        f"Description: {t['description']}"
    )
    chunks.append((f"{base_id}_overview", overview))
    pricing = (
        f"Treatment: {t['name']}\n"
        f"Pricing: {t['price_range']}\n"
        f"Sessions needed: {t['sessions_needed']}\n"
        f"Downtime: {t['downtime']}"
    )
    chunks.append((f"{base_id}_pricing", pricing))
    candidacy = (
        f"Treatment: {t['name']}\n"
        f"Candidacy and contraindications: {t['candidacy_notes']}"
    )
    chunks.append((f"{base_id}_candidacy", candidacy))
    return chunks


def chunk_faq(i: int, faq: dict) -> tuple[str, str]:
    return (
        f"faq_{i}",
        f"Q: {faq['question']}\nA: {faq['answer']}"
    )


def chunk_provider(p: dict) -> tuple[str, str]:
    slug = p["name"].lower().replace(" ", "_").replace(",", "")
    text = (
        f"Provider: {p['name']}, {p['title']}\n"
        f"Bio: {p['bio']}\n"
        f"Specialties: {', '.join(p['specialties'])}"
    )
    return (f"provider_{slug}", text)


def chunk_package(i: int, pkg: dict) -> tuple[str, str]:
    text = (
        f"Package: {pkg['name']}\n"
        f"Includes: {', '.join(pkg['treatments'])}\n"
        f"Description: {pkg['description']}\n"
        f"Price: {pkg['price']}\n"
        f"Ideal for: {', '.join(pkg['ideal_for'])}"
    )
    return (f"package_{i}", text)


def main():
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_path)

    try:
        client.delete_collection(settings.chroma_collection_name)
        print("Cleared existing collection.")
    except Exception:
        pass

    collection = client.create_collection(settings.chroma_collection_name)

    ids, docs = [], []

    for t in load_json("treatments.json"):
        for chunk_id, chunk_text in chunk_treatment(t):
            ids.append(chunk_id)
            docs.append(chunk_text)

    for i, faq in enumerate(load_json("faqs.json")):
        cid, text = chunk_faq(i, faq)
        ids.append(cid)
        docs.append(text)

    for p in load_json("providers.json"):
        cid, text = chunk_provider(p)
        ids.append(cid)
        docs.append(text)

    for i, pkg in enumerate(load_json("packages.json")):
        cid, text = chunk_package(i, pkg)
        ids.append(cid)
        docs.append(text)

    print(f"Embedding {len(docs)} chunks...")
    embeddings = embed(docs)

    batch_size = 50
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i:i + batch_size],
            documents=docs[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
        )
        print(f"  Ingested {min(i + batch_size, len(ids))}/{len(ids)}")

    print(f"\nDone. {collection.count()} chunks in ChromaDB.")


if __name__ == "__main__":
    main()
