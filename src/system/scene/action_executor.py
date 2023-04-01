from __future__ import annotations

import asyncio
from typing import Coroutine, Optional, TYPE_CHECKING

from system.misc.exceptions import IllegalState
from .action_task import ActionTask
from .scene import Scene
from .stage import Stage

if TYPE_CHECKING:
    from .scene_manager import SceneManager


class ActionExecutor:
    _scene_manager: SceneManager

    def __init__(self, manager: SceneManager):
        self._scene_manager = manager

    _current_action: Optional[ActionTask] = None
    _pending_action: Optional[ActionTask] = None
    _executor_task: Optional[asyncio.Task] = None
    _stage: Optional[Stage] = None

    # ===== Internal methods =====

    async def _executor_run_routine(self, routine: Coroutine) -> None:
        self._executor_task = asyncio.create_task(routine)
        await self._executor_task
        self._executor_task = None
        self._executor_task_done()

    def _executor_run(self, routine: Coroutine) -> None:
        if self._executor_task is not None:
            raise IllegalState("Could not run manager task because there is another")
        asyncio.create_task(self._executor_run_routine(routine))

    async def _wait_current_action(self):
        if self._current_action is None:
            raise IllegalState("Could not wait current action because there is no such")
        await self._current_action.join()
        if self._current_action.stop_reason != Scene.StopReason.LocalIntercept:
            if self._current_action.stop_reason == Scene.StopReason.SceneStop:
                self._current_action.scene_context.set_state(Scene.State.Stopped)
                self._current_action.scene_context.scene.on_stop()
            else:
                self._current_action.scene_context.set_state(Scene.State.Idle)
        self._current_action = None

    def _executor_task_done(self):
        if self._pending_action is not None:
            self._executor_run(self._execute_action(self._pending_action))
            self._pending_action = None

    # ===== Action methods =====

    async def _execute_action(self, action: ActionTask):
        self._current_action = action
        action.scene_context.set_state(Scene.State.Playing)
        action.execute(self._scene_manager.get_stage())
        asyncio.create_task(self._wait_current_action())

    async def _interrupt_current_action(self):
        if self._current_action is None:
            return

        reason = Scene.StopReason.SceneStop

        if self._pending_action is not None:
            source = self._current_action.scene_context.id
            target = self._pending_action.scene_context.id
            if source == target:
                reason = Scene.StopReason.LocalIntercept
            else:
                self._pending_action.scene_context.set_state(Scene.State.Preparing)
                self._current_action.scene_context.set_state(Scene.State.Interrupting)
                reason = Scene.StopReason.ExternalIntercept
        else:
            self._current_action.scene_context.set_state(Scene.State.Interrupting)
        await self._current_action.interrupt(reason)

    # ===== Public API =====

    def execute(self, action: ActionTask):
        if self._current_action is None:
            self._executor_run(self._execute_action(action))
        else:
            self._pending_action = action
            if self._executor_task is None:
                self._executor_run(self._interrupt_current_action())

    async def stop_scene_actions(self, scene_id: int):
        if self._pending_action is not None:
            if self._pending_action.scene_context.id == scene_id:
                self._pending_action = None

        if self._current_action is not None:
            if self._current_action.scene_context.id == scene_id:
                self._executor_run(self._interrupt_current_action())
