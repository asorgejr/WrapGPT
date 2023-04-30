import typing as t
import openai
from PySide2 import QtCore, QtWidgets
from . import ai


class Settings(QtCore.QSettings):
  """The settings of the application"""
  _staticInstance: 'Settings' = None

  @property
  def validApiKey(self) -> bool:
    """Whether the API key is valid or not"""
    return self._keyValid

  def __init__(self, application: QtWidgets.QApplication):
    orgName = application.organizationName()
    appName = application.applicationName()
    super().__init__(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, orgName, appName)
    self.setValue(self.KEY_VERSION(), application.applicationVersion())
    key = self.value(self.KEY_OPENAI_API_KEY(), '')
    self._keyValid = isinstance(key, str) and self.tryValidateApiKey(key)


  def setValue(self, key: str, value: t.Any) -> None:
    super().setValue(key, value)
    self._onValueChanged(key, value)

  @staticmethod
  def KEY_OPENAI_API_KEY() -> str:
    """The settings key for the OpenAI API key"""
    return 'openai/api_key'

  @staticmethod
  def KEY_VERSION() -> str:
    """The settings key for the version"""
    return 'version'

  def _onValueChanged(self, key: str, value):
    self._ifKeyValueChanged(key, value)

  def _ifKeyValueChanged(self, key: str, value):
    if key == self.KEY_OPENAI_API_KEY():
      if self.tryValidateApiKey(value):
        self._keyValid = True
        self._oldKey = value
      else:
        self._keyValid = False

  @staticmethod
  def tryValidateApiKey(key: str) -> bool:
    oldKey = openai.api_key
    openai.api_key = key
    try:
      ai.getModels(['gpt'])
      return True
    except openai.error.AuthenticationError as e:
      openai.api_key = oldKey
      return False

  @staticmethod
  def instance(application: QtWidgets.QApplication = None) -> 'Settings':
    """Get the settings instance"""
    if Settings._staticInstance is None:
      Settings._staticInstance = Settings(application if application else QtWidgets.QApplication.instance())
    return Settings._staticInstance

# SETTINGS: Settings = None  # type: ignore

def ShowNoApiKeyDialog():
  message = QtWidgets.QDialog()
  message.setModal(True)
  message.setWindowTitle('No API Key')
  message.setLayout(QtWidgets.QVBoxLayout())
  label = QtWidgets.QLabel('<p>The OpenAI API key is invalid. You will not be able to send prompts to openai without a valid API key.</p>'
                           f'<p>Please go to <a href="https://platform.openai.com/account/api-keys">https://platform.openai.com/account/api-keys</a> '
                           'to get your API key.</p><p>You can set the key in \'Settings\' -> \'OpenAI API Key\'.</p>')
  # allow label to be selectable
  label.setTextFormat(QtCore.Qt.RichText)
  label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
  label.setOpenExternalLinks(True)
  message.layout().addWidget(label)
  okButton = QtWidgets.QPushButton('OK')
  okButton.setFixedWidth(100)
  buttonLayout = QtWidgets.QHBoxLayout()
  buttonLayout.addStretch()
  buttonLayout.addWidget(okButton)
  message.layout().addLayout(buttonLayout)
  okButton.clicked.connect(message.accept)
  message.exec_()
