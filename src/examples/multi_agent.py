import asyncio
from pinet import Agent, Supervisor, RestartStrategy

# Update with your real keys
ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
BRAVE_API_KEY = "BRAVE_API_KEY"

async def create_worker(name: str, supervisor: Supervisor) -> Agent:
    mcp_config = {
        "command": "npx -y @modelcontextprotocol/server-brave-search",
        "env": {"BRAVE_API_KEY": BRAVE_API_KEY}
    }

    return await Agent.create(
        name=name,
        llm_config={"provider": "anthropic", "api_key": ANTHROPIC_API_KEY},
        mcp_config=mcp_config,
        supervisor=supervisor,
    )

async def main():

    supervisor = Supervisor("supervisor", strategy=RestartStrategy.ONE_FOR_ALL)
    manager = await Agent.create(
        name="manager",
        llm_config={"provider": "anthropic", "api_key": ANTHROPIC_API_KEY},
        supervisor=supervisor,
    )
    worker1 = await create_worker("worker1", supervisor=supervisor)
    worker2 = await create_worker("worker2", supervisor=supervisor)

    # Start all agents
    # 🚀 Start all agents via supervisor
    await supervisor.start_all()

    print("\n📤 Assigning tasks...\n")
    await manager.send_to(worker1, "perform_task", {
        "type": "search",
        "query": "AI in healthcare 2025"
    })
    await manager.send_to(worker2, "perform_task", {
        "type": "search",
        "query": "AI in education 2025"
    })

    await asyncio.sleep(5)

    # 🔍 Ask again after restart
    print("\n📥 Manager asking for results...\n")
    answer1 = await worker1.ask("What did you find?")
    print("\n📄 Worker 1:\n", answer1)

      # 🧨 Simulate a crash in worker2
    print("\n💥 Simulating crash in worker2...\n")
    try:
        await worker2.server.call("fail", None)
    except Exception as e:
        print(f"[Expected crash] {e}")

    # ⏳ Wait for supervisor to restart it
    await asyncio.sleep(2)
    answer2 = await worker2.ask("What did you find after restart?")
    print("\n📄 Worker 2:\n", answer2)

    # 🛑 Shutdown
    await supervisor.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
