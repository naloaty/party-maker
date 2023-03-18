from __future__ import annotations
from typing import Callable, Coroutine, Optional, TYPE_CHECKING
import asyncio
from .scene import Scene

if TYPE_CHECKING:
    from .scene_context import SceneContext
    from .stage import Stage


class ActionContext:
    Callback = Callable[[Scene.StopReason], Coroutine]

    scene: "SceneContext"
    func: Callable
    args: tuple
    kwargs: dict
    callback: Optional[Callback] = None
    task: Optional[asyncio.Task] = None
    stop_reason: Optional[Scene.StopReason] = None
    _lock: Optional[asyncio.Semaphore] = None
    _stage: Optional[Stage] = None

    def __init__(self, scene: "SceneContext", func: Callable, args: tuple, kwargs: dict):
        self.scene = scene
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._lock = asyncio.Semaphore(0)

    async def _wait_return(self):
        if self.task is None:
            return
        await self.task
        if not self.task.cancelled():
            self.stop_reason = Scene.StopReason.Return
            if self.callback is not None:
                await self.callback(self.stop_reason)
            self._stage.invalidate()
            self._lock.release()

    # ===== Public api =====

    def execute(self, stage: Stage) -> bool:
        if self.task is None:
            self._stage = stage
            self.scene.set_stage(stage)
            self.task = asyncio.create_task(self.func(*self.args, **self.kwargs))
            asyncio.create_task(self._wait_return())
            return True
        else:
            return False

    async def interrupt(self, reason: Scene.StopReason):
        if self.task is None:
            return
        self.task.cancel()
        while not self.task.done():
            await asyncio.sleep(0.1)
        if self.task.cancelled():
            self.stop_reason = reason
            if self.callback is not None:
                await self.callback(self.stop_reason)
            self._stage.invalidate()
            self._lock.release()

    async def join(self):
        await self._lock.acquire()
