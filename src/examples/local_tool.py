import asyncio
from pinet import Agent

async def main():
    alice = await Agent.create(name="alice",
                               description="A helpful assistant",
                               goal="To answer questions and help users",
                               role="Assistant",
                               tools={"wiki_search": "local"})
    await alice.start()
    await alice.ask("Artificial intelligence in healthcare")
    await alice.stop()

if __name__ == "__main__":
    asyncio.run(main())
