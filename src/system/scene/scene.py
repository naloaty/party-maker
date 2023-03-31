from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from system.misc.exceptions import IllegalState


if TYPE_CHECKING:
    from .scene_context import SceneContext
    from .action_context import ActionContext


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

    def run_action(self, action: "ActionContext"):
        if self.context is None:
            raise IllegalState("Could not run action because Context is None")
        self.context.manager.run_action(action)
