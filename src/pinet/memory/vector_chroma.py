from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from .base import VectorStore

# Embedding interface
class LocalEmbedder:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def __call__(self, input):  # updated to match Chroma's expected signature
        return self.model.encode(input).tolist()

    def name(self):  # ✅ Add this method
        return "local-embedder"



# Chroma backend implementing the VectorStore interface
class ChromaMemory(VectorStore):
    def __init__(self, name: str):
        self.name = name
        self.client = chromadb.Client()
        self.path = Path("./agent_data") / name
        self.path.mkdir(parents=True, exist_ok=True)

        self.embedder = LocalEmbedder()
        self.collection = self.client.get_or_create_collection(name=self.name, embedding_function=self.embedder)

    def add(self, item: str | dict):
        if isinstance(item, dict):
            text = item.get("content", str(item))
        else:
            text = item
        doc_id = f"doc-{len(self.collection.get()['ids']) + 1}"
        self.collection.add(documents=[text], ids=[doc_id])

    def get_messages(self) -> List[dict]:
        results = self.collection.get(limit=10)
        docs = results.get("documents", [[]])[0]
        return [{"role": "assistant", "content": d} for d in docs if isinstance(d, str)]

    def search(self, query: str, top_k: int = 3) -> List[str]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        return results.get("documents", [[]])[0]

    def load(self) -> List[str]:
        return self.get_messages()

    def save(self):
        pass  # Chroma handles persistence internally
