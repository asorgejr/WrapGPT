from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, Union, TypeVar
from PySide2 import QtCore, QtWidgets, QtGui
# Numeric Parameter controls: QSpinBox, QDoubleSpinBox, QSlider, QDial, QScrollBar


Numeric = Union[int, float]
_Num = (int, float)


_TVal = TypeVar("_TVal", int, float, str, bool, list, tuple, dict, set)
class ValueChangedEvent(Generic[_TVal]):
  """An event that is emitted when the value of a control changes"""
  oldValue: _TVal
  newValue: _TVal

  def __init__(self, oldValue: _TVal, newValue: _TVal):
    self.oldValue = oldValue
    self.newValue = newValue


class AbstractControl:
  """An abstract class for a numeric parameter control"""
  eValueChanged: QtCore.Signal
  """An event that is emitted when the value of the control changes. The callable should take a ValueChangedEvent as its only parameter"""


  def value(self) -> Any:
    """Returns the current value of the control"""
    pass

  def setValue(self, value: Any):
    """Sets the value of the control"""
    pass

  def setDefault(self):
    """Sets the value of the control to its default value"""
    pass

  def setEnabled(self, enabled: bool):
    """Sets whether the control is enabled or not"""
    pass


class DebugWidget(QtWidgets.QWidget):
  """A QWidget which paints its layout as a debug overlay"""
  _layout: QtWidgets.QHBoxLayout
  _label: QtWidgets.QLabel

  _control: AbstractControl

  def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
    super().__init__(parent)

  def paintEvent(self, event: QtGui.QPaintEvent) -> None:
    super().paintEvent(event)
    painter = QtGui.QPainter(self)
    painter.setPen(QtGui.QPen(QtCore.Qt.blue, 2, QtCore.Qt.SolidLine))
    painter.drawRect(self.rect())


class NumberField(AbstractControl, QtWidgets.QWidget):
  """A numeric field that supports floating point values"""
  _layout: QtWidgets.QHBoxLayout

  _numberField: Union[QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox]

  _min: Numeric
  @property
  def min(self) -> Numeric:
    """The minimum value of the number field"""
    return self._min
  @min.setter
  def min(self, value: Numeric):
    self._min = int(value) if self._isInteger else value
    self.setRange(self._min, self._max)

  _max: Numeric
  @property
  def max(self) -> Numeric:
    """The maximum value of the number field"""
    return self._max
  @max.setter
  def max(self, value: Numeric):
    self._max = int(value) if self._isInteger else value
    self.setRange(self._min, self._max)

  _value: Numeric
  @property
  def val(self) -> Numeric:
    """The current value of the number field"""
    return self.value()
  @val.setter
  def val(self, value: Numeric):
    self.setValue(value)

  _step: Numeric
  @property
  def step(self) -> Numeric:
    """The step size of the number field"""
    return self._step
  @step.setter
  def step(self, value: Numeric):
    self._step = int(value) if self._isInteger else value
    self.setSingleStep(self._step)

  _isInteger: bool
  @property
  def integer(self) -> bool:
    """Whether the number field is an integer or not"""
    return self._isInteger

  _decimals: int
  @property
  def decimals(self) -> int:
    """The number of decimal places to display"""
    return self._decimals
  @decimals.setter
  def decimals(self, value: int):
    self._decimals = value
    if not self._isInteger: self.setDecimals(self._decimals)


  eValueChanged = QtCore.Signal(ValueChangedEvent)

  def __init__(self, parent: Optional[QtWidgets.QWidget] = None,
               minimum: Numeric = 0, maximum: Numeric = 100, value: Numeric = 0, step: Numeric = 1,
               isInteger: bool = False, decimals: int = 2):
    if not isinstance(minimum, _Num): raise TypeError("minimum must be a number")
    if not isinstance(maximum, _Num): raise TypeError("maximum must be a number")
    if not isinstance(value, _Num): raise TypeError("value must be a number")
    if not isinstance(step, _Num): raise TypeError("step must be a number")
    if not isinstance(isInteger, bool): raise TypeError("integer must be a bool")
    if not isinstance(decimals, int): raise TypeError("decimals must be an int")
    super().__init__(parent=parent)
    self._layout = QtWidgets.QHBoxLayout(self)
    self._isInteger = isInteger
    value = max(minimum, min(value, maximum))
    if isInteger:
      self._numberField = QtWidgets.QSpinBox(self)
    else:
      self._numberField = QtWidgets.QDoubleSpinBox(self)
      self._numberField.setDecimals(decimals)
    self._numberField.setValue(value)
    self._numberField.setRange(minimum, maximum)
    self._numberField.setSingleStep(step)
    self._layout.addWidget(self._numberField)
    self._min = minimum
    self._max = maximum
    self._step = step
    self._value = value
    self._decimals = decimals
    self._numberField.valueChanged.connect(self._onValueChanged)

  def value(self) -> Numeric:
    """Returns the current value of the number field"""
    v = self._numberField.value()
    self._value = int(v) if self._isInteger else v
    return self._value

  def setValue(self, value: Numeric):
    """Sets the value of the number field"""
    self._numberField.setValue(int(value) if self._isInteger else value)

  def setDefault(self):
    """Sets the value of the number field to its default value (minimum)"""
    self.setValue(self._min)

  def setRange(self, min: Numeric, max: Numeric):
    """Sets the range of the number field"""
    self._numberField.setRange(min, max)

  def setSingleStep(self, step: Numeric):
    """Sets the step size of the number field"""
    self._numberField.setSingleStep(step)

  def setDecimals(self, decimals: int):
    """Sets the number of decimals of the number field"""
    if not self._isInteger:
      self._numberField.setDecimals(decimals)

  def setKeyboardTracking(self, tracking: bool):
    """Sets whether the number field should emit the eValueChanged signal while typing"""
    self._numberField.setKeyboardTracking(tracking)

  def keyboardTracking(self) -> bool:
    """Returns whether the number field emits the eValueChanged signal while typing"""
    return self._numberField.keyboardTracking()

  def setEnabled(self, enabled: bool):
    self._numberField.setEnabled(enabled)

  def _onValueChanged(self, value: Numeric):
    """Emits the eValueChanged signal"""
    oldValue = int(self._value) if self._isInteger else self._value
    self._value = int(value) if self._isInteger else value
    self.eValueChanged.emit(ValueChangedEvent(oldValue, self._value))



