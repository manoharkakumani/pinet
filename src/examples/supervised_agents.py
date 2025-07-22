# examples/supervised_agents.py

import asyncio
from pinet import Agent, Supervisor, RestartStrategy

async def main():
    root_sup = Supervisor("root_sup")
    worker_sup = Supervisor("worker_sup", strategy=RestartStrategy.ONE_FOR_ONE)

    planner = await Agent.create("planner", 
                                 description="A helpful assistant",
                                 goal="To answer questions and help users",
                                 role="Assistant",
                                 llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                 supervisor=root_sup)
    worker_1 = await Agent.create("worker_1", 
                                  description="A helpful assistant",
                                  goal="To answer questions and help users",
                                  role="Assistant",
                                  llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                  supervisor=worker_sup)
    worker_2 = await Agent.create("worker_2", 
                                  description="A helpful assistant",
                                  goal="To answer questions and help users",
                                  role="Assistant",
                                  llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                  supervisor=worker_sup)
    summarizer = await Agent.create("summarizer", 
                                   description="A helpful assistant",
                                   goal="To answer questions and help users",
                                   role="Assistant",
                                   llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                   supervisor=worker_sup)

    await root_sup.start_all()
    await worker_sup.start_all()

    await planner.send_to(worker_1, "remember", "Task: Analyze sales data")
    await worker_1.send_to(worker_2, "remember", "Use math tool on Q2 numbers")
    await worker_2.send_to(summarizer, "remember", "Summary: 12% increase over Q1")

    print("[Before failure]", await summarizer.ask("Report status?"))

    print("\n>>> Simulating crash")
    try:
        await worker_1.server.call("fail", None)
    except Exception as e:
        print("[Recovery] Caught failure:", e)

    await asyncio.sleep(0.2)

    await summarizer.send_to(summarizer, "remember", "System recovered successfully")
    print("[After recovery]", await summarizer.ask("Final summary?"))

    await root_sup.stop_all()
    await worker_sup.stop_all()

if __name__ == "__main__":
    asyncio.run(main())