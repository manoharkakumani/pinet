
### pinet/memory/__init__.py
from .json_memory import JSONMemory
from .vector_chroma import ChromaMemory
from .hybrid import HybridMemory
from .knowledge_graph import KnowledgeGraphMemory

def load_memory(agent_name: str, config: dict):
    backend = config.get("type", "json")
    if backend == "json":
        return JSONMemory(agent_name)
    elif backend == "chroma":
        return ChromaMemory(agent_name)
    elif backend == "hybrid":
        return HybridMemory(agent_name, config.get("components", []))
    elif backend == "kg":
        return KnowledgeGraphMemory(agent_name)
    else:
        raise ValueError(f"Unknown memory backend: {backend}")

__all__ = ["load_memory", "JSONMemory", "ChromaMemory", "HybridMemory", "KnowledgeGraphMemory"]