class Slider(AbstractControl, QtWidgets.QWidget):
  """A slider that supports floating point values"""
  from PySide2.QtWidgets import QSlider
  _RATIO: Numeric = 1000.0

  _layout: QtWidgets.QHBoxLayout

  _numberField: NumberField

  _slider: QSlider
  @property
  def slider(self) -> QSlider:
    """The slider"""
    return self._slider

  _min: Numeric
  @property
  def min(self) -> Numeric:
    """The minimum value of the slider"""
    return self._min
  @min.setter
  def min(self, value: Numeric):
    self._min = int(value) if self._isInteger else value
    self.setRange(self._min, self._max)

  _max: Numeric
  @property
  def max(self) -> Numeric:
    """The maximum value of the slider"""
    return self._max
  @max.setter
  def max(self, value: Numeric):
    self._max = int(value) if self._isInteger else value
    self.setRange(self._min, self._max)

  _value: Numeric
  @property
  def val(self) -> Numeric:
    """The current value of the slider"""
    return self.value()
  @val.setter
  def val(self, value: Numeric):
    self.setValue(value)

  _step: Numeric
  @property
  def step(self) -> Numeric:
    """The step size of the slider"""
    return self._step
  @step.setter
  def step(self, value: Numeric):
    self._step = int(value) if self._isInteger else value
    self.setSingleStep(self._step)

  _isInteger: bool
  @property
  def isInteger(self) -> bool:
    """Whether the slider should only support integer values"""
    return self._isInteger

  _decimals: int
  @property
  def decimals(self) -> int:
    """The number of decimals of the slider"""
    return self._decimals
  @decimals.setter
  def decimals(self, value: int):
    self._decimals = value
    if not self._isInteger:
      self.setDecimals(self._decimals)

  eValueChanged = QtCore.Signal(ValueChangedEvent)

  def __init__(self, orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal,
               parent: Optional[QtWidgets.QWidget] = None,
               min: Numeric = 0.0, max: Numeric = 1.0, value: Numeric = 0.0, step: Numeric = 1.0,
               isInteger: bool = False, decimals: int = 2,
               tickPosition: QSlider.TickPosition = QSlider.NoTicks,
               tickInterval: Numeric = 0.1):
    if not isinstance(min, _Num): raise TypeError(f"min must be a number. Got {type(min)}")
    if not isinstance(max, _Num): raise TypeError(f"max must be a number. Got {type(max)}")
    if not isinstance(value, _Num): raise TypeError(f"value must be a number. Got {type(value)}")
    if not isinstance(step, _Num): raise TypeError(f"step must be a number. Got {type(step)}")
    if not isinstance(isInteger, bool): raise TypeError(f"isInteger must be a boolean. Got {type(isInteger)}")
    if not isinstance(decimals, int): raise TypeError(f"decimals must be an integer. Got {type(decimals)}")
    if not isinstance(tickInterval, _Num): raise TypeError(f"tickInterval must be a number. Got {type(tickInterval)}")
    super().__init__(parent)
    if isInteger: self._RATIO = 1
    else: self._RATIO = Slider._RATIO
    self._layout = QtWidgets.QHBoxLayout(self)
    self._isInteger = isInteger
    self.setLayout(self._layout)
    self._numberField = NumberField(self, minimum=min, maximum=max, value=value, step=step, isInteger=isInteger, decimals=decimals)
    self._numberField.setRange(min, max)
    self._numberField.setValue(value)
    self._numberField.setSingleStep(step)
    self._numberField.setDecimals(decimals)
    self._numberField.setKeyboardTracking(False)
    self._layout.addWidget(self._numberField)
    self._layout.addSpacing(10)
    self._slider = QtWidgets.QSlider(orientation, self)
    self._layout.addWidget(self._slider)
    self._slider.setFixedHeight(40)
    self._layout.setStretch(0, 0)
    self._layout.setContentsMargins(0, 0, 0, 0)
    self._layout.setSpacing(0)
    self._min = min
    self._max = max
    self._value = value
    self._step = step
    self.setRange(min, max)
    self.setValue(value)
    self.setSingleStep(step)
    self.setTickPosition(tickPosition)
    self.setTickInterval(tickInterval)

    def numberFieldValueChanged(evt: ValueChangedEvent[Numeric]):
      self.eValueChanged.emit(evt)  # type: ignore
      self._slider.blockSignals(True)
      val = evt.newValue
      self._slider.setValue(self._sliderValue(val))
      self._slider.blockSignals(False)
    self._numberField.eValueChanged.connect(numberFieldValueChanged)

    def sliderValueChanged(val):
      val = self._actualValue(val)
      evt = ValueChangedEvent(self._value, self.value())
      self.eValueChanged.emit(evt)  # type: ignore
      self._numberField.blockSignals(True)
      self._numberField.setValue(val)
      self._numberField.blockSignals(False)
    self._slider.valueChanged.connect(sliderValueChanged)

  def setValue(self, value: Numeric) -> None:
    self._value = int(value) if self._isInteger else value
    self._numberField.setValue(value)
    self._slider.setValue(self._sliderValue(value))

  def value(self) -> Numeric:
    v = self._numberField.value()
    self._value = int(v) if self._isInteger else v
    return self._value

  def setDefault(self):
    """Set the value to the default value (minimum)"""
    self.setValue(self._min)

  def setEnabled(self, enabled: bool):
    self._numberField.setEnabled(enabled)
    self._slider.setEnabled(enabled)

  def setRange(self, min: Numeric, max: Numeric) -> None:
    self._min = int(min) if self._isInteger else min
    self._max = int(max) if self._isInteger else max
    self._numberField.setRange(min, max)
    self._slider.setRange(self._sliderValue(min), self._sliderValue(max))

  def setSingleStep(self, step: Numeric) -> None:
    self._slider.setSingleStep(self._sliderValue(step))

  def setSliderPosition(self, value: Numeric) -> None:
    self._slider.setSliderPosition(self._sliderValue(value))

  def sliderPosition(self) -> Numeric:
    return self._actualValue(self._slider.sliderPosition())

  def minimum(self) -> Numeric:
    return self._min

  def maximum(self) -> Numeric:
    return self._max

  def singleStep(self) -> Numeric:
    return self._step

  def setTickInterval(self, ti: Numeric) -> None:
    self._slider.setTickInterval(self._sliderValue(ti))

  def tickInterval(self) -> Numeric:
    return self._actualValue(self._slider.tickInterval())

  def setTickPosition(self, position: QSlider.TickPosition) -> None:
    self._slider.setTickPosition(position)

  def tickPosition(self) -> QSlider.TickPosition:
    return self._slider.tickPosition()

  def _sliderValue(self, value: Numeric) -> int:
    """Scales the value to the slider's range.
    int(value * Slider._RATIO)"""
    return int(value * self._RATIO)

  def _actualValue(self, value: int) -> Numeric:
    """Scales the slider's value to the actual range.
    value / Slider._RATIO"""
    return value / self._RATIO




