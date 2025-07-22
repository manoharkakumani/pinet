# pinet/llms/anthropic_llm.py

from anthropic import AsyncAnthropic
from pinet.llms.base import BaseLLM
from typing import List, Dict, Optional
import logging

class AnthropicLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", system: Optional[str] = None):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.system = system

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        logging.info(f"Anthropic sending messages")
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,  
            max_tokens=1024,
            system=self.system
        )

        logging.info(f"Anthropic response")
        return response.content[0].text if response.content else "[no content]"

    async def complete(self, prompt: str) -> str:
        raise NotImplementedError("AnthropicLLM does not support 'complete', use 'chat' instead.")
