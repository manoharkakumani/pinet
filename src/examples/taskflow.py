from pinet import Agent, Supervisor, RestartStrategy, Task, PinetAI
import asyncio

import logging
logging.disable(level=logging.INFO)

llm_config = {
    "provider": "anthropic",
    "api_key": "ANTHROPIC_API_KEY"
}

mcp_config = {
    "command": "npx -y @modelcontextprotocol/server-brave-search",
    "env": {"BRAVE_API_KEY": "BRAVE_API_KEY"}
}

supervisor = Supervisor("supervisor", strategy=RestartStrategy.ONE_FOR_ONE)

async def main():

    agent = await Agent.create(name="agent",
                               description="A helpful assistant",
                               goal="To answer questions and help users",
                               role="Assistant",
                               llm_config=llm_config,
                               mcp_config=mcp_config,
                               supervisor=supervisor,
                            )
    task1 = Task(name="task1", 
                 description="Search for AI in healthcare 2025", 
                 result="list of 5 articles", 
                 agent=agent,
                 next_tasks={
                     "more": "task1",
                     "done": "task2"
                 }
    )

    task2 = Task(name="task2", 
                 description="Search for AI in education 2025", 
                 result="list of 5 articles", 
                 agent=agent,
    )

    task3 = Task(name="task3", 
                 description="write a report on the articles", 
                 result="report", 
                 agent=agent,
    )

    pinet_ai = PinetAI([agent], [task1, task2, task3])
    await pinet_ai.start()
    


if __name__ == "__main__":
    asyncio.run(main())