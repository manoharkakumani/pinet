from pinet import Agent, Supervisor, RestartStrategy, RemoteServer
import asyncio

import logging
logging.basicConfig(level=logging.INFO)

llm_config = {
    "provider": "anthropic",
    "api_key": "ANTHROPIC_API_KEY"
}

mcp_config = {
    "brave": {
        "command": "npx -y @modelcontextprotocol/server-brave-search",
        "env": {"BRAVE_API_KEY": "BRAVE_API_KEY"}
    },
    "fetch": {
        "command": "uvx mcp-server-fetch"
    }

}

supervisor = Supervisor("supervisor", strategy=RestartStrategy.ONE_FOR_ONE)

async def main():

    agent1 = await Agent.create(
        name="websearch",
        description="A helpful assistant that can search for information on the web",
        goal="To answer questions and help users with information on the web",
        role="Assistant",
        llm_config=llm_config,
        mcp_config=mcp_config,
        supervisor=supervisor,
    )
    agent2 = await Agent.create(
        name="fetch",
        description="A helpful assistant that can search for information on the web",
        goal="To answer questions and help users with information on the web",
        role="Assistant",
        llm_config=llm_config,
        mcp_config=mcp_config,
        supervisor=supervisor,
    )

    agent3 = await Agent.create(
        name="agent3",
        description="A helpful assistant",
        goal="To answer questions and help users",
        role="Assistant",
        llm_config=llm_config,
        mcp_config=mcp_config,
        supervisor=supervisor,
    )

    agents = [agent1, agent2, agent3]

    server = RemoteServer(host="localhost", port=8765, auth="supersecret")
    await server.start(agents)


if __name__ == "__main__":
    asyncio.run(main())

    
