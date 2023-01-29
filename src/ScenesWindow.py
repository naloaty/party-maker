from dataclasses import asdict
from typing import Union, Optional

from PyQt6 import QtGui
from PyQt6.QtCore import QItemSelection, pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QHeaderView

from ScenesWindowUI import Ui_ScenesWindow
from models.AnyDictTableModel import AnyDictTableModel
from models.SimpleColumn import SimpleColumn
from system.scene import Scene, SceneManager


class ScenesWindow(QMainWindow):

    def __init__(self, manager: SceneManager):
        super().__init__()
        self.ui = Ui_ScenesWindow()
        self.ui.setupUi(self)

        self.manager = manager

        self.model = AnyDictTableModel()
        self.model.registerColumn(SimpleColumn("name", "Название"))
        self.model.registerColumn(SimpleColumn("state", "Статус"))
        self.model.setIdColumn("id")
        self.ui.tbl_scenes.setModel(self.model)

        headerView = self.ui.tbl_scenes.horizontalHeader()
        headerView.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        headerView.setMinimumSectionSize(100)

        self.model.replaceRows([asdict(it) for it in self.manager.get_registered_scenes()])
        self.ui.tbl_scenes.selectionModel().selectionChanged.connect(self.on_scene_selected)
        self.ui.btn_start.clicked.connect(self.start_selected_scene)
        self.ui.btn_stop.clicked.connect(self.stop_selected_scene)
        self.manager.scene_state_changed.connect(self.scene_state_changed)

    def get_selected_scene(self) -> Optional[int]:
        selection = self.ui.tbl_scenes.selectionModel().selection()
        if selection.isEmpty():
            return None
        row = selection.indexes()[0].row()
        return self.model.getIdByRow(row)

    def update_ui_state(self) -> None:
        scene_id = self.get_selected_scene()
        if scene_id is None:
            self.ui.btn_start.setEnabled(False)
            self.ui.btn_stop.setEnabled(False)
        else:
            scene_desc = self.manager.get_scene_description(scene_id)

            if scene_desc.state == Scene.State.Stopped:
                self.ui.btn_start.setEnabled(True)
                self.ui.btn_stop.setEnabled(False)
            else:
                self.ui.btn_start.setEnabled(False)
                self.ui.btn_stop.setEnabled(True)

    @pyqtSlot(QItemSelection)
    def on_scene_selected(self, selection: QItemSelection) -> None:
        self.update_ui_state()

    @pyqtSlot()
    def start_selected_scene(self) -> None:
        scene_id = self.get_selected_scene()
        if scene_id is not None:
            self.manager.start_scene(scene_id)

    @pyqtSlot()
    def stop_selected_scene(self) -> None:
        scene_id = self.get_selected_scene()
        if scene_id is not None:
            self.manager.stop_scene(scene_id)

    @pyqtSlot(int)
    def scene_state_changed(self, scene_id: int) -> None:
        scene_description = asdict(self.manager.get_scene_description(scene_id))
        self.model.updateRecord(scene_description)
        self.update_ui_state()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.manager.teardown()