class LabelControl(AbstractControl, QtWidgets.QWidget):
  """A simple control with a label"""
  _layout: QtWidgets.QHBoxLayout
  @property
  def layout(self) -> QtWidgets.QHBoxLayout:
    """The layout of the control"""
    return self._layout

  _label: QtWidgets.QLabel
  @property
  def label(self) -> str:
    """The label of the control"""
    return self._label.text()
  @label.setter
  def label(self, value: str):
    if not isinstance(value, str): raise TypeError(f"label must be a string. Got {type(value)}")
    self._label.setText(value)

  _control: AbstractControl
  @property
  def control(self) -> AbstractControl:
    """The control"""
    return self._control

  eValueChanged = QtCore.Signal(object)

  def __init__(self, label: str, control: AbstractControl, parent: Optional[QtWidgets.QWidget] = None):
    if not isinstance(label, str): raise TypeError(f"label must be a string. Got {type(label)}")
    if not isinstance(control, AbstractControl): raise TypeError(f"control must be an AbstractControl. Got {type(control)}")
    super().__init__(parent)
    self._layout = QtWidgets.QHBoxLayout()
    self.setLayout(self._layout)
    self._label = QtWidgets.QLabel(label)
    self._label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self._layout.addWidget(self._label)
    self._control = control
    self._layout.addWidget(self._control)
    self._control.eValueChanged.connect(self.eValueChanged.emit)
    self._layout.setContentsMargins(0, 0, 0, 0)

  def setValue(self, value: _TVal) -> None:
    self._control.setValue(value)

  def value(self) -> _TVal:
    return self._control.value()

  def setDefault(self) -> None:
    self._control.setDefault()

  def setLabelVisible(self, visible: bool) -> None:
    self._label.setVisible(visible)

  def setEnabled(self, enabled: bool) -> None:
    self._control.setEnabled(enabled)





