from typing import Optional, Any, Callable, Union, Dict
from pinet.agent import Agent
import re


class Task:
    def __init__(
        self,
        name: str,
        description: str,
        result: Union[str, dict],
        agent: Agent,
        task_type: str = "ask",
        next_tasks: Optional[Dict[str, Union[str, "Task"]]] = None,
        callback: Optional[Callable[[Any], Any]] = None,
        status: str = "pending",
        reuse: bool = False
    ):
        self.name = name
        self.description = description
        self.end_result = result
        self.agent = agent
        self.task_type = task_type
        self.callback = callback
        self.status = status
        self.reuse = reuse
        self.result = None
        self.error = None
        self.outcome = None
        self.next_tasks: Dict[str, Union[str, "Task"]] = next_tasks or {}

    def reset(self):
        self.status = "pending"
        self.result = None
        self.error = None
        self.outcome = None

    def add_next(self, outcome: str, task: Union[str, "Task"]):
        self.next_tasks[outcome.lower()] = task

    def _extract_outcome(self, response: str) -> Optional[str]:
        match = re.search(r"\[Outcome\]\s*(\w+)", response, re.IGNORECASE)
        return match.group(1).lower() if match else None

    async def run(self) -> Any:
        self.status = "running"
        try:
            if isinstance(self.end_result, dict):
                method = self.end_result.get("method", self.task_type)
                description = self.end_result.get("description", "")
                payload = self.end_result.get("payload", {})
            else:
                method = self.task_type
                description = self.description

            payload= (f"""
---
Task Name: {self.name}
Your goal is to {description}
Expected output: {self.end_result}
---
## Task Outcome Routing
If your response is intended to trigger a next step, include one of:
[Outcome] more  
[Outcome] done  
Respond naturally, but include the [Outcome] tag at the end of your message.
---
"""             )
            if method == "ask":
                self.result = await self.agent.ask(payload)
            elif method == "remember":
                self.result = await self.agent.remember(description)
            elif method == "tool":
                if not isinstance(payload, dict) or "name" not in payload or "args" not in payload:
                    raise ValueError("Tool payload must include 'name' and 'args'")
                self.result = await self.agent.use_tool(payload["name"], payload["args"])
            else:
                raise ValueError(f"Unknown task method: {method}")

            self.outcome = self._extract_outcome(self.result or "")
            self.status = "done"
            if self.callback:
                self.callback(self.result)
            return self.result

        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            return f"[Task {self.name} Error] {e}"

    def summary(self):
        return {
            "name": self.name,
            "status": self.status,
            "agent": self.agent.name,
            "result": self.result,
            "outcome": self.outcome,
            "error": self.error,
        }

    def __repr__(self):
        return f"<Task name={self.name}, status={self.status}, agent={self.agent.name}>"
