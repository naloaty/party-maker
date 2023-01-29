from typing import Any, List, Union

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QObject, QVariant


class AbstractColumn(QObject):

    def __init__(self, key: str, header: str):
        super().__init__()
        self._key = key
        self._header = header

    def getKey(self):
        return self._key

    def getHeader(self):
        return self._header

    def setHeader(self, header: str):
        self._header = header

    def colData(self, rowData: dict[str, Any], role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        pass

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        pass

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        pass


class AnyDictTableModel(QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self._columns: List[AbstractColumn] = []
        self._rows: List[dict[str, Any]] = []
        self._rowById: dict[int, int] = {}
        self._idColumn: str = "id"

    def registerColumn(self, column: AbstractColumn) -> None:
        for col in self._columns:
            if col.getKey() == column.getKey():
                return

        column.setParent(self)
        self._columns.append(column)

    def setIdColumn(self, columnKey: str):
        if columnKey.strip() == "":
            raise RuntimeError("Column key cannot be empty")
        self._idColumn = columnKey

    def updateRow(self, rowIndex: int, rowData: dict[str, Any]):
        if rowIndex < 0 or rowIndex >= len(self._rows):
            raise RuntimeError(f"Row index is out of bounds: "
                               f"{rowIndex} of {len(self._rows)}")
        self._rows[rowIndex].update(rowData)
        topLeft = self.index(rowIndex, 0)
        rightBottom = self.index(rowIndex, len(self._columns) - 1)
        self.dataChanged.emit(topLeft, rightBottom)

    def updateRecord(self, recordData: dict[str, Any]):
        recordId = recordData[self._idColumn]
        row = self.getRowById(recordId)
        if row == -1:
            raise RuntimeError(f"No record with id '{recordId}' is found")
        self.updateRow(row, recordData)

    def updateRecords(self, records: List[dict[str, Any]]) -> None:
        for record in records:
            self.updateRecord(record)

    def replaceRows(self, newRows: List[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rowById.clear()
        self._rows.clear()
        for i in range(len(newRows)):
            row = newRows[i]
            if self._idColumn in row:
                recordId = row[self._idColumn]
                if recordId in self._rowById:
                    recordIndex = self._rowById[recordId]
                    record = self._rows[recordIndex]
                    raise RuntimeError(f"Unique constraint violated on id column "
                                       f"'{self._idColumn}': '{record}' inserted before '{row}' ")
                self._rows.append(row)
                self._rowById[recordId] = i
            else:
                raise RuntimeError(f"Cannot insert row that does not contain an "
                                   f"id column '{self._idColumn}': {row.items()}")
        self.endResetModel()

    def getColumnKey(self, columnIndex: int) -> str:
        if columnIndex < 0 or columnIndex >= len(self._columns):
            raise RuntimeError(f"Column index is out of bounds: "
                               f"{columnIndex} of {len(self._columns)}")

        return self._columns[columnIndex].getKey()

    def getColumnIndex(self, columnKey: str) -> int:
        for i in range(len(self._columns)):
            col = self._columns[i]
            if col.getKey() == columnKey:
                return i

        return -1

    def getRowById(self, recordId: int) -> int:
        if recordId in self._rowById:
            return self._rowById[recordId]
        else:
            return -1

    def getIdByRow(self, rowIndex: int) -> int:
        if rowIndex < 0 or rowIndex >= len(self._rows):
            raise RuntimeError(f"Row index is out of bounds: "
                               f"{rowIndex} of {len(self._rows)}")
        return self._rows[rowIndex][self._idColumn]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()
        row = self._rows[index.row()]
        column = self._columns[index.column()]
        return column.colData(row, role)

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if not index.isValid():
            return False

        row = self._rows[index.row()]
        column = self._columns[index.column()]

        if role == Qt.ItemDataRole.EditRole:
            row[column.getKey()] = value
            column.setData(index, value, role)
            self.dataChanged.emit(index, index)
            return True

        if role == Qt.ItemDataRole.CheckStateRole:
            return column.setData(index, value, role)

        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Horizontal \
                and (role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole):
            return self._columns[section].getHeader()

        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return self._columns[index.column()].flags(index)