class CheckBoxControl(AbstractControl, QtWidgets.QWidget):
  """A simple control with a checkbox and a LabelControl. The LabelControl is enabled when the checkbox is checked."""
  eValueChanged = QtCore.Signal(ValueChangedEvent)
  eEnabledChanged = QtCore.Signal(ValueChangedEvent)

  def __init__(self, control: LabelControl, isChecked=True, parent=None):
    super().__init__(parent)
    self._layout = QtWidgets.QHBoxLayout()
    self.setLayout(self._layout)
    self.checkBox = QtWidgets.QCheckBox()
    self._layout.addWidget(self.checkBox)
    self.checkBox.setChecked(isChecked)
    self.checkBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self.control = control
    self.control.setEnabled(isChecked)
    self._layout.addWidget(self.control)
    def onValueChanged(evt: ValueChangedEvent): self.eValueChanged.emit(evt)
    self.control.eValueChanged.connect(onValueChanged)
    def onEnabledChanged(val: int):
      self.control.setEnabled(bool(val))
      self.eEnabledChanged.emit(ValueChangedEvent(not bool(val), bool(val)))
    self.checkBox.stateChanged.connect(onEnabledChanged)
    self._layout.setContentsMargins(0, 0, 0, 0)

  def setValue(self, value: _TVal) -> None:
    self.control.setValue(value)

  def value(self) -> _TVal:
    return self.control.value()

  def setDefault(self) -> None:
    self.control.setDefault()

  def setLabelVisible(self, visible: bool) -> None:
    self.control.setLabelVisible(visible)

  def setChecked(self, checked: bool) -> None:
    self.checkBox.setChecked(checked)

  def isChecked(self) -> bool:
    return self.checkBox.isChecked()

  def setToolTip(self, text: str) -> None:
    self.control.setToolTip(text)
