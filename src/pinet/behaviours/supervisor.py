import asyncio
from enum import Enum, auto
from typing import Dict, Any, Optional, Callable, Awaitable

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RestartStrategy(Enum):
    ONE_FOR_ONE = auto()
    ONE_FOR_ALL  = auto()
    REST_FOR_ONE = auto()

class Supervisor:
    def __init__(
        self,
        name: str,
        *,
        strategy: RestartStrategy = RestartStrategy.ONE_FOR_ONE,
        max_restarts: int = 3,
        backoff_base: float = 0.5,
        notify_failure: Optional[Callable[[str, Exception], Awaitable[None]]] = None,
    ):
        self.name = name
        self.strategy = strategy
        self.max_restarts = max_restarts
        self.backoff_base = backoff_base
        self.notify_failure = notify_failure

        self._children: Dict[str, Any] = {}
        self._restart_counts: Dict[str, int] = {}
        self._restarting = set()

    def _register_child(self, genserver: Any) -> None:
        self._children[genserver.name] = genserver

    async def _child_failed(self, genserver: Any, exc: Exception) -> None:
        logger.warning(f"[{self.name}] Handling failure of {genserver.name}: {exc}")
        if genserver.name in self._restarting:
            return

        count = self._restart_counts.get(genserver.name, 0)
        if count >= self.max_restarts:
            logger.error(f"[{self.name}] Max restarts reached for {genserver.name}. Not restarting.")
            if self.notify_failure:
                await self.notify_failure(genserver.name, exc)
            return

        self._restart_counts[genserver.name] = count + 1
        self._restarting.add(genserver.name)

        backoff = self.backoff_base * (2 ** count)
        logger.info(f"[{self.name}] Backing off {backoff:.2f}s before restarting {genserver.name}")
        await asyncio.sleep(backoff)

        try:
            if self.strategy is RestartStrategy.ONE_FOR_ONE:
                await self._restart(genserver)
            elif self.strategy is RestartStrategy.ONE_FOR_ALL:
                for gs in list(self._children.values()):
                    await self._restart(gs)
            elif self.strategy is RestartStrategy.REST_FOR_ONE:
                names = list(self._children)
                idx = names.index(genserver.name)
                for name in names[idx:]:
                    await self._restart(self._children[name])
        finally:
            self._restarting.remove(genserver.name)


    async def _restart(self, gs: Any) -> None:
        logger.info(f"[{self.name}] 🔁 Restarting {gs.name}")
        await gs.stop()
        if hasattr(gs, "_on_restart") and gs._on_restart:
            await gs._on_restart(gs._state)
        await gs.start()

    async def start_all(self) -> None:
        logger.info(f"[{self.name}] Starting all children")
        for gs in list(self._children.values()):
            logger.info(f"[{self.name}] Starting {gs.name}")
            await gs.start()

    async def stop_all(self) -> None:
        for gs in list(self._children.values()):
            logger.info(f"[{self.name}] Stopping {gs.name}")
            await gs.stop()
