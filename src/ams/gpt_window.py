import ams.ui.window as window
import ams.ui.fields as fields
import ams.ui.controls as controls
import ams.ui.themes as themes
from .ai import Chat, Message, PartialMessage, ChatCompletionParams, Response, ChatEntry, getModels
from . import gpt_prefs
from . import settings
from .settings import Settings

import copy
from dataclasses import dataclass, field
from typing import *
import openai
from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import (Qt, QTimer, Signal)
from PySide2.QtWidgets import (QAbstractButton, QCheckBox, QComboBox, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout)

HAS_TIKTOKEN = True
try:
  import tiktoken
except ImportError:
  HAS_TIKTOKEN = False

# # get the openai api key from OPENAI_API_KEY env var
# api_key = os.getenv('OPENAI_API_KEY')
# if not api_key:
#   errmsg = \
# f'''The OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key.
# You can get your API key from https://platform.openai.com/account/api-keys'''
#   raise ValueError(errmsg)
# openai.api_key = api_key
# del api_key  # definitely don't let this one hang around


DEFAULT_MODEL = 'gpt-3.5-turbo'





@dataclass(frozen=True)
class ButtonEvent:
  """A button event, which contains the button that was pressed."""
  button: QAbstractButton
  """The button that was pressed."""
  data: Dict[str, Any] = field(default_factory=dict)
  """The data associated with the button."""




class GPTState:
  _model: str
  @property
  def model(self) -> str:
    """The model to use for GPT chat."""
    return self._model
  @model.setter
  def model(self, value: str):
    if not isinstance(value, str): raise TypeError(f'Expected str, got {type(value)}')
    self._model = value

  _chatParams: ChatCompletionParams
  @property
  def completionParams(self) -> ChatCompletionParams:
    """The chat parameters to use for GPT chat."""
    return self._chatParams
  @completionParams.setter
  def completionParams(self, value: ChatCompletionParams):
    if not isinstance(value, ChatCompletionParams): raise TypeError(f'Expected ChatParams, got {type(value)}')
    self._chatParams = value

  _window: Optional['GPTWindow']
  @property
  def window(self) -> Optional['GPTWindow']:
    """The GPT window."""
    return self._window
  @window.setter
  def window(self, value: Optional['GPTWindow']):
    if value and not isinstance(value, GPTWindow): raise TypeError(f'Expected GPTWindow, got {type(value)}')
    self._window = value

  _chat: Chat = Chat()
  @property
  def chat(self) -> Chat:
    """The GPT chat."""
    return self._chat
  @chat.setter
  def chat(self, value: Chat):
    if not isinstance(value, Chat): raise TypeError(f'Expected Chat, got {type(value)}')
    self._chat = value

  def __init__(self, model: str, chatParams: Optional[ChatCompletionParams] = None, window: Optional['GPTWindow'] = None, chat: Optional[Chat] = None):
    self.model = model
    self.completionParams = chatParams if chatParams else ChatCompletionParams(model=model, apiKey=str(Settings.instance().value(Settings.KEY_OPENAI_API_KEY(), '')))
    self.window = window
    self.chat = chat if chat else Chat()

  @staticmethod
  def Default() -> 'GPTState':
    """Get the default GPT state."""
    return GPTState(DEFAULT_MODEL)

  def copy(self) -> 'GPTState':
    """Returns a GPTState with deep copies of all mutable members of this GPTState, except for the window which is a weak reference."""
    chat = copy.deepcopy(self.chat)
    chatParams = self.completionParams.copy()
    return GPTState(model=self.model, chatParams=chatParams, window=self.window, chat=chat)






def TFTHEME():
  return fields.TextFieldStyle(
    font=fields.QFont('Source Code Pro', 10),
    caretType=fields.CaretType.BLOCK,
  )





class ResultThread(QtCore.QThread):
  """A thread that attempts to run a function, and if it takes too long, it kills the thread and raises an exception."""
  _func: Callable
  _args: Tuple[Any, ...]
  _kwargs: Dict[str, Any]
  timeout: float
  exception: Optional[Exception]
  result: Any

  eTimeout = Signal(TimeoutError)
  eFinished = Signal(object)

  def __init__(self, target: Callable, args: Tuple[Any, ...] = (), kwargs: Optional[Dict[str, Any]] = None):
    """Create a new TimeoutThread.

    Args:
      target: The callable to run.
      args: The arguments to pass to the function.
      kwargs: The keyword arguments to pass to the function.
    """
    super().__init__()
    self._func = target
    self._args = args
    self._kwargs = kwargs if kwargs else {}
    self.exception = None
    self.result = None

  def run(self):
    self.result = self._func(*self._args, **self._kwargs)
    self.eFinished.emit(self.result)






