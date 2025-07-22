import asyncio
from typing import Any, Optional
from .io import VoiceIO


class Voice:
    def __init__(
        self,
        agent: Any,
        wake_word: Optional[str] = None,
        transcriber: Optional[Any] = None,
    ):
        self.agent = agent
        self.wake_word = wake_word
        self._stop_event = asyncio.Event()
        self._task = None
        self.transcriber = transcriber
        self._running_flag = {"status": False}

    @classmethod
    def create(cls, agent, **kwargs):
        wake_word = kwargs.pop("wake_word", None)
        transcriber_type = kwargs.pop("transcriber_type", "faster")
        whisper_model = kwargs.pop("whisper_model", "base")
        device = kwargs.pop("device", "cpu")

        # Define instance-level running state
        running_flag = {"status": True}

        def check_status():
            return running_flag["status"]

        transcriber = VoiceIO(
            transcriber_type=transcriber_type,
            whisper_model=whisper_model,
            device=device,
            is_running=check_status,
        )

        instance = cls(agent=agent, wake_word=wake_word, transcriber=transcriber)
        instance._running_flag = running_flag  # store flag for stopping
        return instance

    async def start(self):
        if self._task and not self._task.done():
            return
        print("🔊 Voice interface started. Speak to your agent.")
        self._stop_event.clear()
        self._running_flag["status"] = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        print("🛑 Stopping voice interface...")
        self._running_flag["status"] = False
        self._stop_event.set()
        if self._task:
            await self._task

    async def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                user_input = await self.transcriber.listen_async()
                if not user_input.strip():
                    continue  # 🔇 skip silence or empty input

                if self.wake_word and self.wake_word.lower() not in user_input.lower():
                    continue  # 🚫 skip if wake word not present

                print(f"🎤 User: {user_input}")
                response = await self.agent.ask(user_input)
                if response and response.strip():
                    print(f"🤖 Agent: {response}")
                    await self.transcriber.speak_async(response)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Voice interface error: {e}")
