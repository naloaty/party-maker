from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from typing import Optional
from .scene import Scene


if TYPE_CHECKING:
    from .stage import Stage
    from .scene_manager import SceneManager


@dataclass
class SceneContext:
    id: int
    state: Scene.State
    scene: Scene
    manager: SceneManager
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
