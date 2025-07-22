# pinet/remote/proxy.py

import json
import asyncio
import websockets
from .auth import Auth

class RemoteClient:
    def __init__(self, agent_name: str,  url="ws://localhost:8765", auth: str = "supersecret", reconnect_attempts=3, backoff=1.0,):
        self.agent_name = agent_name
        self.auth = Auth(auth or "supersecret")
        self.url = url
        self.token = self.auth.generate_token(agent_name)
        self.ws = None
        self.reconnect_attempts = reconnect_attempts
        self.backoff = backoff
        self._lock = asyncio.Lock()

    async def _connect(self):
        for attempt in range(self.reconnect_attempts):
            try:
                ws = await websockets.connect(self.url)
                await ws.send(json.dumps({"auth": self.token, "agent_name": self.agent_name}))
                return ws
            except Exception as e:
                print(f"Retrying connection ({attempt+1}/3)...")
                await asyncio.sleep(1)
        raise RuntimeError("Failed to connect after 3 retries")

    async def _send(self, message: dict):
        message["token"] = self.token
        message["target"] = self.agent_name

        async with self._lock:
            self.ws = await self._connect()
            try:
                await self.ws.send(json.dumps(message))
                if message["kind"] == "ask":
                    resp = await self.ws.recv()
                    data = json.loads(resp)
                    if "error" in data:
                        raise RuntimeError(f"[RemoteClient] Error: {data['error']}")
                    return data["result"]
                elif message["kind"] == "cast":
                    resp = await self.ws.recv()
                    data = json.loads(resp)
                    if "error" in data:
                        raise RuntimeError(f"[RemoteClient] Error: {data['error']}")
                    return data["result"]
                elif message["kind"] == "remember":
                    resp = await self.ws.recv()
                    data = json.loads(resp)
                    if "error" in data:
                        raise RuntimeError(f"[RemoteClient] Error: {data['error']}")
                    return data["result"]
            except websockets.ConnectionClosed:
                raise RuntimeError("[RemoteClient] Lost connection during send")
            finally:
                await self.ws.close()  # ✅ Ensures proper close frame sent
                self.ws = None

    async def ask(self, payload):
        return await self._send({
            "kind": "ask",
            "method": "ask",
            "payload": payload,
        })

    async def remember(self, payload):
        return await self._send({
            "kind": "remember",
            "method": "remember",
            "payload": payload,
        })

    async def cast(self, method: str, payload):
        await self._send({
            "kind": "cast",
            "method": method,
            "payload": payload,
        })
