from __future__ import annotations
import asyncio
from typing import Type, List, TYPE_CHECKING
from PyQt6.QtCore import QObject, pyqtSignal
from settings import bulb_settings
from system.services.projector import Projector
from system.misc.exceptions import IllegalState
from system.services.lighting import Lighting
from .action_executor import ActionExecutor
from .scene_context import SceneContext
from .scene import Scene
from .stage import Stage


if TYPE_CHECKING:
    from .action_task import ActionTask


class SceneManager(QObject):
    _auto_inc: int = 0
    _scenes: dict[int, SceneContext] = dict()
    _action_executor: ActionExecutor
    _display: Projector
    _lighting: Lighting

    scene_state_changed: pyqtSignal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._action_executor = ActionExecutor(self)
        self._display = Projector()
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
            return
        if scene.state != Scene.State.Idle:
            asyncio.create_task(self._action_executor.stop_scene_actions(scene.id))
        else:
            scene.scene.on_stop()
            scene.set_state(Scene.State.Stopped)

    def get_scene_description(self, scene_id: int) -> Scene.Description:
        return self._get_scene(scene_id).get_description()

    def run_action(self, action: ActionTask):
        self._action_executor.execute(action)

    def teardown(self):
        for scene_context in self._scenes.values():
            scene_context.scene.stop()
