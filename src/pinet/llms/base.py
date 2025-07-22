# pinet/llms/base.py

from abc import ABC, abstractmethod
from typing import List, Dict

class BaseLLM(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Simple prompt completion"""
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat-style interaction using message history"""
        pass
