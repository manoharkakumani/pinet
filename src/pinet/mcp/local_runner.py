# pinet/mcp/local_runner.py
from typing import Any, Dict
import pinet.tools as pinet_tools
from .runner import MCPRunner

import asyncio

class LocalMCPRunner(MCPRunner):
    def __init__(self, tools):
        self.tools = {}
        for tool in tools:
            self.tools[tool] = getattr(pinet_tools, tool)
        

    async def initialize(self) -> Dict[str, Any]:
        return {"status": "local-mcp-ready"}

    async def list_tools(self) -> Dict[str, Any]:
        return {"result": {"tools": self.tools}}

    async def list_resources(self) -> Dict[str, Any]:
        return {"result": {"resources": []}}

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        func = self.tools.get(name, None)
        if callable(func):
            try:
                # await if async
                result = await func(**arguments) if asyncio.iscoroutinefunction(func) else func(**arguments)
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Tool '{name}' not found"}

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        return {"error": "LocalMCP does not support resources"}

    async def close(self):
        pass
