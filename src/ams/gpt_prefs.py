from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import (Qt, QTimer, Signal)
from PySide2.QtWidgets import (QAbstractButton, QCheckBox, QComboBox, QDialogButtonBox,
                               QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout, QSlider,
                               QSpinBox, QTableWidget)
from ams.ui.kvp import KeyValueListView, KeyValue
from ams.ui.fields import TextFieldStyle
from . import ai
from . import gpt_window
from .settings import Settings


def TFTHEME():
  return TextFieldStyle(
    font=QtGui.QFont('Source Code Pro', 10),
  )

class GPTPrefsWindow(QtWidgets.QDialog):
  """Preferences window for GPT ChatParams."""
  _completionParams: ai.ChatCompletionParams
  _gptWindow: 'gpt_window.GPTWindow'

  @property
  def completionParams(self):
    return self._completionParams


  eClosedOk = Signal()
  eClosedCancel = Signal()

  def __init__(self, gptWindow: 'gpt_window.GPTWindow', parent=None):
    super().__init__(parent)
    self._settings = Settings.instance()
    self._gptWindow = gptWindow
    self._completionParams = gptWindow.state.completionParams.copy()
    self.setWindowTitle('GPT Preferences')
    self.setMinimumSize(800, 1280)
    self.setMaximumSize(800, 1280)
    # layout items should be 'spaced between' and not 'stretched'
    self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
    self._initUI()

  def _initUI(self):
    """Initialize the UI."""
    self._layout = QVBoxLayout()
    self.setLayout(self._layout)
    self._layout.setStretch(0, 0)
    self._initChatParamOptions()
    self._initButtons()

  def _initChatParamOptions(self):
    from ams.ui.fields import StringField
    from ams.ui.controls import LabelControl, CheckBoxControl, NumberField, Slider, ValueChangedEvent
    def onApiFieldChanged(evt: ValueChangedEvent[str]): self._completionParams._apiKey = evt.newValue
    apiStringField = StringField(text=self._completionParams.apiKey)
    apiStringField.fieldStyle = TFTHEME()
    self._apiField = LabelControl("OpenAI API Key", apiStringField)
    self._apiField.setToolTip("""The OpenAI API key to use for the chat completion. This is required to use any OpenAI functionality.""")
    self._apiField.eValueChanged.connect(onApiFieldChanged)
    self._layout.addWidget(self._apiField)

    self._maxTokensField = CheckBoxControl(LabelControl("Max Tokens", NumberField(minimum=1, maximum=4096, value=self._completionParams.max_tokens, isInteger=True)),
                                           self._completionParams.hasMaxTokens())
    self._layout.addWidget(self._maxTokensField)
    def onMaxTokensChanged(evt: ValueChangedEvent[int]): self._completionParams._max_tokens = evt.newValue
    self._maxTokensField.eValueChanged.connect(onMaxTokensChanged)
    self._maxTokensField.setToolTip("""The maximum number of tokens to generate in the chat completion.
The total length of input tokens and generated tokens is limited by the model's context length. GPT-3 has a context
length of 2048 tokens (roughly 1,500 words)""")
    def onMaxTokensEnabledChanged(evt: ValueChangedEvent[bool]): self._completionParams._max_tokens = self._maxTokensField.value() if evt.newValue else None
    self._maxTokensField.eEnabledChanged.connect(onMaxTokensEnabledChanged)

    self._temperatureSlider = CheckBoxControl(LabelControl("Temperature", Slider(Qt.Horizontal, min=0, max=2, value=self._completionParams.temperature, tickInterval=0.1)),
                                              self._completionParams.hasTemperature())
    self._layout.addWidget(self._temperatureSlider)
    def onTemperatureChanged(evt: ValueChangedEvent[float]): self._completionParams._temperature = evt.newValue
    self._temperatureSlider.eValueChanged.connect(onTemperatureChanged)
    self._temperatureSlider.setToolTip("""Influences the randomness of the chat completion.
Lower values make the chat more predictable, higher values make it more spontaneous. Disable 'Nucleus Sampling' when using this.""")
    def onTemperatureEnabledChanged(evt: ValueChangedEvent[bool]): self._completionParams._temperature = self._temperatureSlider.value() if evt.newValue else None
    self._temperatureSlider.eEnabledChanged.connect(onTemperatureEnabledChanged)

    self._topPField = CheckBoxControl(LabelControl("Nucleus Sampling", Slider(min=0, max=1, value=self._completionParams.top_p, step=0.1)),
                                      self._completionParams.hasTopP())
    self._layout.addWidget(self._topPField)
    def onTopPChanged(evt: ValueChangedEvent[float]): self._completionParams._top_p = evt.newValue
    self._topPField.eValueChanged.connect(onTopPChanged)
    self._topPField.setToolTip("""An alternative to sampling with temperature, called nucleus sampling, where the model
considers the results of the tokens with probability mass. A value of 0.1 means only the tokens comprising the top 10%
probability mass are considered. Disable 'Temperature' when using this.""")
    def onTopPEnabledChanged(evt: ValueChangedEvent[bool]): self._completionParams._top_p = self._topPField.value() if evt.newValue else None
    self._topPField.eEnabledChanged.connect(onTopPEnabledChanged)

    self._nField = CheckBoxControl(LabelControl("Response Choices", Slider(min=1, max=10, value=self._completionParams.n, step=1, isInteger=True)),
                                   self._completionParams.hasN())
    self._layout.addWidget(self._nField)
    def onNChanged(evt: ValueChangedEvent[int]): self._completionParams._n = evt.newValue
    self._nField.eValueChanged.connect(onNChanged)
    self._nField.setToolTip("The number of response choices to generate for the chat completion. Currently only the first response can be viewed.")
    def onNEnabledChanged(evt: ValueChangedEvent[bool]): self._completionParams._n = self._nField.value() if evt.newValue else None
    self._nField.eEnabledChanged.connect(onNEnabledChanged)

    self._frequencyPenaltyField = CheckBoxControl(LabelControl("Frequency Penalty", Slider(min=-2, max=2, value=self._completionParams.frequency_penalty, tickInterval=0.1)),
                                                  self._completionParams.hasFrequencyPenalty())
    self._layout.addWidget(self._frequencyPenaltyField)
    def onFrequencyPenaltyChanged(evt: ValueChangedEvent[float]): self._completionParams._frequency_penalty = evt.newValue
    self._frequencyPenaltyField.eValueChanged.connect(onFrequencyPenaltyChanged)
    self._frequencyPenaltyField.setToolTip("""The higher the frequency penalty, the more likely the model will talk about new topics.
Positive values encourage the model to talk about new topics, while negative values encourage the model to repeat itself.
This parameter has been superseded by `presence_penalty`, which is much more effective. It must be a number between -2.0 and 2.0.""")
    def onFrequencyPenaltyEnabledChanged(evt: ValueChangedEvent[bool]): self._completionParams._frequency_penalty = self._frequencyPenaltyField.value() if evt.newValue else None
    self._frequencyPenaltyField.eEnabledChanged.connect(onFrequencyPenaltyEnabledChanged)

    self._presencePenaltyField = CheckBoxControl(LabelControl("Presence Penalty", Slider(min=-2, max=2, value=self._completionParams.presence_penalty, tickInterval=0.1)),
                                                 self._completionParams.hasPresencePenalty())
    self._layout.addWidget(self._presencePenaltyField)
    def onPresencePenaltyChanged(evt: ValueChangedEvent[float]): self._completionParams._presence_penalty = evt.newValue
    self._presencePenaltyField.eValueChanged.connect(onPresencePenaltyChanged)
    self._presencePenaltyField.setToolTip("""The higher the presence penalty, the less likely the model will repeat itself.
Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood
to talk about new topics. Negative values encourage the model to repeat itself. Must be a number between -2.0 and 2.0.""")
    def onPresencePenaltyEnabledChanged(evt: ValueChangedEvent[bool]): self._completionParams._presence_penalty = self._presencePenaltyField.value() if evt.newValue else None
    self._presencePenaltyField.eEnabledChanged.connect(onPresencePenaltyEnabledChanged)

    self._initLogitBiasTable()

    # app name and version and copyright
    self._layout.addSpacing(5)
    app = QtWidgets.QApplication.instance()
    self._appInfoLabel = QLabel(f'<a href="https://github.com/asorgejr/GPFree">{app.applicationName()} v{app.applicationVersion()}</a> © Anthony Sorge 2023')
    self._appInfoLabel.setTextFormat(Qt.RichText)
    self._appInfoLabel.setOpenExternalLinks(True)
    self._appInfoLabel.setAlignment(Qt.AlignCenter)
    self._layout.addWidget(self._appInfoLabel)

  def _initButtons(self):
    """Initialize the buttons."""
    self._buttonLayout = QHBoxLayout()
    self._layout.addLayout(self._buttonLayout)
    self._initOkButton()
    self._initCancelButton()

  def _initOkButton(self):
    """Initialize the ok button."""
    def onClicked():
      """Update the chat params and close the window."""
      self._gptWindow.state.completionParams = self._completionParams
      # print(f'{self._gptWindow.state.completionParams.toDict()}')
      self._settings.setValue(Settings.KEY_OPENAI_API_KEY(), self._completionParams.apiKey)
      self.eClosedOk.emit()
      self.accept()
    self._okButton = QPushButton('Save')
    self._okButton.clicked.connect(onClicked)
    self._buttonLayout.addWidget(self._okButton)

  def _initCancelButton(self):
    """Initialize the cancel button."""
    self._cancelButton = QPushButton('Cancel')
    def onClicked():
      """Close the window."""
      self.eClosedCancel.emit()
      self.reject()
    self._cancelButton.clicked.connect(onClicked)
    self._buttonLayout.addWidget(self._cancelButton)

  def _initLogitBiasTable(self):
    """Initialize the logit bias table."""
    # if not HAS_TIKTOKEN: return
    self._logitBiasLabel = QtWidgets.QLabel("Word Biases")
    self._layout.addWidget(self._logitBiasLabel)
    self._logitBiasLabel.setToolTip("""Modify the likelihood of specified words appearing in the response.
Add a word to the left column and a number value to the right column.
Values between -100 and 100 are accepted. Positive values increase the probability of the word appearing, while negative
values decrease the probability. Text passed to GPT is tokenized, so there is a possibility that a word will become
multiple tokens. For example, the word 'racecar' is tokenized as 'race' and 'car'. This might be a problem if a word is
composed of tokens which are also common words, in this case the word 'car' is assigned bias whether it is part of the
word 'racecar' or not. See https://platform.openai.com/tokenizer to see how a word is tokenized.""")
    self._logitBiasList = KeyValueListView(self)
    def onListChange(evt):
      """Update the logit bias table."""
      d = {}
      for kvp in self._logitBiasList:
        key = kvp.key
        value = kvp.value
        if key and value:
          try:
            d[key] = float(value)
          except ValueError:
            pass
      self._completionParams.setLogitBiasStrDict(d)
    self._logitBiasList.eListChanged.connect(onListChange)
    self._logitBiasList.setToolTip("Add a word to the left column and a number value to the right column. Double click to edit")
    self._layout.addWidget(self._logitBiasList)

