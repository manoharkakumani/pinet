### pinet/memory/base.py
from abc import ABC, abstractmethod
from typing import List, Union

class VectorStore(ABC):
    @abstractmethod
    def add(self, item: Union[str, dict]):
        """Add a message or item to memory."""
        pass

    @abstractmethod
    def get_messages(self) -> List[dict]:
        """Return a list of usable messages (for context)."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Search memory and return top-k results."""
        pass

    def load(self) -> List[str]:
        """Load memory state if applicable."""
        return []

    def save(self):
        """Persist memory state if needed."""
        pass
