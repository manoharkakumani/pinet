from .runner import MCPRunner
from typing import Dict, Any, Optional
import httpx
from .errors import MCPConnectionError
from .errors import MCPProtocolError

class SSEMCPRunner(MCPRunner):
    """MCP runner for SSE-based servers"""
    
    def __init__(self, endpoint: str, token: Optional[str] = None):
        self.endpoint = endpoint.rstrip('/')
        self.token = token
        self.client = None
        self.initialized = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get SSE headers"""
        headers = {"Accept": "text/event-stream", "Cache-Control": "no-cache"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _make_sse_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an SSE request"""
        if not self.client:
            self.client = httpx.AsyncClient()
        
        payload = {
            "method": method,
            "params": params or {}
        }
        
        try:
            response = await self.client.post(
                f"{self.endpoint}/sse",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise MCPConnectionError(f"SSE error: {e}")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection"""
        response = await self._make_sse_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "clientInfo": {
                "name": "generalized-mcp-client",
                "version": "1.0.0"
            }
        })
        
        self.initialized = True
        return response
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_sse_request("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_sse_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_sse_request("resources/list")
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_sse_request("resources/read", {"uri": uri})
    
    async def close(self):
        """Close the connection"""
        if self.client:
            await self.client.aclose()
            self.client = None
