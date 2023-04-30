# import os
import importlib as il
from typing import Callable, List, Optional, Tuple, Union

from PySide2.QtCore import Qt, QObject
from PySide2.QtWidgets import (
  QPushButton, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel,
  QSizePolicy, QSpacerItem)

from . import window

il.reload(window) # TODO: remove this

Window = window.Window
TPosition = window.TPosition
TSize = window.TSize
StandardButton = QDialogButtonBox.StandardButton

class Dialog(Window[QVBoxLayout]):
  """A modeless dialog with a title bar and a close button. Useful for displaying a widget in a floating window.
  Callbacks can be registered to be called when the dialog is closed and when the action buttons are clicked."""

  _dialogBody: Union[QVBoxLayout, QHBoxLayout]
  @property
  def dialogBody(self) -> QVBoxLayout:
    """The body of the dialog. Add widgets to this layout to add them to the dialog."""
    return self._dialogBody
  @dialogBody.setter
  def dialogBody(self, value: Union[QVBoxLayout, QHBoxLayout]):
    if not isinstance(value, (QVBoxLayout, QHBoxLayout)): raise TypeError(f"body must be a Q[H|V]BoxLayout. Got {type(value)}")
    self._dialogBody = value
    self._rebuild()
    # self.windowLayout.insertLayout(0, self._dialogBody)

  _dialogButtonBox: QDialogButtonBox
  @property
  def dialogButtonBox(self) -> QDialogButtonBox:
    """The action buttons of the dialog. By default this contains a close button."""
    return self._dialogButtonBox

  _dialogButtons: tuple = (QDialogButtonBox.Close,)
  @property
  def dialogButtons(self) -> tuple:
    """The action buttons of the dialog. By default this contains QDialogButtonBox.Close."""
    return self._dialogButtons
  @dialogButtons.setter
  def dialogButtons(self, value: tuple):
    if not isinstance(value, tuple): raise TypeError(f"dialogButtons must be a tuple. Got {type(value)}")
    # make buttons from the tuple
    self._dialogButtonBox.clear()
    added = set()
    for standardButton in value:
      if not isinstance(standardButton, QDialogButtonBox.StandardButton): raise TypeError(f"dialogButtons must be a tuple of QDialogButtonBox.StandardButton. Got {type(standardButton)}")
      if standardButton in added: continue
      button = self._dialogButtonBox.addButton(standardButton)
      def buttonClicked(_):
        for callback in self._buttonCallbacks:
          callback(standardButton)
        if standardButton in (QDialogButtonBox.Close, QDialogButtonBox.Cancel):
          self.close()
      button.clicked.connect(buttonClicked)
      added.add(standardButton)
    self._dialogButtons = value

  # callbacks registered to be called when the dialog is closed
  _closeCallbacks: List[Callable[[], None]]
  _buttonCallbacks: List[Callable[[QDialogButtonBox.StandardButton], None]]


  def __init__(self, parent: Optional[QObject]=None,
               body: QVBoxLayout=QVBoxLayout(), dialogButtons: Tuple[StandardButton]=(QDialogButtonBox.Close,),
               title="Window", position: Optional[TPosition] = None, size: Optional[TSize] = None):
    """A modeless dialog with a title bar and a close button. Useful for displaying a widget in a floating window.
    Callbacks can be registered by button id to be called when a button is clicked.

    Args:
      parent (QtWidgets.QWidget = None): The parent widget.
      body (QVBoxLayout = QVBoxLayout()): The body of the dialog.
      dialogButtons ((QtWidgets.QDialogButtonBox.StandardButton,...) = (QDialogButtonBox.Close,)): The action buttons of the dialog.
      title (str = "Window"): The title of the dialog. Can be set later with the `windowTitle` property.
      position (QPoint|Tuple[int,int] = None): The position of the dialog. If not specified, the dialog will be centered on the screen. Can be set later with the `windowPosition` property.
      size (QSize|Tuple[int,int] = None): The size of the dialog. If not specified, the dialog will be 480x360. Can be set later with the `windowSize` property.
    """
    # Validate arguments
    if not isinstance(body, QVBoxLayout): raise TypeError(f"body must be a QVBoxLayout. Got {type(body)}")
    if not isinstance(dialogButtons, tuple): raise TypeError(f"dialogButtons must be a tuple. Got {type(dialogButtons)}")
    super(Dialog, self).__init__(parent, QVBoxLayout(), title=title, position=position, size=size)
    self._dialogBody: QVBoxLayout = body
    self._dialogButtonBox: QDialogButtonBox = QDialogButtonBox()
    self._closeCallbacks = []
    self._buttonCallbacks = []
    self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
    self.setMinimumSize(self.windowSize)
    self.dialogButtons = dialogButtons
    self.windowLayout.addLayout(self.dialogBody, stretch=1)
    self.windowLayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
    self.windowLayout.addStretch(1)
    self._dialogButtonBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    self.windowLayout.addWidget(self._dialogButtonBox, alignment=Qt.AlignBottom)
    # expand the body layout to fill the dialog
    # button box should be at the bottom and compressed
    self.setLayout(self.windowLayout)
    self.windowLayout.setSpacing(10)

  def registerCloseCallback(self, callback: Callable[[], None]) -> bool:
    """Add a callback to be called when the dialog is closed.

    Args:
      callback (Callable[[], None]): The callback to be called when the dialog is closed.
    Returns:
      bool: True if the callback was added, False if the callback was already registered.
    """
    if not isinstance(callback, Callable): raise TypeError(f"callback must be a Callable. Got {type(callback)}")
    if callback in self._closeCallbacks:
      return False
    self._closeCallbacks.append(callback)
    return True

  def unregisterCloseCallback(self, callback: Callable[[], None]) -> bool:
    """Remove a callback from the list of callbacks to be called when the dialog is closed.

    Args:
      callback (Callable[[], None]): The callback to be called when the dialog is closed.
    Returns:
      bool: True if the callback was removed, False if the callback was not registered.
    """
    if callback not in self._closeCallbacks:
      return False
    self._closeCallbacks.remove(callback)
    return True

  def registerButtonCallback(self, callback: Callable[[StandardButton], None]) -> bool:
    """Add a callback to be called when a button is clicked.

    Args:
      callback (Callable[[QDialogButtonBox.StandardButton], None]): The callback to be called when a button is clicked. The StandardButton type that was clicked is passed as an argument.
    Returns:
      bool: True if the callback was added, False if the callback was already registered.
    """
    if not isinstance(callback, Callable): raise TypeError(f"callback must be a Callable. Got {type(callback)}")
    if callback in self._buttonCallbacks:
      return False
    self._buttonCallbacks.append(callback)
    return True

  def unregisterButtonCallback(self, callback: Callable[[StandardButton], None]) -> bool:
    """Remove a callback from the list of callbacks to be called when a button is clicked.

    Args:
      callback (Callable[[QDialogButtonBox.StandardButton], None]): The callback to be called when a button is clicked. The StandardButton type that was clicked is passed as an argument.
    Returns:
      bool: True if the callback was removed, False if the callback was not registered.
    """
    if callback not in self._buttonCallbacks:
      return False
    self._buttonCallbacks.remove(callback)
    return True

  def show(self):
    """Show the dialog."""
    super(Dialog, self).show()
    # make sure the dialog is always on top and doesn't steal focus. If _position is set, move the dialog to that position.
    self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
    self.activateWindow()
    self.raise_()
    if self._windowPosition is not None:
      self.move(self._windowPosition)
    if self._windowSize is not None:
      self.resize(self._windowSize)
    super(Dialog, self).show()

  def hide(self):
    """Hide the dialog."""
    # get the current position of the dialog
    self._windowPosition = self.pos()
    self._windowSize = super(Dialog, self).size()
    super(Dialog, self).hide()

  def close(self):
    """Close the dialog."""
    # get the current position of the dialog
    self._windowPosition = self.pos()
    self._windowSize = super(Dialog, self).size()
    super(Dialog, self).close()

  def _onDestroy(self):
    """Called when the dialog is destroyed. Unregisters all callbacks."""
    self._buttonCallbacks.clear()
    self._closeCallbacks.clear()

  def _onButtonClicked(self, button: QPushButton):
    """Called when a button is clicked. Calls all registered callbacks for that button."""
    buttonId = self._dialogButtonBox.standardButton(button)
    for callback in self._buttonCallbacks:
      callback(buttonId)

  def _createButtonBox(self, buttons: Tuple[StandardButton,...]) -> QDialogButtonBox:
    """Create a button box with the specified buttons."""
    buttonBox = QDialogButtonBox()
    added = []
    for standardButton in buttons:
      if standardButton in added: continue
      button = buttonBox.addButton(standardButton)
      button.clicked.connect(lambda: self._onButtonClicked(button))
    return buttonBox
  
  def _clear(self):
    i: int
    for i in reversed(range(self.windowLayout.count())): # type: ignore
      it = self.windowLayout.takeAt(i)
      if it.widget() is not None:
        it.widget().deleteLater()
      elif it.layout() is not None:
        it.layout().deleteLater()
      else:
        pass
  
  def _rebuild(self):
    self._clear()
    if self._dialogBody is None:
      self._dialogBody = Dialog._defaultLayout()
    if self._dialogButtonBox is None:
      self._dialogButtonBox = Dialog._defaultButtonBox()
    self.windowLayout.addLayout(self._dialogBody, 1)
    self.windowLayout.addWidget(self._dialogButtonBox, 0, alignment=Qt.AlignBottom)
    self.windowLayout.addSpacing(10)

  @staticmethod
  def _defaultLayout() -> QVBoxLayout:
    body = QVBoxLayout()
    sampleLabel = QLabel("This is a Dialog.\nOverride the 'Dialog.dialogBody' property with your own QVBoxLayout to add your own widgets.")
    sampleLabel.setAlignment(Qt.AlignCenter)
    sampleLabel.setWordWrap(True)
    body.addWidget(sampleLabel)
    # body.addStretch(1)
    return body

  @staticmethod
  def _defaultButtonBox() -> QDialogButtonBox:
    buttonBox = QDialogButtonBox()
    buttonBox.addButton(QDialogButtonBox.Close)
    return buttonBox