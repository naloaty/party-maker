# Form implementation generated from reading ui file 'main_window.ui'
#
# Created by: PyQt6 UI code generator 6.4.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_ScenesWindow(object):
    def setupUi(self, ScenesWindow):
        ScenesWindow.setObjectName("ScenesWindow")
        ScenesWindow.resize(371, 328)
        self.centralwidget = QtWidgets.QWidget(ScenesWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName("gridLayout")
        self.scenes_group = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scenes_group.sizePolicy().hasHeightForWidth())
        self.scenes_group.setSizePolicy(sizePolicy)
        self.scenes_group.setObjectName("scenes_group")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scenes_group)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tbl_scenes = QtWidgets.QTableView(self.scenes_group)
        self.tbl_scenes.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_scenes.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_scenes.setCornerButtonEnabled(False)
        self.tbl_scenes.setObjectName("tbl_scenes")
        self.verticalLayout.addWidget(self.tbl_scenes)
        self.scenes_layout = QtWidgets.QHBoxLayout()
        self.scenes_layout.setObjectName("scenes_layout")
        self.btn_start = QtWidgets.QPushButton(self.scenes_group)
        self.btn_start.setEnabled(False)
        self.btn_start.setObjectName("btn_start")
        self.scenes_layout.addWidget(self.btn_start)
        self.btn_stop = QtWidgets.QPushButton(self.scenes_group)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setObjectName("btn_stop")
        self.scenes_layout.addWidget(self.btn_stop)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.scenes_layout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.scenes_layout)
        self.gridLayout.addWidget(self.scenes_group, 0, 0, 1, 1)
        ScenesWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(ScenesWindow)
        QtCore.QMetaObject.connectSlotsByName(ScenesWindow)

    def retranslateUi(self, ScenesWindow):
        _translate = QtCore.QCoreApplication.translate
        ScenesWindow.setWindowTitle(_translate("ScenesWindow", "PartyMaker [от Naloaty]"))
        self.scenes_group.setTitle(_translate("ScenesWindow", "Управление сценами"))
        self.btn_start.setText(_translate("ScenesWindow", "Запустить"))
        self.btn_stop.setText(_translate("ScenesWindow", "Остановить"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ScenesWindow = QtWidgets.QMainWindow()
    ui = Ui_ScenesWindow()
    ui.setupUi(ScenesWindow)
    ScenesWindow.show()
    sys.exit(app.exec())