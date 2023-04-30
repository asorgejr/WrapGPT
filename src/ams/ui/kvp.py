import copy
import enum
from typing import Any, Optional, List, Iterator
from dataclasses import dataclass
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QAbstractListModel, QModelIndex, Signal
from PySide2.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QStyledItemDelegate, QApplication

from . import themes

_DarkPalette = themes.DarkPalette()
_LightPalette = themes.LightPalette()

class KeyValue:
  def __init__(self, key, value):
    self.key = key
    self.value = value

class KeyValueModel(QAbstractListModel):

  def __init__(self, data):
    super().__init__()
    self.dataList = data

  def rowCount(self, parent=QModelIndex()):
    return len(self.dataList)

  def data(self, index, role=Qt.DisplayRole):
    if not index.isValid():
      return None
    if role == Qt.DisplayRole or role == Qt.EditRole:
      return self.dataList[index.row()]
    return None

  def setData(self, index, value: KeyValue, role=Qt.EditRole):
    if role == Qt.EditRole:
      self.dataList[index.row()] = value
      self.dataChanged.emit(index, index, [Qt.EditRole])
      return True
    return False

  def flags(self, index):
    return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable \
           | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

  def insertRows(self, row, count, parent=QModelIndex()):
    self.beginInsertRows(parent, row, row + count - 1)
    for i in range(count):
      self.dataList.insert(row, KeyValue('', ''))
    self.endInsertRows()
    # set focus to the last added row
    self.setData(self.index(row + count - 1, 0), KeyValue('', ''), Qt.EditRole)
    return True

  def removeRows(self, row, count, parent=QModelIndex()):
    self.beginRemoveRows(parent, row, row + count - 1)
    for i in range(count):
      if len(self.dataList) > row and len(self.dataList) > 0:
        self.dataList.pop(row)
    self.endRemoveRows()
    return True

class KeyValueDelegate(QStyledItemDelegate):
  palette = QApplication.palette()
  def createEditor(self, parent, option, index):
    editor = QWidget(parent)
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    key_edit = QLineEdit()
    layout.addWidget(key_edit)
    key_edit.setStyleSheet('border: 1px solid black;')
    value_edit = QLineEdit()
    layout.addWidget(value_edit)
    value_edit.setStyleSheet('border: 1px solid black;')

    editor.setLayout(layout)
    return editor

  def setEditorData(self, editor, index):
    kv = index.data(Qt.EditRole)
    editor.children()[1].setText(kv.key)
    editor.children()[2].setText(kv.value)

  def setModelData(self, editor, model, index):
    key = editor.children()[1].text()
    value = editor.children()[2].text()
    model.setData(index, KeyValue(key, value), Qt.EditRole)

  def updateEditorGeometry(self, editor, option, index):
    editor.setGeometry(option.rect)

  def paint(self, painter, option, index):
    from PySide2.QtGui import QColor, QPalette
    from PySide2.QtCore import QRect
    from PySide2.QtWidgets import QStyle
    rect: QRect = option.rect
    bg_color = _DarkPalette.color(QPalette.Midlight) if index.row() % 2 else _DarkPalette.color(QPalette.Dark)
    txt_color = _DarkPalette.color(QPalette.Text)
    # if the item is selected, color the background
    if option.state & QStyle.State_Selected:
      bg_color = _DarkPalette.color(QPalette.Highlight)
    painter.fillRect(option.rect, bg_color)
    kv = index.data(Qt.EditRole)
    # KEY
    key_rect = copy.copy(rect)
    key_rect.setWidth(option.rect.width() / 2)
    # calculate where to truncate the key
    key_text = kv.key
    key_text_width = painter.fontMetrics().width(key_text)
    if key_text_width > key_rect.width():
      key_text = painter.fontMetrics().elidedText(key_text, Qt.ElideRight, key_rect.width())
    # draw the key with the correct color
    painter.setPen(txt_color)
    painter.drawText(key_rect, Qt.AlignLeft, key_text)
    # VALUE
    value_rect = copy.copy(rect)
    value_rect.setWidth(option.rect.width() / 2)
    value_rect.moveLeft(value_rect.width())
    # calculate where to truncate the value
    value_text = kv.value
    value_text_width = painter.fontMetrics().width(value_text)
    if value_text_width > value_rect.width():
      value_text = painter.fontMetrics().elidedText(value_text, Qt.ElideRight, value_rect.width())
    painter.setPen(txt_color)
    painter.drawText(value_rect, Qt.AlignRight, value_text)
    # draw a line down the middle
    painter.setPen(_DarkPalette.color(QPalette.Mid))
    painter.drawLine(option.rect.center().x(), option.rect.top(), option.rect.center().x(), option.rect.bottom())
    painter.setPen(_DarkPalette.color(QPalette.Dark))
    painter.drawLine(option.rect.center().x() + 1, option.rect.top(), option.rect.center().x() + 1, option.rect.bottom())

