import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Union
from .errors import MCPConnectionError, MCPProtocolError
from .runner import MCPRunner


class StdioMCPRunner(MCPRunner):
    """MCP runner for stdio-based servers"""
    
    def __init__(self, command: Union[str, List[str]], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.env = env or {}
        self.process = None
        self.request_id = 0
        self.initialized = False
    
    async def _start_process(self):
        """Start the subprocess"""
        env = os.environ.copy()
        env.update(self.env)
        
        if isinstance(self.command, str):
            self.process = await asyncio.create_subprocess_shell(
                self.command,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
    
    async def _send_request(self, request: Dict[str, Any]) -> None:
        """Send a JSON-RPC request"""
        if not self.process:
            raise MCPConnectionError("Process not started")
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
    
    async def _read_response(self) -> Dict[str, Any]:
        """Read a JSON-RPC response"""
        if not self.process:
            raise MCPConnectionError("Process not started")
        
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise MCPConnectionError("No response from MCP server")
        
        try:
            return json.loads(response_line.decode().strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_line}")
            raise MCPProtocolError(f"Invalid JSON response: {e}")
    
    async def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a JSON-RPC request and return the response"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        await self._send_request(request)
        response = await self._read_response()
        
        if "error" in response:
            raise MCPProtocolError(f"MCP error: {response['error']}")
        
        return response
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection"""
        if not self.process:
            await self._start_process()
        
        # Send initialize request
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
        
        # Send initialized notification
        await self._send_request({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
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
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None