import yaml
import asyncio
import logging

from pinet import Supervisor, RestartStrategy, Agent, TaskFlow, Task
from pinet.knowledge import load_knowledge
from typing import Dict, Any




logging.basicConfig(level=logging.INFO)

STRATEGY_MAP = {
    "one_for_all": RestartStrategy.ONE_FOR_ALL,
    "one_for_one": RestartStrategy.ONE_FOR_ONE,
    "rest_for_one": RestartStrategy.REST_FOR_ONE,
}

async def run_playbook(path):
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    topic = config.get("topic", "general")
    roles = config.get("agents", {})
    supervisor_defs = config.get("supervisors", {})
    mcp_defs = config.get("mcps", {})
    llm_defs = config.get("llms", {})
    taskflows_defs = config.get("taskflows", {})

    # Default supervisor
    supervisors = {
        "default": Supervisor(name="default", strategy=RestartStrategy.ONE_FOR_ONE)
    }

    for name, sup in supervisor_defs.items():
        strategy = STRATEGY_MAP.get(sup.get("strategy", "one_for_one"), RestartStrategy.ONE_FOR_ONE)
        supervisors[name] = Supervisor(name=name, strategy=strategy)

    agents = {}
    for name, role in roles.items():
        agent_id = role.get("agent", name)
        desc = role.get("description", f"{name} working on {topic}")
        goal = role.get("goal", "")
        tools = role.get("tools", {})
        sup = supervisors.get(role.get("supervisor", "default"))
        memory = role.get("memory", {"enabled": True, "memory": {"type": "json"}})

        # LLM config
        llm_key = role.get("llm")
        llm_config = llm_defs.get(llm_key) if isinstance(llm_key, str) else llm_key

        # MCP routes (one or many)
        mcp_config = {}
        mcp_routes = role.get("mcp", [])
        if isinstance(mcp_routes, list):
            for route in mcp_routes:
                if route in mcp_defs:
                    mcp_config[route] = mcp_defs[route]
        elif isinstance(mcp_routes, str) and mcp_routes in mcp_defs:
            mcp_config = {mcp_routes: mcp_defs[mcp_routes]}
        elif "default" in mcp_defs:
            mcp_config = {"default": mcp_defs["default"]}

        # Slaves
        team = role.get("team", [])
        team_agents = []
        if isinstance(team, list):
            for member in team:
                if member in agents:
                    team_agents.append(agents[member][0])

        # Create the agent
        agent:Agent = await Agent.create(
            name=agent_id,
            description=desc,
            goal=goal,
            role=role.get("role", "assistant"),
            llm_config=llm_config,
            memory=memory,
            supervisor=sup,
            mcp_config=mcp_config,
            tools=tools,
            team=team_agents,
        )
        
        agents[agent_id] = (agent, role)

    # Load knowledge
    for agent_id, (agent, role) in agents.items():
        for item in role.get("knowledge", []):
            try:
                content = load_knowledge(item)
                await agent.remember(f"[Knowledge from {item}]{content}")
            except Exception as e:
                logging.warning(f"Failed to load knowledge from {item} for {agent.name}: {e}")

    # Execute tasks
    async def run_tasks(agent: Agent, role: Dict[str, Any]):
        results = []
        for task_id, task in role.get("tasks", {}).items():
            try:
                print(f"\n📤 [{agent.name}] Task: {task_id}")
                response = None

                if "ask" in task:
                    prompt = task["ask"].format(topic=topic)
                    response = await agent.ask(prompt)

                elif "remember" in task:
                    note = task["remember"].format(topic=topic)
                    await agent.remember(note)
                    response = "ok"
                
                elif "tool" in task:
                    tool_name = task["tool"]
                    args = task.get("payload", {})
                    response = await agent.use_tool(tool_name, args)

                elif "send" in task:
                    send = task["send"]
                    target = agents.get(send["to"])
                    if not target:
                         raise ValueError(f"Target agent {send['to']} not found")
                    response = await agent.send_to(target[0], send["type"], send["payload"])

                results.append((task_id, response))
            except Exception as e:
                results.append((task_id, f"[Error] {e}"))

        return agent.name, results

   #task flow

    taskflows = {}

    for taskflow_name, taskflow_def in taskflows_defs.items():
        supervisor = supervisors.get(taskflow_def.get("supervisor", "default"))
        tasks = []
        for task_name, task_def in taskflow_def.items():
            agent_id = task_def["agent"]
            description = task_def.get("description", "").format(topic=topic)
            result = task_def.get("result", "").format(topic=topic)
            next_tasks = task_def.get("next_tasks", {})
            reuse = task_def.get("reuse", False)
            type = task_def.get("type", "ask")
            task = Task(
                name=task_name,
                description=description,
                result=result,
                agent=agents[agent_id][0],
                next_tasks=next_tasks,
                reuse=reuse,
                task_type=type,
                status="pending"
            )
            tasks.append(task)
        taskflow = TaskFlow(name=taskflow_name, tasks=tasks, supervisor=supervisor)
        taskflows[taskflow_name] = taskflow

        # Start all supervisors
    for sup in supervisors.values():
        await sup.start_all()

    if taskflows:
        all_taskflows = [taskflow.run_all() for taskflow in taskflows.values()]
        all_results = await asyncio.gather(*all_taskflows)
        for flow_result in all_results:
            for flow_name, results in flow_result.items():
                if results:
                    print(f"\n✅ Results from [{flow_name}]:")
                    for task_id, result in results:
                        print(f"🧾 {task_id}: {result}")

    else:
        all_tasks = [run_tasks(agent, role) for (agent, role) in agents.values()]
        all_results = await asyncio.gather(*all_tasks)
        for agent_name, results in all_results:
            print(f"\n✅ Results from [{agent_name}]:") if results else ""
            for task_id, output in results:
                print(f"🧾 {task_id}: {output}")

    await asyncio.gather(*[sup.stop_all() for sup in supervisors.values()])
