# 📁 pinet/mcp/mcp.py
from typing import Dict, Any, Optional, List, Union
from .stdio_runner import StdioMCPRunner
from .http_runner import HTTPMCPRunner
from .runner import MCPRunner
from .sse_runner import SSEMCPRunner
from .local_runner import LocalMCPRunner
from .errors import MCPConnectionError, MCPProtocolError
import logging

logger = logging.getLogger("mcp_client")

class MCP:
    """Generalized MCP client that can connect to any MCP server type"""
    
    def __init__(self, runner: MCPRunner):
        self.runner = runner
        self.tools_cache = None
        self.resources_cache = None
    
    @classmethod
    def from_stdio(cls, command: Union[str, List[str]], env: Optional[Dict[str, str]] = None):
        """Create client for stdio-based MCP server"""
        runner = StdioMCPRunner(command, env)
        return cls(runner)
    
    @classmethod
    def from_http(cls, endpoint: str, token: Optional[str] = None, verify_ssl: bool = True):
        """Create client for HTTP-based MCP server"""
        runner = HTTPMCPRunner(endpoint, token, verify_ssl)
        return cls(runner)
    
    @classmethod
    def from_sse(cls, endpoint: str, token: Optional[str] = None):
        """Create client for SSE-based MCP server"""
        runner = SSEMCPRunner(endpoint, token)
        return cls(runner)

    @classmethod
    def from_local(cls, tools: Optional[List[str]] = None):
        """Create client for local MCP server"""
        runner = LocalMCPRunner(tools)
        return cls(runner)
    
    @classmethod
    def create(cls, config: Dict[str, Any]):
        """Create client from configuration dictionary"""  
        if "command" in config:
            # Stdio mode
            return cls.from_stdio(
                config["command"],
                config.get("env")
            )
        elif "endpoint" in config:
            # HTTP mode
            return cls.from_http(
                config["endpoint"],
                config.get("token"),
                config.get("verify_ssl", True)
            )
        elif "sse_endpoint" in config:
            # SSE mode
            return cls.from_sse(
                config["sse_endpoint"],
                config.get("token")
            )
        elif "local" in config:
            # Local mode
            return cls.from_local(config["local"])
        else:
            raise ValueError("Invalid config: must specify 'command', 'endpoint', 'sse_endpoint', or 'local'")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection"""
        return await self.runner.initialize()
    
    async def get_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get available tools"""
        if self.tools_cache is None or force_refresh:
            response = await self.runner.list_tools()
            self.tools_cache = response.get("result", {}).get("tools", [])
        return self.tools_cache
    
    async def get_resources(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get available resources"""
        if self.resources_cache is None or force_refresh:
            try:
                response = await self.runner.list_resources()
                self.resources_cache = response.get("result", {}).get("resources", [])
            except MCPProtocolError:
                # Some servers might not support resources
                self.resources_cache = []
        return self.resources_cache
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool and return the result"""
        arguments = arguments or {}
        response = await self.runner.call_tool(name, arguments)
        if "result" in response:
            return response["result"]
        elif "error" in response:
            raise MCPProtocolError(f"Tool call failed: {response['error']}")
        else:
            return response
    
    async def read_resource(self, uri: str) -> Any:
        """Read a resource and return the content"""
        response = await self.runner.read_resource(uri)
        
        if "result" in response:
            return response["result"]
        elif "error" in response:
            raise MCPProtocolError(f"Resource read failed: {response['error']}")
        else:
            return response
    
    async def close(self):
        """Close the connection"""
        await self.runner.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()