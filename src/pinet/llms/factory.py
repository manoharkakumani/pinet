# pinet/llms/factory.py

from typing import Optional
from pinet.llms.anthropic_llm import AnthropicLLM
from pinet.llms.openai_llm import OpenAILLM
from pinet.llms.ollama_llm import OllamaLLM
from pinet.llms.grok_llm import GrokLLM

import os


def create_llm(provider: str, vision: bool = False, **kwargs):
    provider = provider.lower()
    if vision:
        if provider == "openai":
            return OpenAILLM(api_key=kwargs.get("api_key", os.getenv("OPENAI_API_KEY")), model=kwargs.get("model", "gpt-4o-vision-preview"), system=kwargs.get("system", "You are a helpful assistant."))
        elif provider == "anthropic":
            return AnthropicLLM(api_key=kwargs.get("api_key", os.getenv("ANTHROPIC_API_KEY")), model=kwargs.get("model", "claude-3-opus-20240229"), system=kwargs.get("system", "You are a helpful assistant."))
        elif provider == "grok":
            return GrokLLM(token=kwargs.get("api_key", os.getenv("GROK_API_KEY")), model=kwargs.get("model", "grok-1"), system=kwargs.get("system", "You are a helpful assistant."))
        elif provider == "ollama":
            return OllamaLLM(model=kwargs.get("model", "mistral"), host=kwargs.get("host", "http://localhost:11434"), system=kwargs.get("system", "You are a helpful assistant."))
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    else:
        if provider == "anthropic":
            return AnthropicLLM(api_key=kwargs.get("api_key", os.getenv("ANTHROPIC_API_KEY")), model=kwargs.get("model", "claude-3-opus-20240229"), system=kwargs.get("system", "You are a helpful assistant."))

        elif provider == "openai":
            return OpenAILLM(api_key=kwargs.get("api_key", os.getenv("OPENAI_API_KEY")), model=kwargs.get("model", "gpt-4o"), system=kwargs.get("system", "You are a helpful assistant."))

        elif provider == "ollama":
            return OllamaLLM(model=kwargs.get("model", "mistral"), host=kwargs.get("host", "http://localhost:11434"), system=kwargs.get("system", "You are a helpful assistant."))

        elif provider == "grok":
            return GrokLLM(token=kwargs.get("api_key", os.getenv("GROK_API_KEY")), model=kwargs.get("model", "grok-1"), system=kwargs.get("system", "You are a helpful assistant."))

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
