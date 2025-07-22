import argparse
from pinet.agent import Agent
import asyncio
from pinet.playbook import run_playbook
import logging
import os

# disable logging
# logging.disable(logging.INFO)

api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")
provider = os.getenv("LLM_PROVIDER")

async def main():
    parser = argparse.ArgumentParser(description="Pinet AI CLI")
    parser.add_argument("--auto", type=str, help="Auto-run agent with a single prompt")
    parser.add_argument("--yaml", type=str, help="Run agents from a YAML playbook")

    args = parser.parse_args()

    if args.auto:
        llm_config = {
            "provider":  provider,
            "api_key": api_key,
            "model": model
        }
        agent = await Agent.create(name="AutoAgent", description="You are a helpful AI assistant", llm_config=llm_config, tools="__all__")
        await agent.start()
        response = await agent.ask(args.auto)
        print("\n🧠 Response:\n", response)
    elif args.yaml:
        await run_playbook(args.yaml)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
