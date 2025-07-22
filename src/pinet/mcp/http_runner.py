# 📁 pinet/mcp/http_runner.py
import httpx
from .runner import MCPRunner
from .errors import MCPConnectionError, MCPProtocolError
from typing import Dict, Any, Optional, Union

class HTTPMCPRunner(MCPRunner):
    """MCP runner for HTTP-based servers"""
    
    def __init__(self, endpoint: str, token: Optional[str] = None, verify_ssl: bool = True):
        self.endpoint = endpoint.rstrip('/')
        self.token = token
        self.verify_ssl = verify_ssl
        self.client = None
        self.initialized = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request"""
        if not self.client:
            self.client = httpx.AsyncClient(verify=self.verify_ssl)
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method
        }
        
        if params:
            payload["params"] = params
        
        try:
            response = await self.client.post(
                f"{self.endpoint}/mcp",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                raise MCPProtocolError(f"MCP error: {result['error']}")
            
            return result
        except httpx.HTTPError as e:
            raise MCPConnectionError(f"HTTP error: {e}")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection"""
        response = await self._make_request("initialize", {
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
        
        return await self._make_request("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_request("resources/list")
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource"""
        if not self.initialized:
            await self.initialize()
        
        return await self._make_request("resources/read", {"uri": uri})
    
    async def close(self):
        """Close the connection"""
        if self.client:
            await self.client.aclose()
            self.client = None
