# 📁 pinet/mcp/errors.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class MCPError(Exception):
    """Base exception for MCP operations"""
    pass

class MCPConnectionError(MCPError):
    """Connection-related MCP errors"""
    pass

class MCPProtocolError(MCPError):
    """Protocol-related MCP errors"""
    pass

class MCPRunner(ABC):
    """Abstract base class for MCP runners"""
    
    @abstractmethod
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the connection"""
        pass
