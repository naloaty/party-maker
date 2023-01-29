import asyncio
import inspect
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Type, List, Optional, Coroutine

from PyQt6.QtCore import pyqtSignal, QObject

from settings import bulb_settings
from system.display import MediaDisplay
from system.exceptions import IllegalState
from system.lighting import Lighting


class Resource:
    __invalid: bool = False

    def __getattribute__(self, name: str):
        if "invalid" in name:
            return super().__getattribute__(name)
        if self.__invalid:
            raise RuntimeError("Could not access resource outside of @action scope")
        else:
            return super().__getattribute__(name)

    def invalidate(self):
        attrs = [a for a in dir(self) if not a.startswith('__')]
        for attr_name in attrs:
            setattr(self, attr_name, None)
        self.__invalid = True

    def invalid(self) -> bool:
        return self.__invalid


@dataclass
class Stage(Resource):
    display: MediaDisplay
    lighting: Lighting


class Scene:
    class StopReason(Enum):
        Return = 0
        LocalIntercept = 1
        ExternalIntercept = 2
        SceneStop = 3

    class State(str, Enum):
        Stopped = "Остановлена"
        Idle = "Ожидание"
        Playing = "Действие"
        Interrupting = "Прерывание"
        Preparing = "Подготовка"

        def __str__(self):
            return self.value

    @dataclass
    class Description:
        id: int
        name: str
        state: "Scene.State"

    NAME: str = "Unnamed Scene"
    context: Optional["SceneContext"] = None

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def stop(self):
        if self.context is None:
            raise IllegalState("Could stop scene because Context is None")
        self.context.manager.stop_scene(self.context.id)

    def set_context(self, api: "SceneContext"):
        self.context = api

    def run_action(self, action: "ActionContext", callback: Optional["ActionContext.Callback"]):
        if self.context is None:
            raise IllegalState("Could not run action because Context is None")
        action.callback = callback
        self.context.manager.run_action(action)


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


@dataclass
class SceneContext:
    id: int
    state: Scene.State
    scene: Scene
    manager: "SceneManager"
    _stage: Optional[Stage] = None

    def get_description(self) -> Scene.Description:
        return Scene.Description(
            id=self.id,
            name=self.scene.NAME,
            state=self.state
        )

    def set_state(self, state: Scene.State):
        self.state = state
        self.manager.notify_state_change(self)

    def get_stage(self) -> Stage:
        return self._stage

    def set_stage(self, stage: Stage) -> None:
        self._stage = stage


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


class SceneManager(QObject):
    _auto_inc: int = 0
    _scenes: dict[int, SceneContext] = dict()
    _action_manager: ActionManager
    _display: MediaDisplay
    _lighting: Lighting

    scene_state_changed: pyqtSignal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._action_manager = ActionManager(self)
        self._display = MediaDisplay()
        self._lighting = Lighting(**bulb_settings)
        self._display.placeholder()

    def get_stage(self):
        return Stage(self._display, self._lighting)

    def notify_state_change(self, scene: SceneContext):
        self.scene_state_changed.emit(scene.id)

    def _get_scene(self, scene_id) -> SceneContext:
        if scene_id not in self._scenes:
            raise RuntimeError(f"Scene with id {scene_id} is not found")
        else:
            return self._scenes[scene_id]

    def register_scene(self, scene: Type[Scene]):
        self._auto_inc += 1
        context = SceneContext(
            id=self._auto_inc,
            state=Scene.State.Stopped,
            scene=scene(),
            manager=self
        )
        context.scene.set_context(context)
        self._scenes[self._auto_inc] = context

    def get_registered_scenes(self) -> List[Scene.Description]:
        return [scene.get_description() for scene in self._scenes.values()]

    def start_scene(self, scene_id: int) -> None:
        scene = self._get_scene(scene_id)
        if scene.state != Scene.State.Stopped:
            raise IllegalState("Could not start already started scene")
        scene.set_state(Scene.State.Idle)
        scene.scene.on_start()

    def stop_scene(self, scene_id: int) -> None:
        scene = self._get_scene(scene_id)
        if scene.state == Scene.State.Stopped:
            raise IllegalState("Could not stop already stopped scene")
        if scene.state != Scene.State.Idle:
            asyncio.create_task(self._action_manager.stop_scene_actions(scene.id))
        else:
            scene.scene.on_stop()
            scene.set_state(Scene.State.Stopped)

    def get_scene_description(self, scene_id: int) -> Scene.Description:
        return self._get_scene(scene_id).get_description()

    def run_action(self, action: ActionContext):
        self._action_manager.run(action)

    def teardown(self):
        for scene_context in self._scenes.values():
            scene_context.scene.stop()
