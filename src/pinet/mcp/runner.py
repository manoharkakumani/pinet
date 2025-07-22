# 📁 pinet/mcp/runner.py
import abc
from typing import Dict, Any

class MCPRunner(abc.ABC):
    @abc.abstractmethod
    async def initialize(self) -> Dict[str, Any]: pass

    @abc.abstractmethod
    async def list_tools(self) -> Dict[str, Any]: pass

    @abc.abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]: pass

    @abc.abstractmethod
    async def list_resources(self) -> Dict[str, Any]: pass

    @abc.abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]: pass

    @abc.abstractmethod
    async def close(self): pass