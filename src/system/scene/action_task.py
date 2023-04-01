from __future__ import annotations
from typing import Callable, Coroutine, Optional, TYPE_CHECKING, Final
import asyncio
from .scene import Scene

if TYPE_CHECKING:
    from .scene_context import SceneContext
    from .stage import Stage


class ActionTask:
    Callback = Callable[[Scene, Scene.StopReason], Coroutine]

    func: Final[Callable]
    args: Final[tuple]
    kwargs: Final[dict]

    scene_context: Final[SceneContext]
    on_stop: Optional[Callback] = None
    stop_reason: Optional[Scene.StopReason] = None

    _task: Optional[asyncio.Task] = None
    _lock: Final[asyncio.Semaphore] = None
    _stage: Optional[Stage] = None

    def __init__(self, scene_context: SceneContext, func: Callable, args: tuple, kwargs: dict):
        self.scene_context = scene_context
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._lock = asyncio.Semaphore(0)

    async def _wait_return(self):
        if self._task is None:
            return
        await self._task
        if not self._task.cancelled():
            self.stop_reason = Scene.StopReason.Return
            if self.on_stop is not None:
                await self.on_stop(self.scene_context.scene, self.stop_reason)
            self._stage.invalidate()
            self._lock.release()

    # ===== Public api =====

    def execute(self, stage: Stage) -> bool:
        if self._task is None:
            self._stage = stage
            self.scene_context.set_stage(stage)
            self._task = asyncio.create_task(self.func(*self.args, **self.kwargs))
            asyncio.create_task(self._wait_return())
            return True
        else:
            return False

    async def interrupt(self, reason: Scene.StopReason):
        if self._task is None:
            return
        self._task.cancel()
        while not self._task.done():
            await asyncio.sleep(0.1)
        if self._task.cancelled():
            self.stop_reason = reason
            if self.on_stop is not None:
                await self.on_stop(self.scene_context.scene, self.stop_reason)
            self._stage.invalidate()
            self._lock.release()

    async def join(self):
        await self._lock.acquire()
