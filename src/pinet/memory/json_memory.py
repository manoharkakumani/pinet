### pinet/memory/json_memory.py
import json
from pathlib import Path
from .base import VectorStore
from typing import List

class JSONMemory(VectorStore):
    def __init__(self, agent_name: str):
        self.path = Path("./agent_data") / f"{agent_name}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self.load()

    def load(self):
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except Exception:
                return []
        return []

    def get_messages(self) -> List[dict]:
        return self.load()

    def add(self, item: str):
        self.data.append(item)

    def search(self, query: str, top_k: int = 3):
        return self.data[-top_k:]  # simple tail for context

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2))

    def clear(self):
        self.path.unlink()