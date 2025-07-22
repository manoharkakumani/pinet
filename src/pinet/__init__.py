"""Pinet - Erlang/OTP-inspired actor framework."""

from .behaviours import Actor, Supervisor, RestartStrategy, ActorSystem
from .agent import Agent
from .mcp import MCP
from .llms import LLM
from .remote import RemoteClient, RemoteServer, Router, Auth
from .voice import Voice
from .taskflow import TaskFlow
from .task import Task
from .pinetai import PinetAI

__version__ = "0.1.0"
__author__ = "Manohar"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Manohar"
__url__ = "https://github.com/manoharkakumani/pinet"

__all__ = [
    "Actor",
    "Supervisor",
    "RestartStrategy",
    "ActorSystem",
    "MCP",
    "LLM",
    "Agent",
    "RemoteClient",  
    "RemoteServer",
    "Router",
    "Auth",
    "Voice",
    "TaskFlow",
    "Task",
    "PinetAI"
    "__version__",
]