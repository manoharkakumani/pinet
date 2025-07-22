# pinet/remote/router.py

# AGENT_HOST_MAP = {
#     "default": "ws://localhost:8765",
#     "worker1": "ws://192.168.1.10:8765",
#     "worker2": "ws://192.168.1.11:8765",
# }

from collections import defaultdict
import asyncio


class Router:
    def __init__(self):
        self.agents = defaultdict()
        self.indices = defaultdict(int)
        self.lock = asyncio.Lock()

    def register(self, logical_name: str, agent):
        if logical_name in self.agents:
            raise ValueError(f"Agent '{logical_name}' already registered")
        self.agents[logical_name] = agent
        print(f"[Router] Registered agent '{agent.name}' under '{logical_name}'")
    
    def resolve_agent(self, agent_name: str) -> str:
        return self.agents.get(agent_name)
    
    def unregister(self, logical_name: str):
        self.agents.pop(logical_name)
        print(f"[Router] Unregistered agent '{logical_name}'")

    # async def get_next(self, logical_name: str):
    #     async with self.lock:
    #         group = self.agents.get(logical_name , [])
    #         if not group:
    #             return None
    #         index = self.indices[logical_name] % len(group)
    #         self.indices[logical_name] += 1
    #         return group[index]
        
        