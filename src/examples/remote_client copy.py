# examples/remote_client.py

import asyncio
from pinet import RemoteClient

async def main():
    client = RemoteClient("default", "ws://localhost:8765")
    await client.remember("This is a test from remote client")
    result = await client.ask("What did I say?")
    print("🔁 Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