class GPTWindow(window.Window[QVBoxLayout]):
  """A dialog window for interacting with OpenAI GPT models."""
  _layout: QVBoxLayout
  _manageSessionState: bool
  _settingsDialog: gpt_prefs.GPTPrefsWindow

  # region Properties
  _state: GPTState
  @property
  def state(self) -> GPTState:
    """The state of the GPT session."""
    return self._state

  _models: List[str]
  @property
  def models(self) -> List[str]:
    """The models available for use."""
    return self._models
  @models.setter
  def models(self, value: List[str]):
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value): raise TypeError(f'Expected a list of strings, but got {value}')
    self._models = value

  _modelMenu: QComboBox
  @property
  def modelMenu(self) -> QComboBox:
    """The model menu, which allows the user to select a GPT chat model."""
    return self._modelMenu

  _roleMenu: QComboBox
  @property
  def roleMenu(self) -> QComboBox:
    """The role menu, which allows the user to select a role for the GPT chat."""
    return self._roleMenu

  _promptField: fields.TextField
  @property
  def promptField(self) -> fields.TextField:
    """The prompt field, which allows the user to enter a prompt to send to the GPT API."""
    return self._promptField

  _responseField: fields.TextField
  @property
  def responseField(self) -> fields.TextField:
    """The response field, which displays the response from the GPT API."""
    return self._responseField

  _controlButtons: QHBoxLayout
  @property
  def controlButtons(self) -> QHBoxLayout:
    """The control buttons, which contain the buttons for controlling which Chat Entry is being displayed."""
    return self._controlButtons

  _buttonBox: QHBoxLayout
  @property
  def buttonBox(self) -> QHBoxLayout:
    """The button box, which contains the buttons for interaction with the GPT API. Buttons should only be added and not removed."""
    return self._buttonBox

  _submitBtn: QPushButton
  @property
  def submitBtn(self) -> QPushButton:
    """The submit button, which submits the prompt to the GPT API."""
    return self._submitBtn

  _displayRespChk: QCheckBox
  @property
  def displayRespChk(self) -> QCheckBox:
    """The display response checkbox, which determines whether the field for displaying the response from the GPT API is visible."""
    return self._displayRespChk

  # endregion Properties
  SUBMIT_BUTTON_TOOLTIP = 'Submit the prompt to GPT and display the response.'
  MODEL_MENU_TOOLTIP = 'The GPT model to use for the chat.'
  DISABLED_NOAPIKEY_TOOLTIP = 'You must set your OpenAI API key in the preferences to use this feature.'
  # region Signals

  eResponseReceived: Signal = Signal(dict)
  """Signal emitted when a response has finished being received from the GPT API."""

  eButtonPressed: Signal = Signal(QAbstractButton)
  """Signal emitted when any button is pressed."""

  # endregion Signals


  def __init__(self, parent=None, models: Optional[List[str]] = None, state: Optional[GPTState] = None,
               title: str = 'GPT', size: Tuple[int, int] = (1024, 900)):
    """Create a new GPTWindow instance.

    Args:
      models ([str,...] = ['gpt-3.5-turbo']): A list of GPT models to display in the model menu.
      state (GPTState = None): The state to initialize the window with.
      title (str = 'GPT'): The title of the window.
      size ((int, int) = (800, 600)): The size of the window
    """
    # validate arguments
    if not models: models = []
    if not isinstance(models, list): raise TypeError('models must be a list of strings.')
    if not all(isinstance(model, str) for model in models): raise TypeError('models must be a list of strings.')
    if not isinstance(title, str): raise TypeError('title must be a string.')
    if not isinstance(size, tuple): raise TypeError('size must be a tuple of integers.')
    if state and not isinstance(state, GPTState): raise TypeError('state must be an instance of GPTState.')
    elif not state:
      state = GPTState(model=DEFAULT_MODEL, window=self)


    # initialize super
    app = QtWidgets.QApplication.instance()
    w, h = min(size[0], app.desktop().screenGeometry().width()), min(size[1], app.desktop().screenGeometry().height())
    super().__init__(parent, layout=QVBoxLayout(), title=app.applicationName(), size=(w, h))

    # initialize self
    self._settings = Settings.instance()
    self._state = state.copy() if isinstance(state, GPTState) else GPTState(model=DEFAULT_MODEL, window=self)
    if not isinstance(self._state, GPTState): raise TypeError('state must be an instance of GPTState.')
    self._state.window = self
    self._models = models

    self._settingsDialog = gpt_prefs.GPTPrefsWindow(self)
    self._settingsDialog.eClosedOk.connect(self._onSettingsDialogClosedOk)

    self._hasApiKey: bool = self._settings.validApiKey

    # set up the window
    # set style
    self.setPalette(themes.DarkPalette())
    self._initUi()
    self._fieldsFromChatEntry(self._state.chat.current)
    self._checkApiKey()

  def _initUi(self):
    self._initMenus()
    self._initInputFields()
    self._initLoadingIndicator()
    self._initControlButtons()
    self._initActionButtons()
    self.windowLayout.setContentsMargins(5, 5, 5, 5)

  def _initMenus(self):
    self._modelRoleMenusContainer = QHBoxLayout()
    self.windowLayout.addLayout(self._modelRoleMenusContainer)
    self._modelMenuLabel = QLabel('Model:')
    self._modelMenuLabel.setFixedWidth(80)
    self._modelMenuLabel.setToolTip('The GPT model to use for the chat.')
    self._modelRoleMenusContainer.addWidget(self._modelMenuLabel)
    self._modelMenu = QComboBox()
    self._modelMenu.addItems(self.models)
    self._modelMenu.setToolTip(self.MODEL_MENU_TOOLTIP)
    self._modelMenu.currentTextChanged.connect(self._onModelChanged)
    self._modelRoleMenusContainer.addWidget(self._modelMenu)
    self._modelRoleMenusContainer.addSpacing(10)
    self._roleMenuLabel = QLabel('Role:')
    self._roleMenuLabel.setFixedWidth(60)
    self._roleMenuLabel.setToolTip("The role of the prompt, which affects the behavior of GPT responses. In most cases, you should leave this as 'user'.")
    self._modelRoleMenusContainer.addWidget(self._roleMenuLabel)
    self._roleMenu = QComboBox()
    self._roleMenu.setFixedWidth(140)
    self._roleMenu.addItems(['user', 'system'])
    self._roleMenu.setToolTip("The role of the prompt, which affects the behavior of GPT responses. In most cases, you should leave this as 'user'.")
    # connect the role menu's currentTextChanged signal to the onRoleChanged slot
    self._roleMenu.currentTextChanged.connect(self._onRoleChanged)
    self._modelRoleMenusContainer.addWidget(self._roleMenu)

  def _initInputFields(self):
    self._promptField = fields.TextField()
    self._promptField.fieldStyle = TFTHEME()
    self._promptField.setPlaceholderText('Prompt')
    # size hint is half the size of fieldsContainer
    self._promptField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # connect the prompt field's textChanged signal to the onPromptChanged slot
    self._promptField.eValueChanged.connect(self._onPromptChanged)  # type: ignore
    self._promptField.setObjectName('promptField')
    self.windowLayout.addWidget(self._promptField)
    self.windowLayout.addSpacing(5)
    self._responseField = fields.TextField()
    self._responseField.fieldStyle = TFTHEME()
    self._responseField.setPlaceholderText('Response')
    self._responseField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self._responseField.setReadOnly(True)
    self._responseField.setObjectName('responseField')
    self.windowLayout.addWidget(self._responseField)

  def _initLoadingIndicator(self):
    self._loadingPrompt = QLabel('Please wait...')
    self.windowLayout.addWidget(self._loadingPrompt)
    self._loadingIndicator = QProgressBar()
    self._loadingIndicator.setRange(0, 0)
    self.windowLayout.addWidget(self._loadingIndicator)
    self._showLoadingIndicator(False)

  def _initControlButtons(self):
    self._controlButtons = QHBoxLayout()
    self.windowLayout.addLayout(self._controlButtons)
    self._controlButtons.addStretch(1)

    self._upButton = QPushButton('↑')
    self._controlButtons.addWidget(self._upButton)
    self._upButton.clicked.connect(self._onUpButton)
    self._upButton.setEnabled(False)
    self._upButton.setToolTip('Go up to the previous prompt in the chat history.')

    self._downButton = QPushButton('↓')
    self._controlButtons.addWidget(self._downButton)
    self._downButton.clicked.connect(self._onDownButton)
    self._downButton.setEnabled(False)
    self._downButton.setToolTip('Go down to the next prompt in the chat history.')

    self._leftButton = QPushButton('←')
    self._controlButtons.addWidget(self._leftButton)
    self._leftButton.clicked.connect(self._onLeftButton)
    self._leftButton.setEnabled(False)
    self._leftButton.setToolTip('Go to the previous edit of this prompt.')

    self._rightButton = QPushButton('→')
    self._controlButtons.addWidget(self._rightButton)
    self._rightButton.clicked.connect(self._onRightButton)
    self._rightButton.setEnabled(False)
    self._rightButton.setToolTip('Go to the next edit of this prompt.')

  def _initActionButtons(self):
    self._buttonBox = QHBoxLayout()
    self.windowLayout.addLayout(self._buttonBox)
    # self._buttonBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    self._settingsBtn = QPushButton('Settings')
    self._buttonBox.addWidget(self._settingsBtn, stretch=0, alignment=Qt.AlignLeft)
    self._settingsBtn.clicked.connect(self._onSettingsButton)
    self._settingsBtn.setToolTip('Open the settings dialog.')

    self._clearBtn = QPushButton('Clear Chat History')
    self._buttonBox.addWidget(self._clearBtn, stretch=1, alignment=Qt.AlignLeft)
    self._clearBtn.clicked.connect(self._onClearButton)
    self._clearBtn.setToolTip('Clear all prompts and responses from the chat history.')

    self._stopBtn = QPushButton('Stop')
    self._buttonBox.addWidget(self._stopBtn, stretch=0, alignment=Qt.AlignRight)
    self._stopBtn.clicked.connect(self._onStopButton)
    self._stopBtn.setToolTip('Stop GPT from responding or cancel the submission.')

    self._submitBtn = QPushButton('Submit')
    self._buttonBox.addWidget(self._submitBtn, stretch=0, alignment=Qt.AlignRight)
    self._submitBtn.clicked.connect(self._onSubmitButton)
    self._submitBtn.setToolTip('Submit the prompt to GPT and display the response.')

    # self._displayRespChk = QCheckBox('Display Response')
    # self._displayRespChk.setChecked(True)
    # self._displayRespChk.stateChanged.connect(self._onDisplayRespChk)
    # self._buttonBox.addButton(self._displayRespChk, QDialogButtonBox.ActionRole)

  def _onButtonPressed(self, button: QAbstractButton):
    self.eButtonPressed.emit(button)  # type: ignore

  def _onPromptChanged(self, e: controls.ValueChangedEvent[str]):
    # if self.state.chat.cursor != self.state.chat.current:  # reject the change
    #   self._promptField.blockSignals(True)
    #   self._promptField.setText(self.state.chat.current.prompt.content)
    #   self._promptField.blockSignals(False)
    self._state.chat.current.prompt.content = e.newValue

  def _showLoadingIndicator(self, show: bool):
    self._loadingPrompt.setHidden(not show)
    self._loadingIndicator.setHidden(not show)

  def _onDisplayRespChk(self, checked: bool):
    self._responseField.setHidden(not checked)

  def _onResponseCompleted(self, apiResponse: Union[dict, list], setResponseField: bool = True):
    response: Response
    if isinstance(apiResponse, dict):
      response = Response.FromApiResponse(apiResponse)
    else:
      response = Response.FromApiResponses(apiResponse)
    # message = apiResponse['choices'][0]['message']
    respMessage: Message = response.choices[0].toMessage()
    self.state.chat.current.response = response
    text = respMessage.content
    if setResponseField:
      self._responseField.setText(text)
    self.eResponseReceived.emit(apiResponse)  # type: ignore
    self._showLoadingIndicator(False)
    if self.state.chat.current.isDefaultContent():  # a listener already added a descendant chat entry during emit
      self._checkDisableControlButtons()
      return
    self.state.chat.addDescendant(Message(role='user', content=''))
    self._checkDisableControlButtons()

  def _submitPrompt(self, message: Message, model: str):
    self._modelMenu.setDisabled(True)
    self._showLoadingIndicator(True)
    self._responseField.clear()
    if self.state.chat.isEditable():
      self.state.chat.current.prompt.role = message.role
      self.state.chat.current.prompt.content = message.content
    else:
      self.state.chat.addSibling(message)
    messages = self.state.chat.current.messages()
    self.state.completionParams.messages = messages

    def task():
      response: Any = openai.ChatCompletion.create(**self.state.completionParams.toDict())
      return response

    def streamTask():
      response = task()
      results = []
      for chunk in response:
        choice = chunk['choices'][0]
        delta = choice['delta']
        if 'content' not in delta:
          continue
        text = delta['content']
        self._responseField.insertPlainText(text)
        results.append(chunk)
      response = results
      return response

    def afterTask(response):
      self._onResponseCompleted(response)
      self._showLoadingIndicator(False)
      self._timer.stop()
    # task() will run with a 15 second timeout
    self._timer = QTimer()
    self._timer.setSingleShot(True)
    self._thread = ResultThread(target=streamTask if self.state.completionParams.stream else task)
    def onTimeout():
      self._thread.terminate()
      self._showLoadingIndicator(False)
      md = QtWidgets.QErrorMessage(self)
      md.setWindowTitle('Request Timed Out')
      md.showMessage('The request timed out.')
      md.exec_()
    self._thread.eFinished.connect(afterTask)
    self._timer.timeout.connect(onTimeout)
    self._timer.start(30000)
    self._thread.start()


  def _onSubmitButton(self):
    """Submit the prompt to the selected model."""
    # get the selected model
    hasConnection = Settings.hasInternetConnection()
    if not hasConnection:
      settings.showNoInternetConnectionWarning()
      return
    if not self._settings.validApiKey:
      settings.showNoApiKeyWarning()
      return
    model = self.modelMenu.currentText()
    role = self.roleMenu.currentText()
    # get the prompt
    prompt = self.promptField.toPlainText()
    if self.state.chat.cursor != self.state.chat.current:  # edited message becomes new sibling in chat
      self.state.chat.addSibling(Message(role, prompt))
    message = Message(role, prompt)
    # submit the prompt
    self._submitPrompt(message, model)

  def submitMessage(self, message: Message, displayPrompt: bool = True, displayResult: bool = True):
    """Submits a prompt to the GPT API, bypassing the UI.

    Args:
      message: The prompt to submit.
      displayPrompt: Whether to display the prompt in the prompt field.
      displayResult: Whether to display the result in the response field."""
    if displayPrompt:
      self.promptField.setText(message.content)
    self._submitPrompt(message, self.state.model)

  def submit(self):
    """Submits whatever is in the prompt field."""
    self._onSubmitButton()

  def _onClearButton(self):
    """Clear the chat history."""
    self.state.chat.clear()
    self.promptField.clear()
    self.responseField.clear()
    self._modelMenu.setDisabled(False)
    self._checkDisableControlButtons()

  def clearHistory(self):
    """Clear the chat history."""
    self._onClearButton()

  def _onStopButton(self):
    """Stop the current request."""
    try:
      self._timer.stop()
      self._thread.terminate()
      self._showLoadingIndicator(False)
    except AttributeError:
      pass

  def close(self):
    """Close the dialog."""
    self.state.chat.current.prompt.content = self._promptField.toPlainText()
    self._updateState()
    super().close()

  def _onRoleChanged(self, role):
    """Change the role of the current chat entry."""
    print('role changed to', role)
    if self.state.chat.cursor != self.state.chat.current:  # reject the change
      print('rejecting role change')
      return
    self.state.chat.current.prompt.role = role

  def _onModelChanged(self, model: str):
    """Change the model."""
    self.state.model = model

  def _checkDisableControlButtons(self):
    """Check if any control buttons should be disabled."""
    if self.state.chat.canMoveUp(): self._upButton.setEnabled(True)
    else: self._upButton.setEnabled(False)
    if self.state.chat.canMoveDown(): self._downButton.setEnabled(True)
    else: self._downButton.setEnabled(False)
    if self.state.chat.canMoveLeft(): self._leftButton.setEnabled(True)
    else: self._leftButton.setEnabled(False)
    if self.state.chat.canMoveRight(): self._rightButton.setEnabled(True)
    else: self._rightButton.setEnabled(False)

  def _fieldsFromChatEntry(self, entry: ChatEntry):
    """Update the prompt and response fields from a chat entry."""
    # prevent signals from being emitted
    self.promptField.blockSignals(True)
    self.responseField.blockSignals(True)
    self.roleMenu.blockSignals(True)
    # update the fields
    self.promptField.setText(entry.prompt.content)
    if len(entry.response.choices) == 0: return
    choice: Union[Message, PartialMessage] = entry.response.choices[0]
    self.responseField.setText(choice.toMessage().content)
    self.roleMenu.setCurrentIndex(0 if entry.prompt.role == 'user' else 1)
    # allow signals to be emitted
    self.promptField.blockSignals(False)
    self.responseField.blockSignals(False)
    self.roleMenu.blockSignals(False)

  def _onUpButton(self):
    """Go up one entry in the chat history."""
    self.state.chat.up()
    self._fieldsFromChatEntry(self.state.chat.cursor)
    self._checkDisableControlButtons()
    self._onButtonPressed(self._upButton)

  def _onDownButton(self):
    """Go down one entry in the chat history."""
    self.state.chat.down()
    self._fieldsFromChatEntry(self.state.chat.cursor)
    self._checkDisableControlButtons()
    self._onButtonPressed(self._downButton)

  def _onLeftButton(self):
    """Go left one entry in the chat history."""
    self.state.chat.left()
    self._fieldsFromChatEntry(self.state.chat.cursor)
    self._checkDisableControlButtons()
    self._onButtonPressed(self._leftButton)

  def _onRightButton(self):
    """Go right one entry in the chat history."""
    self.state.chat.right()
    self._fieldsFromChatEntry(self.state.chat.cursor)
    self._checkDisableControlButtons()
    self._onButtonPressed(self._rightButton)

  def _resizeFields(self):
    # specifically the prompt/response fields
    # get height of all items in windowLayout which aren't the prompt/response fields
    height = 0
    for i in range(self.windowLayout.count()):
      item = self.windowLayout.itemAt(i)
      # skip if item is prompt/response field
      if item.widget() in [self._promptField, self._responseField]: continue
      # add height of item to height
      height += item.geometry().height()
    height = max(80, min(height, self.geometry().height()))
    # force sizehint height of fields to 1/2 of the remaining window height
    self._promptField.setFixedHeight(int(height/2))
    self._responseField.setFixedHeight(int(height/2))
    # resize the prompt and response fields

  def resizeEvent(self, event):
    """Resize the prompt and response fields."""
    # self._resizeFields()
    super().resizeEvent(event)

  def _checkApiKey(self):
    """Check if the API key is valid."""
    if self._settings.validApiKey:
      models = getModels(['gpt'])
      self._modelMenu.clear()
      self._modelMenu.addItems(models)
      self._modelMenu.setToolTip(self.MODEL_MENU_TOOLTIP)
      self._modelMenu.setEnabled(True)
      self._promptField.setToolTip('')
      self._promptField.setReadOnly(False)
      self._promptField.setEnabled(True)
      self._submitBtn.setToolTip(self.SUBMIT_BUTTON_TOOLTIP)
      self._submitBtn.setEnabled(True)
    else:
      self._modelMenu.clear()
      self._modelMenu.addItem('Invalid API Key')
      self._modelMenu.setToolTip(self.DISABLED_NOAPIKEY_TOOLTIP)
      self._modelMenu.setEnabled(False)
      self._promptField.setToolTip(self.DISABLED_NOAPIKEY_TOOLTIP)
      self._promptField.setReadOnly(True)
      self._promptField.setEnabled(False)
      self._submitBtn.setToolTip(self.DISABLED_NOAPIKEY_TOOLTIP)
      self._submitBtn.setEnabled(False)

  def _onSettingsButton(self):
    """Show the settings dialog."""
    self._settingsDialog._completionParams = self.state.completionParams.copy()
    self._settingsDialog.show()

  def _onSettingsDialogClosedOk(self):
    """Updates the models list if apiKey is valid."""
    self._checkApiKey()





# Easy function setup:


def _initGPTWindow() -> GPTWindow:
  """Create a new GPT window."""
  # get the list of models from the openai api
  models = getModels(['gpt'])
  # create the window
  win = GPTWindow(models=models)
  return win


def _initState(win: GPTWindow) -> GPTState:
  """Make a new state from the given window and response."""
  model = win.modelMenu.currentText()
  state = GPTState(window=win, model=model)
  return state


def showGPTWindow() -> GPTWindow:
  """Show the GPT window."""
  # get the list of models from the openai api
  win: GPTWindow = _initGPTWindow()
  state: GPTState = _initState(win)
  win.show()
  return win

