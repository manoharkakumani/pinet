from pinet import Agent, Supervisor, RestartStrategy, Task, PinetAI
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

    agent = await Agent.create(
        name="agent",
        llm_config=llm_config,
        mcp_config=mcp_config,
        supervisor=supervisor,
    )

    # await agent.serve(port=8000)
    await agent.start()
    await agent.ask("Search for AI in healthcare")
    # await agent.ask("What did you find in your search?")
    await agent.ask("fetch https://manoharkakumani.com and tell me about it")
    await agent.stop()
   




if __name__ == "__main__":
    asyncio.run(main())