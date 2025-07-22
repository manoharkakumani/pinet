


### pinet/memory/hybrid.py
from .json_memory import JSONMemory
from .vector_chroma import ChromaMemory
from typing import List
from .base import VectorStore

class HybridMemory(VectorStore):
    def __init__(self, agent_name: str, components_config: list):
        self.components = []
        for config in components_config:
            if config["type"] == "json":
                self.components.append(JSONMemory(agent_name))
            elif config["type"] == "chroma":
                self.components.append(ChromaMemory(agent_name))

    def get_messages(self) -> List[dict]:
        messages = []
        for comp in self.components:
            if hasattr(comp, "get_messages"):
                messages.extend(comp.get_messages())
        return messages

    def load(self, *args, **kwargs):
        return self.get_messages()

    def add(self, item: str):
        for comp in self.components:
            comp.add(item)

    def search(self, query: str, top_k: int = 3):
        results = []
        for comp in self.components:
            results.extend(comp.search(query, top_k))
        return results[:top_k]  # naive merge

    def save(self):
        for comp in self.components:
            comp.save()

    def clear(self):
        for comp in self.components:
            comp.clear()