import asyncio
from pinet import Agent

async def main():
    alice = await Agent.create(name="alice", 
                               description="A helpful assistant",
                               goal="To answer questions and help users",
                               role="Assistant",
                               llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                               mcp_config={"command": "npx -y @modelcontextprotocol/server-brave-search", 
                               "env": {"BRAVE_API_KEY": "BRAVE_API_KEY"}})

    await alice.start()
    await alice.ask("Search for AI in healthcare 2025")
    await alice.stop()

if __name__ == "__main__":
    asyncio.run(main())
