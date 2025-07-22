from pinet.agent import Agent
from pinet.supervisor import Supervisor
from pinet.memory import load_memory
from pinet.llms.factory import create_llm
from pinet.mcp import MCP
from pinet import tools as local_tools
from pinet import RestartStrategy

async def create_agents(master: Agent, config: Dict[str, Any]):
    agents = []
    for name, role in config.get("roles", {}).items():
        agent = await Agent(name=name)
        agent.llm = master.llm
        agent.memory = load_memory(name, role.get("memory", {"enabled": True, "memory": {"type": "json"}}))
        agents.append(agent)
    return agents
    