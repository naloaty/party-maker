from __future__ import annotations
from typing import Callable, Coroutine, Optional, TYPE_CHECKING
import asyncio
import inspect
from system.misc.exceptions import IllegalState
from .scene import Scene
from .action_context import ActionContext
from .stage import Stage


if TYPE_CHECKING:
    from .scene_manager import SceneManager


class ActionManager:
    _scene_manager: "SceneManager"

    def __init__(self, manager: "SceneManager"):
        self._scene_manager = manager

    @staticmethod
    def action(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise RuntimeError("The @action decorator can only be applied "
                               "to async functions")

        def wrapper(*args, **kwargs) -> ActionContext:
            if len(args) == 0:
                raise RuntimeError("The @action decorator can only be applied "
                                   "to methods of the class")
            scene: Scene = args[0]
            if not isinstance(scene, Scene):
                raise RuntimeError("The @action decorator can only be applied "
                                   "to methods of the Scene class")
            return ActionContext(scene.context, func, args, kwargs)

        return wrapper

    _current_action: Optional[ActionContext] = None
    _pending_action: Optional[ActionContext] = None
    _manager_task: Optional[asyncio.Task] = None
    _stage: Optional[Stage] = None

    # ===== Internal methods =====

    async def _manager_run_routine(self, routine: Coroutine) -> None:
        self._manager_task = asyncio.create_task(routine)
        await self._manager_task
        self._manager_task = None
        self._manager_done()

    def _manager_run(self, routine: Coroutine) -> None:
        if self._manager_task is not None:
            raise IllegalState("Could not run manager task because there is another")
        asyncio.create_task(self._manager_run_routine(routine))

    async def _wait_current_action(self):
        if self._current_action is None:
            raise IllegalState("Could not wait current action because there is no such")
        await self._current_action.join()
        if self._current_action.stop_reason != Scene.StopReason.LocalIntercept:
            if self._current_action.stop_reason == Scene.StopReason.SceneStop:
                self._current_action.scene.set_state(Scene.State.Stopped)
                self._current_action.scene.scene.on_stop()
            else:
                self._current_action.scene.set_state(Scene.State.Idle)
        self._current_action = None

    def _manager_done(self):
        if self._pending_action is not None:
            self._manager_run(self._execute_action(self._pending_action))
            self._pending_action = None

    # ===== Action methods =====

    async def _execute_action(self, action: ActionContext):
        self._current_action = action
        action.scene.set_state(Scene.State.Playing)
        action.execute(self._scene_manager.get_stage())
        asyncio.create_task(self._wait_current_action())

    async def _interrupt_current_action(self):
        if self._current_action is None:
            return

        reason = Scene.StopReason.SceneStop

        if self._pending_action is not None:
            source = self._current_action.scene.id
            target = self._pending_action.scene.id
            if source == target:
                reason = Scene.StopReason.LocalIntercept
            else:
                self._pending_action.scene.set_state(Scene.State.Preparing)
                self._current_action.scene.set_state(Scene.State.Interrupting)
                reason = Scene.StopReason.ExternalIntercept
        else:
            self._current_action.scene.set_state(Scene.State.Interrupting)
        await self._current_action.interrupt(reason)

    # ===== Public API =====

    def run(self, action: ActionContext):
        if self._current_action is None:
            self._manager_run(self._execute_action(action))
        else:
            self._pending_action = action
            if self._manager_task is None:
                self._manager_run(self._interrupt_current_action())

    async def stop_scene_actions(self, scene_id: int):
        if self._pending_action is not None:
            if self._pending_action.scene.id == scene_id:
                self._pending_action = None

        if self._current_action is not None:
            if self._current_action.scene.id == scene_id:
                self._manager_run(self._interrupt_current_action())