# Window. Minimum required 3.9
import sys
if sys.version_info.major < 3 or sys.version_info.minor < 9:
  raise RuntimeError("Python 3.9 or higher is required.")
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, Union, TypeVar
from PySide2.QtCore import (QPoint, QSize, Qt, QObject, QRect, Signal)
from PySide2.QtGui import (QCloseEvent, QMoveEvent, QResizeEvent, QShowEvent, QHideEvent)
from PySide2.QtWidgets import (QWidget, QLayout)

DEFAULT_SIZE = QSize(480, 360) # 4:3
"""The default size of a Window."""

TPosition = Union[QPoint, Tuple[int, int]]
TSize = Union[QSize, Tuple[int, int]]
TLayout = TypeVar("TLayout", bound=QLayout)


class Window(QWidget, Generic[TLayout]):
  """A simple non-modal window initialized with some kind of layout, a title and a close button.
  
  Type Parameters:
    TLayout (QLayout): The type of the layout of the Window."""
  # region Public Attributes/Properties
  _windowLayout: TLayout
  @property
  def windowLayout(self) -> TLayout:
    """The main layout of the Window."""
    return self._windowLayout

  _windowTitle: str
  @property
  def windowTitle(self) -> str:
    """The title of the Window."""
    return self._windowTitle
  @windowTitle.setter
  def windowTitle(self, value: str):
    if not isinstance(value, str): raise TypeError(f"title must be a str. Got {type(value)}")
    self._windowTitle = value
    self.setWindowTitle(value)
  
  _windowPosition: Optional[TPosition]
  @property
  def windowPosition(self) -> QPoint:
    """The position of the Window."""
    if not self._windowPosition: return QPoint(0, 0)
    return self._windowPosition
  @windowPosition.setter
  def windowPosition(self, value: TPosition):
    if isinstance(value, tuple): value = QPoint(value[0], value[1])
    elif not isinstance(value, QPoint): raise TypeError(f"position must be a QPoint or a tuple of 2 ints. Got {type(value)}")
    self._windowPosition = value
    self.move(value)
  
  _windowSize: Optional[TSize]
  @property
  def windowSize(self) -> QSize:
    """The size of the Window."""
    if not self._windowSize: return DEFAULT_SIZE # 4:3
    return self._windowSize
  @windowSize.setter
  def windowSize(self, value: TSize):
    if isinstance(value, tuple): value = QSize(value[0], value[1])
    elif not isinstance(value, QSize): raise TypeError(f"size must be a QSize or a tuple of 2 ints. Got {type(value)}")
    self._windowSize = value
    self.resize(value)

  _windowGeometry: QRect
  @property
  def windowGeometry(self) -> QRect:
    """The geometry of the Window."""
    return self._windowGeometry
  @windowGeometry.setter
  def windowGeometry(self, value: QRect):
    if not isinstance(value, QRect): raise TypeError(f"geometry must be a QRect. Got {type(value)}")
    self._windowGeometry = value
    self.setGeometry(value)
  
  # endregion Public Attributes/Properties

  # region Signals

  windowClosed = Signal(QCloseEvent)
  """Emitted when the window is closed."""
  windowShown = Signal(QShowEvent)
  """Emitted when the window is shown."""
  windowHidden = Signal(QHideEvent)
  """Emitted when the window is hidden."""
  windowMoved = Signal(QMoveEvent)
  """Emitted when the window is moved."""
  windowResized = Signal(QResizeEvent)
  """Emitted when the window is resized."""

  # endregion Signals

  def __init__(self, parent: Optional[QObject], layout: TLayout, title="Window", position: Optional[TPosition] = None, size: Optional[TSize] = None):
    """Initializes a Window.
    
    Args:
      parent (QObject = None): The parent to attach to.
      title (str = "Window"): The title of the window. Can be set later with the `windowTitle` property.
      position (TPosition = None): The position of the window. Can be set later with the `windowPosition` property.
      size (TSize = None): The size of the window. Can be set later with the `windowSize` property. If not set, the default size is 480x360 (4:3).
      layout (QLayout = None): The layout of the window. Can be set later with the `windowLayout` property.
    """
    # Validate arguments
    if not isinstance(title, str): raise TypeError(f"title must be a str. Got {type(title)}")
    if layout and not isinstance(layout, QLayout): raise TypeError(f"layout must be a QLayout. Got {type(layout)}")
    if position and not isinstance(position, (QPoint, tuple)): raise TypeError(f"position must be a QPoint or a tuple of 2 ints. Got {type(position)}")
    if size and not isinstance(size, (QSize, tuple)): raise TypeError(f"size must be a QSize or a tuple of 2 ints. Got {type(size)}")
    # Initialize super
    super().__init__(parent)
    # Initialize instance attributes with arguments
    self._windowTitle = title
    self._windowLayout = layout
    self._windowPosition = position
    self._windowSize = size
    # Set up window
    self._windowLayout.setContentsMargins(0, 0, 0, 0)
    self._windowLayout.setSpacing(0)
    self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint) # Make the window non-modal with title and close button
    self.setAttribute(Qt.WA_DeleteOnClose) # Delete the window when it is closed
    self.setLayout(self._windowLayout)
    self.setWindowTitle(self._windowTitle)
    self.resize(self._windowSize if self._windowSize else DEFAULT_SIZE)
    if self._windowPosition: self.move(self._windowPosition)
    # Additional attributes to be initialized
    self._windowGeometry = self.geometry()
  
  # region Private Methods

  def _updateGeometryCoords(self):
    self._windowGeometry = self.geometry()
    self._windowPosition = self.pos()
    self._windowSize = self.size()

  # endregion Private Methods

  # region Overridden Methods

  def closeEvent(self, event: QCloseEvent):
    """Called when the Window is closed."""
    self._updateGeometryCoords()
    self.windowClosed.emit(event) # type: ignore
    super().closeEvent(event)
  
  def hideEvent(self, event: QHideEvent):
    """Called when the Window is hidden."""
    super().hideEvent(event)
    self.windowHidden.emit(event) # type: ignore
  
  def moveEvent(self, event: QMoveEvent):
    """Called when the Window is moved."""
    super().moveEvent(event)
    self._updateGeometryCoords()
    self.windowMoved.emit(event) # type: ignore
  
  def resizeEvent(self, event: QResizeEvent):
    """Called when the Window is resized."""
    super().resizeEvent(event)
    self._updateGeometryCoords()
    self.windowResized.emit(event) # type: ignore
  
  def showEvent(self, event: QShowEvent):
    """Called when the Window is shown."""
    super().showEvent(event)
    self.windowShown.emit(event) # type: ignore

  def show(self):
    """Show the Window."""
    # get the current position of the Window
    self.activateWindow()
    self.raise_()
    if self._windowPosition is not None:
      super().move(self._windowPosition)
    if self._windowSize is not None:
      super().resize(self._windowSize)
    super().show()

  def hide(self):
    """Hide the Window."""
    # get the current position of the Window
    self._windowPosition = self.pos()
    self._windowSize = self.size()
    super().hide()

  def close(self):
    """Close the Window."""
    self._onClose()
    super().close()
  
  def resize(self, size: TSize):
    """Resize the Window."""
    oldSize = self.size()
    if isinstance(size, tuple): size = QSize(size[0], size[1])
    elif not isinstance(size, QSize): raise TypeError(f"size must be a QSize or a tuple of 2 ints. Got {type(size)}")
    self._windowSize = size
    super().resize(size)
    self.windowResized.emit(QResizeEvent(size, self.size())) # type: ignore
  
  def move(self, position: TPosition):
    """Move the Window."""
    oldPos = self.pos()
    if isinstance(position, tuple): position = QPoint(position[0], position[1])
    elif not isinstance(position, QPoint): raise TypeError(f"position must be a QPoint or a tuple of 2 ints. Got {type(position)}")
    self._windowPosition = position
    super().move(position)
    self.windowMoved.emit(QMoveEvent(position, self.pos())) # type: ignore
  
  # endregion Overridden Methods
