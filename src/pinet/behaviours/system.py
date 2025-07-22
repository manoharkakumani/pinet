# pinet/system.py

import logging
logger = logging.getLogger(__name__)

class ActorSystem:
    """
    Central coordinator for actors, supervisors, and remote control.
    """

    def __init__(self):
        self.supervisors = {}  # local supervision trees
        self.agents = {}       # local agents
        self.remotes = {}      # remote proxies

    def add_supervisor(self, sup):
        self.supervisors[sup.name] = sup

    def register_agent(self, agent):
        self.agents[agent.name] = agent

    def register_remote(self, name, proxy):
        self.remotes[name] = proxy

    def get_agent(self, name):
        return self.agents.get(name) or self.remotes.get(name)

    def list_agents(self):
        return list(self.agents.keys()) + list(self.remotes.keys())

    def list_supervisors(self):
        return list(self.supervisors.keys())

    async def broadcast(self, method, payload):
        for agent in self.agents.values():
            await agent.cast(method, payload)

    async def shutdown(self):
        for agent in self.agents.values():
            await agent.stop()
