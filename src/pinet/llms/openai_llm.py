# pinet/llms/openai_llm.py

from openai import AsyncOpenAI
from pinet.llms.base import BaseLLM
from typing import List, Dict, Optional
import os
import logging

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o", system: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.system = system

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        logging.info(f"OpenAI sending messages")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024,
            system_prompt=self.system
        )
        logging.info(f"OpenAI response")
        return response.choices[0].message.content.strip()

    async def complete(self, prompt: str) -> str:
        logging.info(f"OpenAI sending: {prompt}")
        response = await self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens=1024
        )
        return response.choices[0].text.strip()
