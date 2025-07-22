from __future__ import annotations
import asyncio
from typing import Any, Awaitable, Callable, Optional

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Actor:
    """Lightweight co‑operative process with a private mailbox."""

    def __init__(self, name: str, handler: Callable[["Actor", Any], Awaitable[None]], *, supervisor: Optional["Supervisor"] = None):
        self.name = name
        self._mailbox: asyncio.Queue[Any] = asyncio.Queue()
        self._handler = handler
        self._task: Optional[asyncio.Task[None]] = None
        self._supervisor = supervisor

    async def start(self) -> None:
        logger.info(f"[{self.name}] Actor.start() called")
        if self._task and not self._task.done():
            raise RuntimeError(f"Actor {self.name} already running")
        self._task = asyncio.create_task(self._run(), name=self.name)
        logger.info(f"[{self.name}] Actor task created")
        if self._supervisor:
            self._supervisor._register_child(self)

    
    def on_restart(self):
        logger.info(f"[{self.name}] 🔁 Restarted")
        pass

    async def send(self, msg: Any) -> None:
        logger.info(f"[{self.name}] Sending message: {msg}")
        await self._mailbox.put(msg)

    async def stop(self) -> None:
        logger.info(f"[{self.name}] Stopping...")
        if self._task:
            task = self._task
            self._task = None  # prevent recursion
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[{self.name}] Exception during stop: {e}")

    async def _run(self) -> None:
        logger.info(f"[{self.name}] 🔁 Actor loop started")
        while True:
            msg = await self._mailbox.get()
            logger.info(f"[{self.name}] ↪️ Dispatching message: {msg}")
            await self._handler(self, msg)




