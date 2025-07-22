# examples/supervised_agents.py

import asyncio
from pinet import Agent, Supervisor, RestartStrategy

async def main():
    root_sup   = Supervisor("root_sup")
    worker_sup = Supervisor("worker_sup", strategy=RestartStrategy.ONE_FOR_ONE)

    # pass in supervisors but DON'T start individual agents:
    planner    = await Agent.create( name="planner",    
                                     description="A helpful assistant",
                                     goal="To answer questions and help users",
                                     role="Assistant",
                                     llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                     supervisor=root_sup)
    worker_1   = await Agent.create( name="worker_1",   
                                     description="A helpful assistant",
                                     goal="To answer questions and help users",
                                     role="Assistant",
                                     llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                     supervisor=worker_sup)
    worker_2   = await Agent.create( name="worker_2",   
                                     description="A helpful assistant",
                                     goal="To answer questions and help users",
                                     role="Assistant",
                                     llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                     supervisor=worker_sup)
    summarizer = await Agent.create( name="summarizer", 
                                     description="A helpful assistant",
                                     goal="To answer questions and help users",
                                     role="Assistant",
                                     llm_config={"provider": "anthropic", "api_key": "ANTHROPIC_API_KEY"},
                                     supervisor=worker_sup)

    # Now spin them all up from the top:
    await root_sup.start_all()
    await worker_sup.start_all()

    # …do your calls…
    await planner.send_to(worker_1, "remember", "Task: Analyze sales data")
    await planner.send_to(worker_2, "remember", "Task: Analyze marketing data")
    # etc.

    await worker_1.server.call("fail", None)


    # give it a moment to auto-restart…
    await asyncio.sleep(0.1)

    # verify memory was restored…
    print(await summarizer.ask("Final summary?"))

    # tear it all down…
    await worker_sup.stop_all()
    await root_sup.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
