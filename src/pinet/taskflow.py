from typing import List, Optional, Dict
from pinet.task import Task
from pinet.behaviours.gen_server import GenServer
from pinet.behaviours.supervisor import Supervisor
import logging

logging.basicConfig(level=logging.INFO)


class TaskFlow:
    def __init__(
        self,
        name: str = "TaskFlow",
        supervisor: Optional[Supervisor] = None,
        tasks: Optional[List[Task]] = None
    ): 
        self.name = name
        self.tasks: List[Task] = tasks or []
        self.task_map: Dict[str, Task] = {t.name: t for t in self.tasks}
        self.server = GenServer(
            name=name,
            handler=self._handler,
            initial_state={"pointer": 0},
            supervisor=supervisor,
            on_restart=self._on_restart,
        )

    def add_task(self, task: Task):
        self.tasks.append(task)
        self.task_map[task.name] = task

    def add_tasks(self, task_list: List[Task]):
        for task in task_list:
            self.add_task(task)

    def get_task(self, name: str) -> Optional[Task]:
        return self.task_map.get(name)

    def remove_task(self, name: str):
        if name in self.task_map:
            del self.task_map[name]
            self.tasks = [t for t in self.tasks if t.name != name]

    def clear_tasks(self):
        self.tasks.clear()
        self.task_map.clear()

    async def _run_from_entry(self, entry_task: Task, visited: set):
        current_task = entry_task

        while current_task:
            if current_task.name in visited and not current_task.reuse:
                logging.info(f"🔁 Task {current_task.name} already executed. Skipping.")
                break
            visited.add(current_task.name)

            if current_task.reuse:
                current_task.reset()

            logging.info(f"▶️ Running: {current_task.name} (Agent: {current_task.agent.name})")
            await current_task.run()
            logging.info(f"{'✅' if current_task.status == 'done' else '❌'} {current_task.name} → {current_task.result}")

            outcome_key = current_task.outcome or (current_task.result or "").strip().lower()
            next_ref = current_task.next_tasks.get(outcome_key)

            if current_task.status != "done":
                logging.info(f"💥 Task {current_task.name} failed — triggering restart.")
                state["failed_task"] = current_task.name
                await self.server.fail(reason=f"{current_task.name} failed")
                return

            if not next_ref:
                logging.info("⚠️ No matching next task. Flow branch ends.")
                break

            if isinstance(next_ref, str):
                next_task = self.get_task(next_ref)
                if not next_task:
                    logging.info(f"⚠️ Task '{next_ref}' not found.")
                    break
            else:
                next_task = next_ref

            current_task = next_task

    async def run_all(self):
        logging.info(f"🚀 Running full workflow `{self.name}` across all branches")
        visited = set()

        # Step 1: Run from default entry point
        entry_task = self.tasks[0] if self.tasks else None
        if entry_task:
            await self._run_from_entry(entry_task, visited)

        # Step 2: Identify and run orphan/unlinked tasks
        referenced = set()
        for task in self.tasks:
            for target in task.next_tasks.values():
                if isinstance(target, str):
                    referenced.add(target)
                elif isinstance(target, Task):
                    referenced.add(target.name)

        unlinked = [
            t for t in self.tasks
            if t.name not in referenced and t.name not in visited
        ]

        for task in unlinked:
            logging.info(f"🧭 Found unlinked task: {task.name}. Running it.")
            await self._run_from_entry(task, visited)

        # return results
        logging.info(f"🏁 Workflow `{self.name}` complete.\n")
        return {self.name: [(t.name, t.result) for t in self.tasks]}



    async def _on_restart(self, state):
        failed_name = state.get("failed_task")
        if not failed_name:
            logging.info(f"🔄 Workflow `{self.name}` restarted — but no failed task found.")
            return

        failed_task = self.get_task(failed_name)
        if not failed_task:
            logging.info(f"⚠️ Failed task '{failed_name}' not found in task map.")
            return

        logging.info(f"🔁 Restarting failed task: {failed_name}")
        failed_task.reset()
        await self._run_from_entry(failed_task, visited=set())


    async def start(self):
        await self.server.start()
        await self.run_all()
        await self.server.stop()

    async def cast(self, method, payload=None):
        return await self.server.cast(method, payload)

    async def call(self, method, payload=None):
        return await self.server.call(method, payload)

    async def _handler(self, method: str, payload: dict, state: dict):
        if method == "status":
            return self.summary()
        elif method == "add_task":
            self.add_task(payload)
        elif method == "get_task":
            return self.get_task(payload)
        elif method == "remove_task":
            self.remove_task(payload)
        elif method == "clear_tasks":
            self.clear_tasks()
        else:
            raise ValueError(f"Unknown method: {method}")

    def summary(self):
        return [task.summary() for task in self.tasks]
