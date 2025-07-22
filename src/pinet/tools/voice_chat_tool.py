import logging
from typing import Optional
from pinet.voice.io import VoiceIO

from pinet import Agent, Supervisor, RestartStrategy


class VoiceTools:
    def __init__(self):
        self._running = False

    async def start_voice(
        self,
        exit_word: Optional[str] = "exit",
        transcriber_type: str = "faster",
        whisper_model: str = "base",
        device: str = "cpu"
    ) -> str:
       
        if self._running:
            return "Already running"

        agent =  await Agent.create(
            name="voice_agent",
            llm_config={
                "provider": os.getenv("LLM_PROVIDER"),
                "model": os.getenv("LLM_MODEL"),
                "api_key": os.getenv("LLM_API_KEY")
            },
            supervisor=Supervisor(
                name="voice_agent_supervisor",
                strategy=RestartStrategy.ONE_FOR_ONE,
            ),
            description="You are a voice agent",
            goal="be a voice agent",
            role="voice_agent",
            memory={
                "enabled": True,
                "memory": {"type": "json"}
            },
        )

        self._running = True

        await agent.start()

        logging.info("Voice session started")

        voice_io = VoiceIO(
            transcriber_type=transcriber_type,
            whisper_model=whisper_model,
            device=device,
            is_running=lambda: self._running
        )

        while self._running:
            user_input = await voice_io.listen_async()
            user_input = user_input.strip()
            if not user_input or not any(c.isalnum() for c in user_input):
                print("Skipping empty or non-verbal input...")
                continue
            if exit_word and user_input.lower() == exit_word.lower():
                break
            # make the llm chat output minimal
            # user_input = f"You are a helpful assistant. named as {main_agent.name}. try to respond in minimal words and sentences as possible for input. input: {user_input}"
            print(f"🎤 User: {user_input}")
            response = await agent.ask(user_input)
            # response = ""
            print(f"🤖 Agent: {response}")
            await voice_io.speak_async(response)

        await agent.stop()
        self._running = False
        return "Voice session ended"


# Tool exports
_voice_tools = VoiceTools()
start_voice = _voice_tools.start_voice
