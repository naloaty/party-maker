from typing import Any
from PyQt6.QtCore import Qt, QModelIndex, QVariant

from .AnyDictTableModel import AbstractColumn


class SimpleColumn(AbstractColumn):

    def colData(self, rowData: dict[str, Any], role: int = ...) -> Any:
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return str(rowData[self.getKey()])
        else:
            return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
