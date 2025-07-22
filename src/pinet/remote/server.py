# pinet/remote/server.py

import asyncio
import json
import websockets
from pinet import Agent
from .auth import Auth
from typing import Dict, List, Optional
from .router import Router
import logging

logging.basicConfig(level=logging.INFO)

class RemoteServer:
    def __init__(self,  
                 host="localhost", 
                 port=8765, 
                 auth: Optional[str] = None):
        self.host = host
        self.port = port
        self.auth = Auth(auth or "supersecret")
        self.tokens = {}
        self.router = Router()
        
    async def ws_handler(self, websocket):
        try:
            auth_msg = await websocket.recv()
            auth_data = json.loads(auth_msg)
            if not self.auth.verify_token(auth_data.get("auth"), auth_data.get("agent_name")):
                await websocket.send(json.dumps({"error": "Unauthorized"}))
                await websocket.close()
                return

            async for message in websocket:
                try:
                    data = json.loads(message)
                    kind = data["kind"]
                    method = data["method"]
                    payload = data["payload"]
                    target = data.get("target", "default")

                    agent = self.router.resolve_agent(target)
                    if not agent:
                        await websocket.send(json.dumps({"error": f"Agent '{target}' not found"}))
                        continue
                    if kind == "ask":
                        logging.info(f" Asking  {target}")
                        result = await agent.ask(payload)
                        await websocket.send(json.dumps({"result": result}))
                    elif kind == "cast":
                        logging.info(f" Casting {method} to {target}")
                        await agent.cast(method, payload)
                        await websocket.send(json.dumps({"result": "ok"}))
                    elif kind == "remember":
                        logging.info(f" Remembering {payload} to {target}")
                        await agent.remember(payload)
                        await websocket.send(json.dumps({"result": "ok"}))

                except Exception as e:
                    logging.error(f"⚠️ Error processing message: {e}")
                    await websocket.send(json.dumps({"error": str(e)}))

        except websockets.ConnectionClosed as e:
            logging.info(f"🔌 Connection closed: {e.code} - {e.reason}")
        except Exception as e:
            print(f"🔥 Unexpected error: {e}")


    async def start(self, agents: List[Agent]):
        """Start the server and register agents
        
        Args:
            agents (List[Agent]): List of agents to register 
        """
        for agent in agents:
            await agent.start()
            self.tokens[agent.name] = self.auth.generate_token(agent.name)
            self.router.register(agent.name, agent)
        async with websockets.serve(self.ws_handler, self.host, self.port):
            print(f"🌐 Listening on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    auth = os.getenv("AUTH_TOKEN", "supersecret")
    server = RemoteServer(host="localhost", port=8765, auth=auth)

    asyncio.run(server.start([Agent.create("default")]))

