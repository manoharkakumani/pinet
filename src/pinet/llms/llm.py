from typing import List, Dict, Optional, Any
from pinet.llms.factory import create_llm
from pinet.llms.base import BaseLLM

class LLM(BaseLLM):
    def __init__(self, name: str, llm_config: Optional[Dict[str, Any]] = None, system: Optional[str] = None):
        self.name = name
        self.llm_config = llm_config
        self.llm = create_llm(**llm_config)
        self.system = system

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        return await self.llm.chat(messages)

    async def complete(self, prompt: str) -> str:
        return await self.llm.complete(prompt)