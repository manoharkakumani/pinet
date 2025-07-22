from pinet import Agent, Supervisor, Task, TaskFlow, RestartStrategy
from typing import Optional


class PinetAI:
    def __init__(self, agents: Optional[list[Agent]] = None, tasks: Optional[list[Task]] = None):
        self.agents = agents
        self.taskflow = None
        if tasks:
            taskflow_supervisor = Supervisor("taskflow_supervisor", strategy=RestartStrategy.ONE_FOR_ONE)
            self.taskflow = TaskFlow(
                name="taskflow",
                supervisor=taskflow_supervisor,
                tasks=tasks
            )

    async def start(self, entry_task: Optional[Task] = None):
        for agent in self.agents:
            await agent.start()
        print("Agents started")
        if self.taskflow:
            print("Taskflow started")
            await self.taskflow.start()
        await self.stop()
        

    async def stop(self):
        for agent in self.agents:
            await agent.stop()

    
        