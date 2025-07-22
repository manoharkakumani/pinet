# pinet/llms/grok_llm.py

import httpx
from typing import List, Dict, Optional
from .base import BaseLLM

class GrokLLM(BaseLLM):
    def __init__(self, token: str, model: str = "grok-1", system: Optional[str] = None):
        self.token = token
        self.model = model
        self.base_url = "https://grok.openapi.musk/api/chat"
        self.system = system

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "system_prompt": self.system
                }
            )
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

    async def complete(self, prompt: str) -> str:
        return await self.chat([{"role": "user", "content": prompt}])
