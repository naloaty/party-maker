import asyncio
from dataclasses import dataclass, asdict
from typing import List, Optional

from PyQt6.QtCore import QItemSelection, pyqtSlot
from PyQt6.QtWidgets import QDialog, QHeaderView
from models import AnyDictTableModel, SimpleColumn
from system.display import Media
from system.lighting import Light
from system.scene import Scene, ActionManager
from .ChallengePreviewUI import Ui_ChallengePreview


# neutral white
DEFAULT_LIGHT = Light(Light.Type.TEMP, temperature=3620, brightness=100)

@dataclass
class VideoItem:
    name: str
    file: Media
    time: int = 0
    pause: bool = False
    id: int = -1


from .settings import LIBRARY

OPENING = Media("D:/NotGames/Неигры.mp4")


class ChallengePreview(Scene, QDialog):
    NAME = "Демонстрация"
    _items: dict[int, VideoItem] = dict()
    _current_item: Optional[int] = None

    def __init__(self):
        Scene.__init__(self)
        QDialog.__init__(self)
        self.ui = Ui_ChallengePreview()
        self.ui.setupUi(self)

        self.model = AnyDictTableModel()
        self.model.registerColumn(SimpleColumn("name", "Название"))
        self.model.setIdColumn("id")
        self.ui.tbl_challenges.setModel(self.model)

        auto_inc = 0
        for item in LIBRARY:
            auto_inc += 1
            item.id = auto_inc
            self._items[auto_inc] = item
        self.model.replaceRows([asdict(it) for it in self._items.values()])

        headerView = self.ui.tbl_challenges.horizontalHeader()
        headerView.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        headerView.setMinimumSectionSize(100)

        self.ui.tbl_challenges.selectionModel().selectionChanged.connect(self.on_item_selected)
        self.ui.btn_start.clicked.connect(self.on_start_click)
        self.ui.btn_pause.clicked.connect(self.on_pause_click)
        self.ui.btn_stop.clicked.connect(self.on_stop_click)

    def on_start(self):
        self.show()

    def get_selected_item(self) -> Optional[int]:
        selection = self.ui.tbl_challenges.selectionModel().selection()
        if selection.isEmpty():
            return None
        row = selection.indexes()[0].row()
        return self.model.getIdByRow(row)

    @pyqtSlot(QItemSelection)
    def on_item_selected(self, selection: QItemSelection) -> None:
        if selection.isEmpty():
            self.ui.btn_start.setEnabled(False)
        else:
            self.ui.btn_start.setEnabled(True)

    def on_start_click(self):
        item_id = self.get_selected_item()
        if item_id is not None:
            self.run_action(self.play_item(item_id), self.on_stop_playing)

    def on_pause_click(self):
        self.run_action(self.set_pause(), None)

    def on_stop_click(self):
        self.run_action(self.stop_playing(), None)

    def on_stop(self):
        self.hide()

    def reject(self) -> None:
        self.stop()

    @ActionManager.action
    async def play_item(self, item_id: int):
        stage = self.context.get_stage()
        await stage.display.play(OPENING)
        stage.lighting.set(Light(  # color: turquoise
            Light.Type.COLOR, hue=180, saturation=100, brightness=100))
        self._current_item = item_id
        item = self._items[item_id]
        task = asyncio.create_task(stage.display.play(item.file))
        if item.pause:
            await asyncio.sleep(0.3)
            stage.display.set_position(item.time)
            item.pause = False
        self.ui.btn_pause.setEnabled(True)
        self.ui.btn_stop.setEnabled(True)
        await task

    @ActionManager.action
    async def stop_playing(self):
        stage = self.context.get_stage()
        stage.display.stop()
        item = self._items[self._current_item]
        item.pause = False
        item.time = 0
        self.ui.btn_stop.setEnabled(False)
        self.ui.btn_pause.setEnabled(False)
        self.ui.btn_stop.setEnabled(False)

    async def on_stop_playing(self, reason: Scene.StopReason):
        stage = self.context.get_stage()
        stage.lighting.set(DEFAULT_LIGHT)
        if reason != Scene.StopReason.LocalIntercept:
            stage.display.stop()

    @ActionManager.action
    async def set_pause(self):
        stage = self.context.get_stage()
        item = self._items[self._current_item]
        item.pause = True
        item.time = stage.display.get_position()
        stage.display.pause()
        self.ui.btn_stop.setEnabled(True)
        self.ui.btn_pause.setEnabled(False)
