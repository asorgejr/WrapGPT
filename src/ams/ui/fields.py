import os
import enum
from dataclasses import dataclass
from typing import Any, Optional, Union, Protocol, Tuple
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import (QObject, QSize, Qt, QObject, QRect, Signal, QTimer)
from PySide2.QtWidgets import (QWidget, QTextEdit, QLineEdit, QHBoxLayout, QLabel)
from PySide2.QtGui import (QPalette, QColor, QCursor, QPixmap, QPainter, QFont, QFontMetrics, QPaintEvent, QKeyEvent)
from .controls import AbstractControl, ValueChangedEvent

Numeric = Union[int, float]
LineWrapMode = QTextEdit.LineWrapMode


class CaretType(enum.Enum):
  """The type of caret to use"""
  LINE = 1
  """A line caret that is the height of the line"""
  BLOCK = 2
  """A block caret that is the height of the line"""
  UNDERLINE = 3
  """An underline caret that is underneath the character"""



class CaretState:
  """Controls basic caret functionality like blinking"""
  _timer: QTimer
  @property
  def timer(self) -> QTimer:
    """The timer that controls the caret blinking"""
    return self._timer

  _visible: bool
  @property
  def visible(self) -> bool:
    """Whether the caret is visible or not"""
    return self._visible
  @visible.setter
  def visible(self, value: bool):
    self._visible = value

  _rate: int
  @property
  def rate(self) -> int:
    """The rate at which the caret blinks in milliseconds. Values less than 0 will disable the caret blinking"""
    return self._rate
  @rate.setter
  def rate(self, value: int):
    self._rate = value
    if self._rate < 0:
      self._timer.stop()
      return
    self._timer.setInterval(self._rate)
    self._timer.start()

  def __init__(self, rate: int = 500):
    self._rate = rate
    self._timer = QTimer()
    self._timer.setSingleShot(False)
    self._visible = True
    if self._rate < 0: return
    self._timer.timeout.connect(self.toggle)
    self._timer.start(self._rate)

  def toggle(self):
    self._visible = not self._visible





@dataclass
class TextFieldStyle:
  """A style object for TextField"""
  font: QFont = QFont("System", 9)
  """The font to use for the text field"""
  multiLine: bool = False
  """Whether the text field should be multiline or not"""
  wrapMode: LineWrapMode = LineWrapMode.WidgetWidth
  """The wrap mode to use when the text field is multiline"""
  caretType: CaretType = CaretType.LINE
  """The type of caret to use"""
  caretWidth: int = 2
  """The width of the caret in pixels. Only used when the caret type is CaretType.LINE"""
  caretOffset: Tuple[int, int] = (0, 0)
  caretColor: QColor = QColor(231, 167, 38)
  textColor: QColor = QColor(255, 255, 255)
  backgroundColor: QColor = QColor(0, 0, 0)
  borderColor: QColor = QColor(0, 0, 0)
  borderWidth: int = 1
  borderRadius: int = 0
  padding: int = 0
  margin: int = 0
  caretColor: QColor = QColor(209, 154, 102)
  """The color of the caret when the text field has focus"""
  caretBackgroundColor: QColor = QColor(209, 154, 102)
  """The background color of the caret when the text field has focus"""
  caretBorderColor: QColor = QColor(209, 154, 102)
  """The border color of the caret when the text field has focus"""


class AbstractTextEdit(Protocol):
  @property
  def fieldStyle(self) -> TextFieldStyle: ...
  @fieldStyle.setter
  def fieldStyle(self, value: TextFieldStyle): ...

  @property
  def value(self) -> str: ...
  @value.setter
  def value(self, value: str): ...

  @property
  def caretState(self) -> CaretState: ...
  @caretState.setter
  def caretState(self, value: CaretState): ...

  # region QWidget methods
  def sizeHint(self) -> QSize: ...
  def minimumSizeHint(self) -> QSize: ...
  def hasFocus(self) -> bool: ...
  def setFocus(self): ...
  def setEnabled(self, value: bool): ...
  def setStyleSheet(self, value: str): ...
  def setCursor(self, cursor: QCursor): ...
  def setPalette(self, palette: QPalette): ...
  def width(self) -> int: ...
  def height(self) -> int: ...
  # endregion
  # region QTextEdit methods
  def setPlaceholderText(self, text: str): ...
  def setReadOnly(self, value: bool): ...
  def cursorRect(self) -> QRect: ...
  def setFont(self, font: QFont): ...
  def fontMetrics(self) -> QFontMetrics: ...
  def paintEvent(self, event): ...
  def overwriteMode(self) -> bool: ...
  def setOverwriteMode(self, value: bool): ...
  # endregion
  @classmethod # type: ignore
  def create(cls, parent: Optional[QObject] = None, style: Optional[TextFieldStyle] = None) -> 'AbstractTextEdit': ...




def caretPainter(field: AbstractTextEdit, event: QPaintEvent):
    # if not isinstance(field, QWidget): raise TypeError("field must be of type QWidget")
    if not field.hasFocus(): return
    caretState = field.caretState
    if not caretState.visible: return
    rtf = isinstance(field, QTextEdit)
    rect = field.cursorRect()
    rect.setHeight(field.fontMetrics().height())
    if field.fieldStyle.caretType == CaretType.LINE:
      rect.setWidth(field.fieldStyle.caretWidth)
    # set x to the right of the character the cursor is on
    rect.setX(rect.x() + rect.width()-1)
    if all([isinstance(ost, int) for ost in field.fieldStyle.caretOffset]):
      rect.translate(*field.fieldStyle.caretOffset)
    if not isinstance(field, QWidget): raise TypeError("field must inherit from QWidget")
    painter: QPainter = QPainter(field)
    if rtf:
      painter.begin(field.viewport())
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QtGui.QBrush(field.fieldStyle.caretColor))
    # draw the cursor
    painter.drawRect(rect)
    painter.drawText(QRect(QtCore.QPoint(0, 0), field.sizeHint()), "test")
    painter.end()


