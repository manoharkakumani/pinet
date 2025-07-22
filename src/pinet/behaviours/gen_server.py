import asyncio
from typing import Any, Callable, Awaitable, Dict, Optional
from .actor import Actor
from .supervisor import Supervisor
import logging

logging.basicConfig(level=logging.INFO)

class GenServer:
    """High-level request/response actor with supervision support and lifecycle hooks."""

    def __init__(
        self,
        name: str,
        handler: Callable[[str, Any, Dict[str, Any]], Awaitable[Any]],
        *,
        supervisor: Optional[Supervisor] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        on_init: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_terminate: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_info: Optional[Callable[[Any, Dict[str, Any]], Awaitable[None]]] = None,
        on_restart: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ):
        self.name = name
        self._handler = handler
        self._state: Dict[str, Any] = initial_state or {}
        self._on_init = on_init
        self._on_terminate = on_terminate
        self._on_info = on_info
        self._on_restart = on_restart
        self._supervisor = supervisor or Supervisor("supervisor")
        self._actor = Actor(name, self._dispatch)
        if supervisor is not None:
            supervisor._register_child(self)


    async def start(self) -> None:
        logging.info(f"[{self.name}] GenServer.start() called")
        if self._on_init:
            await self._on_init(self._state)
        await self._actor.start()

    async def stop(self) -> None:
        logging.info(f"[{self.name}] GenServer.stop() called")
        if self._on_terminate:
            await self._on_terminate(self._state)
        await self._actor.stop()

    async def call(self, method: str, payload: Any) -> Any:
        logging.info(f"[{self.name}] Calling {method}")
        fut = asyncio.get_event_loop().create_future()
        await self._actor.send(("call", method, payload, fut))
        return await fut

    async def cast(self, method: str, payload: Any) -> None:
        logging.info(f"[{self.name}] Casting {method}")
        await self._actor.send(("cast", method, payload, None))

    async def info(self, message: Any) -> None:
        logging.info(f"[{self.name}] Info: {message}")
        await self._actor.send(("info", None, message, None))

    async def fail(self, reason: str) -> None:
        logging.info(f"[{self.name}] Failing: {reason}")
        await self._supervisor._child_failed(self, RuntimeError(reason))


# in pinet/behaviours/gen_server.py
    async def _dispatch(self, _: Actor, msg: Any) -> None:
        kind, method, payload, fut = msg
        logging.info(f"[{self.name}] Dispatching {kind} for {method}")
        try:
            if kind in ("call", "cast"):
                result = await self._handler(method, payload, self._state)
                if fut:
                    fut.set_result(result)
            elif kind == "info" and self._on_info:
                await self._on_info(payload, self._state)

        except Exception as e:
            # 1) if it was a call, immediately return an error instead of hanging
            if fut and not fut.done():
                fut.set_exception(e)

            # 2) notify your supervisor
            if self._supervisor:
                asyncio.create_task(
                    self._supervisor._child_failed(self, e)
                )

            # 3) if this was a cast (no fut), let it bubble up so the actor really crashes
            if kind == "cast":
                raise