class ListItemChangeType(enum.Enum):
  ADD = 1
  """An item was added to the list"""
  REMOVE = 2
  """An item was removed from the list"""
  MOVE = 3
  """An item was moved in the list"""
  UPDATE = 4
  """An item was updated in the list"""


@dataclass(frozen=True)
class ListChangedEvent:
  """An event that is fired when the list changes"""
  index: int
  """The index of the item that changed"""
  item: Any
  """The item that changed"""
  changeType: ListItemChangeType
  """The type of change that occurred"""
  newIndex: Optional[int] = None
  """The new index of the item if it was moved"""

class KeyValueListView(QWidget):

  eListChanged = Signal(ListChangedEvent)

  def __init__(self, parent=None):
    from PySide2.QtWidgets import QListView, QPushButton, QVBoxLayout
    super().__init__(parent)
    self.model = KeyValueModel([KeyValue('', '')])
    self.delegate = KeyValueDelegate()
    self.listView = QListView()
    self.listView.setModel(self.model)
    self.listView.setItemDelegate(self.delegate)
    self.listView.setEditTriggers(QListView.DoubleClicked)
    # line edit content is always displayed
    self.listView.setViewMode(QListView.ListMode)
    self.listView.setDragDropMode(QListView.InternalMove)
    self.listView.setDragEnabled(True)
    self.listView.setDropIndicatorShown(True)
    self.listView.setAcceptDrops(True)
    # Move/Add/Remove events
    self.listView.model().rowsInserted.connect(lambda parent, start, end: self.eListChanged.emit(ListChangedEvent(start, self.model.dataList[start], ListItemChangeType.ADD)))
    self.listView.model().rowsRemoved.connect(lambda parent, start, end: self.eListChanged.emit(ListChangedEvent(start, None, ListItemChangeType.REMOVE)))
    self.listView.model().rowsMoved.connect(lambda parent, start, end, dest: self.eListChanged.emit(ListChangedEvent(start, self.model.dataList[start], ListItemChangeType.MOVE, dest)))
    self.listView.model().dataChanged.connect(lambda topLeft, bottomRight, roles: self.eListChanged.emit(ListChangedEvent(topLeft.row(), self.model.dataList[topLeft.row()], ListItemChangeType.UPDATE)))
    # +/- buttons to pop off the end or add a new item
    self.addButton = QPushButton('+')
    self.addButton.clicked.connect(self._onAddItemBtn)
    self.removeButton = QPushButton('-')
    self.removeButton.clicked.connect(self._onRemItemBtn)

    self.layout = QVBoxLayout()
    self.setLayout(self.layout)
    self.layout.addWidget(self.listView)
    self.btnLayout = QHBoxLayout()
    self.btnLayout.addWidget(self.addButton)
    self.btnLayout.addWidget(self.removeButton)
    self.layout.addLayout(self.btnLayout)

  def count(self):
    return self.model.rowCount()

  def append(self, item):
    self.model.insertRows(self.model.rowCount(), 1)
    self.model.setData(self.model.index(self.model.rowCount() - 1), item)

  def remove(self, index):
    self.model.removeRows(index, 1)

  def clear(self):
    self.model.removeRows(0, self.model.rowCount())

  def __getitem__(self, index) -> KeyValue:
    return self.model.dataList[index]

  def __setitem__(self, index, value: KeyValue):
    self.model.setData(self.model.index(index), value)

  def __delitem__(self, index):
    self.model.removeRows(index, 1)

  def __iter__(self) -> Iterator[KeyValue]:
    return iter(self.model.dataList)

  def __len__(self):
    return self.model.rowCount()

  def __contains__(self, item):
    return item in self.model.dataList

  def __reversed__(self):
    return reversed(self.model.dataList)

  def __str__(self):
    return str(self.model.dataList)

  def __repr__(self):
    return repr(self.model.dataList)

  def _onAddItemBtn(self):
    self.model.insertRows(self.model.rowCount(), 1)

  def _onRemItemBtn(self):
    self.model.removeRows(self.model.rowCount() - 1, 1)

  def toDict(self) -> dict:
    ret = {}
    for i in range(self.model.rowCount()):
      kv = self.model.data(self.model.index(i))
      ret[kv.key] = kv.value
    return ret
