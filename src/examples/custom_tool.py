import asyncio
from pinet import Agent

"""
# You have to create a __pinet__ file in the current working directory as this file
# The __pinet__ file looks like this:

def add(a: int, b: int) -> int:
    return a + b

__tools__ = {
    "add": add
}

"""

async def main():
    alice = await Agent.create(name="alice",
                               description="A helpful assistant",
                               goal="To answer questions and help users",
                               role="Assistant",
                               tools={"add": "local"})
    await alice.start()
    await alice.ask("Add 2 and 3")
    await alice.stop()

if __name__ == "__main__":
    asyncio.run(main())
    