# pinet/agent.py

import inspect
import json
import logging
import re
from typing import Any, Dict, Optional
import inspect

from pinet.behaviours.gen_server import GenServer
from pinet.behaviours.supervisor import Supervisor
from pinet.llms.factory import create_llm
from pinet.memory import load_memory
from pinet.mcp import MCP
from pinet import tools as local_tools
from pinet.knowledge.rag_system import RAGSystem

import os

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_PROVIDER = os.getenv("LLM_PROVIDER")

logging.basicConfig(level=logging.INFO)

class Agent:
    def __init__(self, name: str):
        self.name = name
        self.description = None
        self.goal = None
        self.role = None
        self.llm = None
        self.llm_config = None
        self.mcps = {}
        self.memory = None
        self.use_memory = True
        self.server = None
        self.allowed_tools = {}
        self.team = {}

    def _maybe_save_memory(self):
        if self.use_memory and self.memory and hasattr(self.memory, "save"):
            self.memory.save()

    @classmethod
    async def create(
        cls,
        name: str,
        llm_config: Optional[Dict[str, Any]] = None,
        mcp_config: Optional[Dict[str, Any]] = None,
        supervisor: Optional[Supervisor] = None,
        description: Optional[str] = None,
        goal: Optional[str] = None,
        role: Optional[str] = None,
        memory: Optional[Dict[str, Any]] = {"enabled": True, "memory": {"type": "json"}},
        tools: Optional[Dict[str, str]] = None,  # {tool_name: "route_key"}
        team: Optional[Dict[str, Any]] = None,
        knowledge_source: Optional[str] = None,
    ):
        self = cls(name)
        self.role = role or "assistant"
        self.description = description or "an assistant"
        self.goal = goal or "Respond to user queries"
        self.use_memory = memory.get("enabled", True) if memory else True
        self.memory = load_memory(name, memory.get("memory", {"type": "json"})) if self.use_memory else None
        if tools == "__all__":
            tools = { tool_name: "local" for tool_name in local_tools.__all__ }
        self.allowed_tools = tools or {}
        self.team = { member.name: member for member in team } if team else {}
        self.llm_config = llm_config
        self.knowledge_source = knowledge_source

        # Initialize RAG system
        self.rag_system =  RAGSystem(name, knowledge_source) if knowledge_source else None

        # Initialize MCPs
        if isinstance(mcp_config, dict) and any("command" in v for v in mcp_config.values()):
            for key, val in mcp_config.items():
                self.mcps[key] = MCP.create(val)
                mcp_tools = await self.mcps[key].get_tools()
                for tool in mcp_tools:
                    self.allowed_tools[tool["name"]] = key
        elif mcp_config:
            self.mcps["default"] = MCP.create(mcp_config)
            mcp_tools = await self.mcps["default"].get_tools()
            for tool in mcp_tools:
                self.allowed_tools[tool["name"]] = "default"
        if tools:
            self.mcps["local"] = MCP.create({"local": [k for k in tools if tools[k] == "local"]})

        # Validate tools
        for tool_name, route in self.allowed_tools.items():
            if route == "local" and not hasattr(local_tools, tool_name): 
                raise ValueError(f"[{self.name}] Tool '{tool_name}' not found in local_tools")
            elif route not in self.mcps:
                raise ValueError(f"[{self.name}] Route '{route}' not found for tool '{tool_name}'")

        # Set LLM with prompt
        self.system_prompt = await self.build_system_prompt()
        if llm_config:
            llm_config["system"] = self.system_prompt
            self.llm = create_llm(**llm_config)
        elif LLM_API_KEY and LLM_MODEL and LLM_PROVIDER:
            llm_config = {
                "provider": LLM_PROVIDER,
                "api_key": LLM_API_KEY,
                "model": LLM_MODEL,
            }
            llm_config["system"] = self.system_prompt
            self.llm = create_llm(**llm_config) 

        # Set up GenServer
        self.server = GenServer(
            name,
            self._handler,
            initial_state={"memory": self.memory, "restart_count": 0},
            supervisor=supervisor,
            on_terminate=self._persist,
            on_restart=self.on_restart,
        )
        return self

    async def _persist(self, state: Dict[str, Any]):
        self._maybe_save_memory()

    async def _describe_tools(self) -> list[str]:
        """Generate signature lines for allowed tools across MCPs and local."""
        tool_lines = []
        for route, mcp in self.mcps.items():
            try:
                tools = await mcp.get_tools()
                if route == "local":
                    for tool_name, tool in tools.items():
                        if tool_name in self.allowed_tools:
                            tname = getattr(tool, "__name__", None)
                            doc = inspect.getdoc(tool)
                            if doc:
                                tool_lines.append(f"  # {doc.splitlines()[0]}")
                            try:
                                sig = str(inspect.signature(tool))
                            except Exception:
                                sig = "(...)"
                            tool_lines.append(f"- `{tname}{sig}` (via `{route}`)")
                        else:
                            logging.warning(f"[{self.name}] Unknown tool type")
                            continue
                else:
                    for tool in tools:
                        # Determine tool name
                        if isinstance(tool, dict):  # JSON-style tool description
                            tname = tool.get("name")
                            doc = tool.get("description")
                            input_schema = tool.get("inputSchema", {})
                            if not tname or tname not in self.allowed_tools:
                                continue
                            # Extract parameters from inputSchema
                            params = input_schema.get("properties", {})
                            required_params = input_schema.get("required", [])
                            # Build parameter signature
                            param_strs = []
                            for k, v in params.items():
                                param_type = v.get('type', 'any')
                                if k in required_params:
                                    param_strs.append(f"{k}: {param_type}")
                                else:
                                    param_strs.append(f"{k}?: {param_type}")
                            sig = ", ".join(param_strs)
                            tool_lines.append(f"- `{tname}({sig})` description: {doc} (via `{route}`)")
                        elif callable(tool):
                            tname = getattr(tool, "__name__", None)
                            if not tname or tname not in self.allowed_tools:
                                continue
                            doc = inspect.getdoc(tool)
                            if doc:
                                tool_lines.append(f"  # {doc.splitlines()[0]}")
                            try:
                                sig = str(inspect.signature(tool))
                            except Exception:
                                sig = "(...)"
                            tool_lines.append(f"- `{tname}{sig}` (via `{route}`)")
                        else:
                            logging.warning(f"[{self.name}] Unknown tool type")
                            continue  # Skip unknown tool type

            except Exception as e:
                logging.warning(f"[{self.name}] Failed to fetch tools from MCP '{route}': {e}")

        return tool_lines

    async def _describe_team(self):
        team_lines = []
        for team_member in self.team.values():
            team_lines.append(f"\n- name: {team_member.name}, role: {team_member.role}, goal: {team_member.goal}\n")
        return team_lines


    async def build_system_prompt(self) -> str:
        tool_lines = await self._describe_tools()
        team_lines = await self._describe_team()

        prompt = (f"""
You name is {self.name}, a helpful and capable AI assistant.  
{self.description}
Your assigned **role** is: {self.role}  
Your primary **goal** is: {self.goal}

---

## Behavior Guidelines

- When discussing your team or capabilities, speak naturally and directly without referencing where you learned this information. Treat your team as an established part of your working environment, not as external information you've been given.
- Always respond in the same language as the user.
- Always aim to deeply understand the user's intent before responding.
- Be concise, clear, and direct in your responses.
- Avoid unnecessary explanations or overuse of tools.
- Use tools or delegate tasks only when needed to achieve accurate, high-quality results.
- Do not make up information, tool names, or team members.
- End your responses naturally without unnecessary closing statements.
- Dont deviate from the topic.
- Stick to the name, role, goal, and description.
- Dont use any complex language or technical terms that the user may not understand.


## Strictly avoid phrases like:
- "Based on the information provided..."
- "According to my configuration..."
- "The system indicates that..."
- "I have been told that..."
- "My documentation shows..."
- "Let me know if you need anything else!"
- "These are the only team members I have access to"
- "Based on the information provided to me"
- "Feel free to ask if you have questions"
- "I hope this helps!"
- "Is there anything else I can assist you with?"
- "Please let me know how I can help further"

---
""")

        if self.allowed_tools:
            prompt += (f"""
## Tool Usage
You have access to the following optional tool(s):
{chr(10).join(tool_lines)}

**Use tools only when necessary** — for example, when a question cannot be answered directly with your own reasoning.
**To invoke a tool, respond in this exact format:**
[Tool Call] tool_name {{
"arg1": "value",
"arg2": "value"
}}
**Rules:**
- Only use tools explicitly listed above.
- Do **not** invent tool names or arguments.
- Never use tools for greetings, definitions, or general knowledge.

---
""")

        if self.team:
            prompt += (f"""
## Team Member Delegation

You may also delegate tasks to the following team members or worker agents:
{chr(10).join(team_lines)}

**To assign a task, use this exact format:**
[Assign To] team_member_name {{
"method": "method_name",
"payload": payload_content
}}

**Method must be one of:**
- `"ask"` for direct questions or requests (payload is a plain string).
- `"remember"` for storing data (payload is a JSON object or stringified JSON).

**Rules:**
- Only assign tasks to known, listed team members.
- Never guess team member names, methods, or payload formats.
- Ensure payload format matches the method.

--- 
""")
        prompt += (f"""
## Final Notes

- Always prefer direct, high-quality responses when possible.
- Use tools or delegate only if they produce significantly better results.
- Respect structure and formatting strictly to ensure task execution.
- End your responses naturally without unnecessary closing statements. Avoid these common tail phrases:
  

---
""")
        # print(prompt)
        return prompt

    async def start(self):
        await self.server.start()


    async def send_to(self, other: "Agent", method: str, payload: Any, await_reply: bool = True, role: str = "user") -> Any:
        if await_reply:
            # save message to memory
            if self.use_memory:
                self.memory.add({"role": role, "content": f"[Message sent to {other.name}] {payload}"})
                self._maybe_save_memory()
            response = await other.server.call(method, payload)
            if self.use_memory:
                self.memory.add({"role": role, "content": f"[Message response from {other.name}] {response}"})
                self._maybe_save_memory()
            return response
        else:
            await other.server.cast(method, payload)


    async def stop(self):
        await self.server.stop()

    async def ask(self, prompt: str) -> str:
        return await self.server.call("ask", prompt)

    async def remember(self, data: str):
        await self.server.cast("remember", data)

    async def cast(self, method: str, payload: dict):
        return await self.server.cast(method, payload)

    async def use_tool(self, tool_name: str, payload: dict):
        return await self.server.call("tool", {"name": tool_name, "payload": payload})

    async def _ask(self, prompt: str) -> str:
        logging.info(f"[{self.name}] Asking: {prompt}")
        if self.use_memory:
            self.memory.add({"role": "user", "content": prompt})
            self._maybe_save_memory()

        if self.rag_system:
            prompt = f"{prompt}\n\n[Knowledge] {self.rag_system.retrieve_and_generate(prompt)}"
        messages = (
            self.memory.get_messages()[-8:]
            if self.use_memory
            else [{"role": "user", "content": prompt}]
        ) 

        if self.llm :
            response = await self.llm.chat(messages)
        else:
            response = "No LLM configured"
       
        if self.use_memory:
            self.memory.add({"role": "assistant", "content": response})
            self._maybe_save_memory()
        

        tool_calls = re.finditer(r"\[Tool Call\]\s*(\w+)\s*(\{.*?\})", response, re.DOTALL)
        assignments = re.finditer(r"\[Assign To\]\s*(\w+)\s*(\{.*?\})", response, re.DOTALL)

        responses = []

        # Process all tool calls
        for match in tool_calls:
            tool_name, raw_args = match.groups()
            try:
                args = json.loads(raw_args)
                result = await self.run_tool(tool_name, args)
                # resend to llm
                messages = (
                    self.memory.get_messages()[-8:]
                    if self.use_memory
                    else [{"role": "user", "content": prompt}]
                ) 
                messages.append({"role": "user", "content": f"[Tool {tool_name} Result] {result} \n--- format the tool result according to the {prompt}"})
                if self.llm :
                    response = await self.llm.chat(messages)
                    if self.use_memory:
                        self.memory.add({"role": "assistant", "content": response})
                        self._maybe_save_memory()
                else:
                    response = "No LLM configured"
                responses.append(f"[Tool {tool_name} Result] {response}")
            except Exception as e:
                responses.append(f"[Tool {tool_name} Error] {e}")

        # Process all agent assignments
        for match in assignments:
            to_agent, raw_args = match.groups()
            try:
                args = json.loads(raw_args)
                result = await self.send_to(self.team[to_agent], args["method"], args["payload"], await_reply=True, role="assistant")
                responses.append(f"[Assign {to_agent} To Result] {result}")
            except Exception as e:
                responses.append(f"[Assign {to_agent} To Error] {e}")

        # Combine final result
        response = "\n".join(responses) if responses else response

        return response

    async def run_tool(self, name: str, args: dict) -> Any:
        # print("run_tool", name, args)
        if name not in self.allowed_tools:
            raise ValueError(f"Tool '{name}' not permitted for this agent")
        route = self.allowed_tools[name]
        mcp = self.mcps.get(route)
        if not mcp:
            raise ValueError(f"MCP route '{route}' not configured for tool '{name}'")
        result = await mcp.call_tool(name, args)
        logging.info(f"[run_tool] {name} result: {result}")
        return result

    async def _handler(self, method: str, payload: Any, state: Dict[str, Any]):
        if method == "ask":
            return await self._ask(payload)

        elif method == "remember":
            if self.use_memory:
                self.memory.add({"role": "user", "content": payload})
                self._maybe_save_memory()

        elif method == "tool":
            name = payload.get("name")
            args = payload.get("payload", {})
            return await self.run_tool(name, args)

        elif method == "fail":
            raise RuntimeError(f"{self.name} failed intentionally")

        elif method == "voice_chat":
            wake_word = payload.get("wake_word")
            exit_word = payload.get("exit_word")
            voice = local_tools.voice_chat_tool(self)
            voice.start_voice(self, wake_word, exit_word)

        else:
            raise ValueError(f"Unknown method: {method}")

    async def on_restart(self, state: Dict[str, Any]):
        state["restart_count"] += 1
        logging.info(f"[{self.name}] 🔁 Restart #{state['restart_count']}")
        
        # Example: reload memory or tools if needed
        if self.use_memory and self.memory:
            self.memory.load()

    async def serve(self, port: int = 8000, routes: Optional[list[str]] = None, auth_secret: str = "supersecret"):
        from fastapi import FastAPI, Request, HTTPException
        from fastapi.responses import JSONResponse
        import uvicorn
        # jwt
        import jwt

        await self.start()

        app = FastAPI()
        routes = set(routes or ["ask", "remember", "tool", "status", "mcp", "tools"])

        def create_jwt(payload: dict):
            return jwt.encode(payload, auth_secret, algorithm="HS256")

        def check_auth(request: Request):
            if auth_secret:
                auth_header = request.headers.get("Authorization")
                
                if not auth_header:
                    raise HTTPException(status_code=401, detail="Unauthorized")
                try:
                    token = auth_header.split(" ")[1]
                    jwt.decode(token, auth_secret, algorithms=["HS256"])
                except jwt.ExpiredSignatureError:
                    raise HTTPException(status_code=401, detail="Token expired")
                except jwt.InvalidTokenError:
                    raise HTTPException(status_code=401, detail="Invalid token") 

        if "ask" in routes:
            @app.post("/ask")
            async def ask_endpoint(request: Request):
                check_auth(request)
                data = await request.json()
                prompt = data.get("prompt")
                if not prompt:
                    raise HTTPException(status_code=400, detail="Missing prompt")
                result = await self.ask(prompt)
                return JSONResponse(content={"response": result})

        if "remember" in routes:
            @app.post("/remember")
            async def remember_endpoint(request: Request):
                check_auth(request)
                data = await request.json()
                await self.remember(data)
                return JSONResponse(content={"status": "ok"})

        if "tool" in routes:
            @app.post("/tool")
            async def tool_endpoint(request: Request):
                check_auth(request)
                data = await request.json()
                name = data.get("name")
                payload = data.get("payload", {})
                result = await self.use_tool(name, payload)
                return JSONResponse(content={"result": result})

        if "status" in routes:
            @app.get("/status")
            async def status_endpoint(request: Request):
                check_auth(request)
                return {"name": self.name, "role": self.role, "goal": self.goal}

        if "mcp" in routes:
            @app.post("/mcp")
            async def add_mcp(request: Request):
                check_auth(request)
                data = await request.json()
                key = data.get("key")
                config = data.get("config")
                if not key or not config:
                    raise HTTPException(status_code=400, detail="Missing key or config")

                self.mcps[key] = MCP.create(config)
                mcp_tools = await self.mcps[key].get_tools()
                for tool in mcp_tools:
                    self.allowed_tools[tool["name"]] = key
                self.system_prompt = await self.build_system_prompt()
                self.llm.system = self.system_prompt
                return {"status": "MCP added", "tools": [t["name"] for t in mcp_tools]}

            @app.get("/mcp")
            async def get_mcp(request: Request):
                check_auth(request)
                return self.mcps

            @app.get("/mcp/{key}")
            async def get_mcp_by_key(request: Request, key: str):
                check_auth(request)
                return self.mcps.get(key)

            @app.delete("/mcp/{key}")
            async def delete_mcp(request: Request, key: str):
                check_auth(request)
                if key in self.mcps:
                    del self.mcps[key]
                    for tool in self.allowed_tools:
                        if self.allowed_tools[tool] == key:
                            del self.allowed_tools[tool]
                self.system_prompt = await self.build_system_prompt()
                self.llm.system = self.system_prompt
                return {"status": "MCP deleted"}

        if "tools" in routes:
            @app.post("/tools")
            async def add_tools(request: Request):
                check_auth(request)
                data = await request.json()
                tools = data.get("tools")
                if not tools or not isinstance(tools, dict):
                    raise HTTPException(status_code=400, detail="Missing or invalid 'tools' dict")

                local = []
                for tool_name, route in tools.items():
                    if route == "local":
                        if not hasattr(local_tools, tool_name):
                            raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' not found in local_tools")
                        local.append(tool_name)
                    self.allowed_tools[tool_name] = route

                if local:
                    self.mcps["local"] = MCP.create({"local": local})
                self.system_prompt = await self.build_system_prompt()
                self.llm.system = self.system_prompt
                return {"status": "Tools added", "tools": list(tools.keys())}

            @app.delete("/tools")
            async def delete_tools(request: Request):
                check_auth(request)
                data = await request.json()
                tools = data.get("tools")
                if not tools or not isinstance(tools, list):
                    raise HTTPException(status_code=400, detail="Missing or invalid 'tools' list")

                for tool_name in tools:
                    if tool_name in self.allowed_tools:
                        del self.allowed_tools[tool_name]
                self.system_prompt = await self.build_system_prompt()
                self.llm.system = self.system_prompt
                return {"status": "Tools deleted", "tools": tools}

            @app.get("/tools")
            async def get_tools(request: Request):
                check_auth(request)
                return self.allowed_tools

            @app.get("/tools/{tool_name}")
            async def get_tool(request: Request, tool_name: str):
                check_auth(request)
                return self.allowed_tools.get(tool_name)
        
        if "ws" in routes:
            @app.websocket("/ws")
            async def ws_endpoint(websocket: WebSocket):
                await websocket.accept()
                while True:
                    data = await websocket.receive_text()
                    await websocket.send_text(f"Future release feature")

        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        print(f"🚀 Agent {self.name} is running at http://localhost:{port}")
        print(f"🔑 JWT Token: {create_jwt({"name": self.name})}")
        await server.serve()


