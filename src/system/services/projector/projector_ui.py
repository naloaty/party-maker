# Form implementation generated from reading ui file 'system\projector.ui'
#
# Created by: PyQt6 UI code generator 6.4.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MediaDisplay(object):
    def setupUi(self, MediaDisplay):
        MediaDisplay.setObjectName("MediaDisplay")
        MediaDisplay.resize(400, 300)
        self.gridLayout = QtWidgets.QGridLayout(MediaDisplay)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.videoframe = QtWidgets.QFrame(MediaDisplay)
        self.videoframe.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.videoframe.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.videoframe.setObjectName("videoframe")
        self.gridLayout.addWidget(self.videoframe, 0, 0, 1, 1)

        self.retranslateUi(MediaDisplay)
        QtCore.QMetaObject.connectSlotsByName(MediaDisplay)

    def retranslateUi(self, MediaDisplay):
        _translate = QtCore.QCoreApplication.translate
        MediaDisplay.setWindowTitle(_translate("MediaDisplay", "Dialog"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MediaDisplay = QtWidgets.QDialog()
    ui = Ui_MediaDisplay()
    ui.setupUi(MediaDisplay)
    MediaDisplay.show()
    sys.exit(app.exec())