def keyEvent(field: AbstractTextEdit, e: QKeyEvent):
  if e.key() == Qt.Key_Insert:
    field.setOverwriteMode(not field.overwriteMode())
    return


class TextField(AbstractControl, QTextEdit):
  """A text input field with a lot of quality of life improvements"""
  # region Properties

  _fieldStyle: TextFieldStyle = None  # type: ignore
  @property
  def fieldStyle(self) -> TextFieldStyle:
    return self._fieldStyle
  @fieldStyle.setter
  def fieldStyle(self, value: TextFieldStyle):
    if not isinstance(value, TextFieldStyle): raise TypeError("style must be of type TextFieldStyle")
    self._fieldStyle = value
    self.setFont(self._fieldStyle.font)

  @property
  def val(self) -> str:
    return self.toPlainText()
  @val.setter
  def val(self, value: str):
    self.setPlainText(value)

  _caretState: CaretState
  @property
  def caretState(self) -> CaretState:
    return self._caretState
  @caretState.setter
  def caretState(self, value: CaretState):
    if not isinstance(value, CaretState): raise TypeError("caretState must be of type CaretState")
    self._caretState = value

  # endregion Properties

  eValueChanged = QtCore.Signal(ValueChangedEvent)

  def __init__(self, parent: Optional[QObject] = None, text: str = ""):
    """A text input field with a lot of quality of life improvements"""
    # Validate super args
    if parent and not isinstance(parent, QObject): raise TypeError("parent must be of type QObject")
    if not isinstance(text, str): raise TypeError("text must be of type str")
    super().__init__(parent)
    # Validate args
    self.fieldStyle = TextFieldStyle()
    self._caretState = CaretState()
    self._oldText = ""
    # Setup the widget
    self.setPlainText(text)
    self.setAcceptRichText(False)
    # multi line
    self.setLineWrapMode(self.fieldStyle.wrapMode)
    self.textChanged.connect(self._onValueChanged)

  def paintEvent(self, event):
      """This creates a custom caret for the input field."""
      super().paintEvent(event)
      caretPainter(self, event)

  def _onValueChanged(self):
    self.eValueChanged.emit(ValueChangedEvent(self._oldText, self.toPlainText()))
    self._oldText = self.toPlainText()

  def value(self) -> str:
    """Returns the value of the field"""
    return self.toPlainText()

  def setValue(self, value: str):
    """Sets the value of the field"""
    self._oldText = self.toPlainText()
    self.setPlainText(value)

  def setDefault(self):
    """Sets the value of the field to the default: `str()`."""
    self.setValue("")



class StringField(AbstractControl, QLineEdit):
  """A text input field with a lot of quality of life improvements"""
  # region Properties

  _fieldStyle: TextFieldStyle = None  # type: ignore
  @property
  def fieldStyle(self) -> TextFieldStyle:
    return self._fieldStyle
  @fieldStyle.setter
  def fieldStyle(self, value: TextFieldStyle):
    if not isinstance(value, TextFieldStyle): raise TypeError("style must be of type TextFieldStyle")
    self._fieldStyle = value
    self.setFont(self._fieldStyle.font)

  @property
  def val(self) -> str:
    return self.text()
  @val.setter
  def val(self, value: str):
    self.setText(value)

  _caretState: CaretState
  @property
  def caretState(self) -> CaretState:
    return self._caretState
  @caretState.setter
  def caretState(self, value: CaretState):
    if not isinstance(value, CaretState): raise TypeError("caretState must be of type CaretState")
    self._caretState = value

  # endregion Properties

  eValueChanged = QtCore.Signal(ValueChangedEvent)

  def __init__(self, parent: Optional[QObject] = None, text: str = ""):
    """A text input field with a lot of quality of life improvements"""
    # Validate super args
    if parent and not isinstance(parent, QObject): raise TypeError("parent must be of type QObject")
    if not isinstance(text, str): raise TypeError("text must be of type str")
    super().__init__(parent)
    # Validate args
    self.fieldStyle = TextFieldStyle()
    self._caretState = CaretState()
    self._oldText = ""
    self.setText(text)
    self.editingFinished.connect(self._onValueChanged)
    self.setFont(self.fieldStyle.font)

  def focusInEvent(self, e: QtGui.QFocusEvent) -> None:
    self._oldText = self.text()
    super().focusInEvent(e)

  def paintEvent(self, event):
      """This creates a custom caret for the input field."""
      super().paintEvent(event)
      caretPainter(self, event)

  def setOverwriteMode(self, overwrite: bool): pass

  def overwriteMode(self) -> bool: return False

  def _onValueChanged(self):
    """This is called when the value of the field changes"""
    self.eValueChanged.emit(ValueChangedEvent(self._oldText, self.text()))

  def value(self) -> str:
    """Returns the value of the field"""
    return self.val

  def setValue(self, value: str):
    """Sets the value of the field"""
    self.val = str(value)

  def setDefault(self):
    """Sets the value of the field to the default: `str()`."""
    self.setValue("")
