import asyncio
from pinet import Agent

async def main():
    alice = await Agent.create(name="alice",
                               description="A helpful assistant",
                               goal="To answer questions and help users",
                               role="Assistant",
                               llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"})
    await alice.start()
    await alice.ask("What is the capital of France?")
    await alice.stop()

if __name__ == "__main__":
    asyncio.run(main())
