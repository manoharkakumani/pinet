# pinet/llms/ollama_llm.py

from ollama import AsyncClient
from pinet.llms.base import BaseLLM
from typing import List, Dict, Optional

class OllamaLLM(BaseLLM):
    def __init__(self, model: str = "mistral", host: str = "http://localhost:11434", system: Optional[str] = None):
        self.model = model
        self.client = AsyncClient(host=host)
        self.system = system

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        return await self.complete(prompt)

    async def complete(self, prompt: str) -> str:
        response = await self.client.generate(model=self.model, prompt=prompt)
        return response['response'].strip() if 'response' in response else "[no content]"
