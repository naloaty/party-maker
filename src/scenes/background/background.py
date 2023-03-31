import asyncio
from dataclasses import dataclass, asdict
from typing import Optional

from PyQt6.QtCore import QItemSelection, pyqtSlot
from PyQt6.QtWidgets import QDialog, QHeaderView

from system.qt import AnyDictTableModel, SimpleColumn
from system.scene import Scene, action
from system.services.projector import Media
from .background_ui import Ui_Background


@dataclass
class VideoItem:
    name: str
    file: Media
    time: int = 0
    id: int = -1


LIBRARY = [
    VideoItem("Лавовая лампа", Media("D:/Background/Bubbles.mp4")),
    VideoItem("Лазер", Media("D:/Background/NeonTunnel.mp4")),
    VideoItem("Облака в воде", Media("D:/Background/InkWater.mp4")),
    VideoItem("Пираты карибского моря", Media("D:/NotGames/src/pirates.mp4"))
]


class Background(Scene, QDialog):
    NAME = "Окружение"
    _items: dict[int, VideoItem] = dict()
    _current_item: Optional[int] = None

    def __init__(self):
        Scene.__init__(self)
        QDialog.__init__(self)
        self.ui = Ui_Background()
        self.ui.setupUi(self)

        self.model = AnyDictTableModel()
        self.model.registerColumn(SimpleColumn("name", "Название"))
        self.model.registerColumn(SimpleColumn("time", "Время"))
        self.model.setIdColumn("id")
        self.ui.tbl_fragments.setModel(self.model)

        auto_inc = 0
        for item in LIBRARY:
            auto_inc += 1
            item.id = auto_inc
            self._items[auto_inc] = item
        self.model.replaceRows([asdict(it) for it in self._items.values()])

        headerView = self.ui.tbl_fragments.horizontalHeader()
        headerView.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        headerView.setMinimumSectionSize(100)

        self.ui.tbl_fragments.selectionModel().selectionChanged.connect(self.on_item_selected)
        self.ui.btn_start.clicked.connect(self.on_start_click)
        self.ui.btn_stop.clicked.connect(self.on_stop_click)

    def on_start(self):
        self.show()

    def get_selected_item(self) -> Optional[int]:
        selection = self.ui.tbl_fragments.selectionModel().selection()
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
            self.run_action(self.play_item(item_id))

    def on_stop_click(self):
        self.run_action(self.stop_playing())

    def on_stop(self):
        self.hide()

    def reject(self) -> None:
        self.stop()

    async def on_stop_playing(self, reason: Scene.StopReason):
        stage = self.context.get_stage()
        item = self._items[self._current_item]
        item.time = stage.display.get_position()
        if reason != Scene.StopReason.LocalIntercept:
            stage.display.stop()
        self.model.updateRecord(asdict(item))
        self.ui.btn_stop.setEnabled(False)

    @action(on_stop_playing)
    async def play_item(self, item_id: int):
        stage = self.context.get_stage()
        self._current_item = item_id
        item = self._items[item_id]
        task = asyncio.create_task(stage.display.play(item.file))
        await asyncio.sleep(0.3)
        stage.display.set_position(item.time)
        self.ui.btn_stop.setEnabled(True)
        await task
        self.ui.btn_stop.setEnabled(False)

    @action()
    async def stop_playing(self):
        stage = self.context.get_stage()
        stage.display.stop()
