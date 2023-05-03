import os
import requests
import json
import re
import semver
from PySide2 import QtGui, QtWidgets, QtCore
from ams.ui import themes
import ams.ai as ai
import ams.gpt_window as gpt_window
from ams.settings import Settings, showNoApiKeyWarning, showNoInternetConnectionWarning
import version
import icons

ORG_NAME = 'AMS'
APP_NAME = 'WrapGPT'
APP_VERSION = version.VERSION


if os.name == 'nt':  # some windows stuff to get the correct icon in the taskbar:
  import ctypes
  ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'{ORG_NAME}.{APP_NAME}.{APP_VERSION}')


class AppStyle(QtWidgets.QProxyStyle):
  def __init__(self, *args, **kwargs):
    """A custom style with optional debug mode. Debug mode draws a red rectangle around widgets and a blue rectangle around primitives.

    Keyword Args:
      debug (bool = False): Whether to enable debug mode."""
    self.debug = kwargs.get('debug', False)
    kwargs.pop('debug', None)
    super().__init__(*args, **kwargs)


  def drawPrimitive(self, element, option, painter, widget=None):
    # if self.debug: print(f"Drawing primitive {element} for {option}")
    super().drawPrimitive(element, option, painter, widget)
    # draw a red rectangle around the widget
    if self.debug:
      painter.save()
      painter.setPen(QtGui.QPen(QtGui.QColor('red'), 2))
      painter.drawRect(option.rect)
      painter.restore()

  def drawControl(self, element, option, painter, widget=None):
    # if self.debug: print(f"Drawing control {element} for {option}")
    super().drawControl(element, option, painter, widget)
    # draw a blue rectangle around the element
    if self.debug:
      painter.save()
      painter.setPen(QtGui.QPen(QtGui.QColor('blue'), 2))
      painter.drawRect(option.rect)
      painter.restore()

  def drawComplexControl(self, element, option, painter, widget=None):
    # if self.debug: print(f"Drawing complex control {element} for {option}")
    super().drawComplexControl(element, option, painter, widget)
    # draw a blue rectangle around the element
    if self.debug:
      painter.save()
      painter.setPen(QtGui.QPen(QtGui.QColor('green'), 2))
      painter.drawRect(option.rect)
      painter.restore()


def updateAvailable() -> bool:
  """Checks github releases for the latest version of WrapGPT, and compares it to the current version."""
  versionRegex = r'^v?(\d+\.\d+\.\d+)(?:-([\w\d\.]+))?$'
  try:
    r = requests.get('https://api.github.com/repos/asorgejr/WrapGPT/releases')
    if r.status_code == 200:
      releases = json.loads(r.text)
      # find latest release which is not a pre-release (-alpha, -beta, etc.)
      latest = next((release for release in releases if not release['prerelease']), None)
      if latest is None: return False  # no non-prerelease releases found
      latestVersion = latest['tag_name']
      if re.match(versionRegex, latestVersion):
        latestVersion = re.search(versionRegex, latestVersion).group(1)
      if semver.compare(APP_VERSION, latestVersion) < 0:
        return True
  except Exception as e:
    print(e)
  return False


def showUpdateDialog():
  updateDialog = QtWidgets.QDialog()
  updateDialog.setWindowTitle('Update Available')
  updateLabel = QtWidgets.QLabel()
  updateLabel.setText(f'A new version is available. Download it from <a href="https://github.com/asorgejr/WrapGPT/releases">The WrapGPT Github Releases Page</a>')
  updateLabel.setOpenExternalLinks(True)
  updateLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
  updateLabel.setTextFormat(QtCore.Qt.RichText)
  updateDialog.setLayout(QtWidgets.QVBoxLayout())
  updateDialog.layout().addWidget(updateLabel)
  updateDialog.exec_()


def getEnterApiKeyDialog():
  dialog = QtWidgets.QInputDialog()
  dialog.setWindowTitle('Enter OpenAI API Key')
  dialog.setLabelText('<p>Please enter your OpenAI API key</p><p>(You can get your API key from <a href="https://platform.openai.com/account/api-keys">https://platform.openai.com/account/api-keys</a>)</p>')
  label: QtWidgets.QLabel = dialog.findChild(QtWidgets.QLabel)
  label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
  label.setTextFormat(QtCore.Qt.RichText)
  label.setOpenExternalLinks(True)
  dialog.setModal(True)
  return dialog


def main():
  app = QtWidgets.QApplication([])
  app.setApplicationName(APP_NAME)
  app.setOrganizationName(ORG_NAME)
  app.setWindowIcon(QtGui.QIcon(':/icons/WrapGPT.png'))
  app.setApplicationVersion(APP_VERSION)
  app.setStyle(AppStyle('Fusion'))
  app.setPalette(themes.DarkPalette())
  app.setStyleSheet(themes.DarkStyle())
  SETTINGS = Settings.instance(application=app)
  models = []
  if Settings.hasInternetConnection():
    if updateAvailable():
      showUpdateDialog()
    api_key = SETTINGS.value(Settings.KEY_OPENAI_API_KEY(), None)
    if not SETTINGS.validApiKey:
      dialog = getEnterApiKeyDialog()
      dialog.exec_()
      api_key = dialog.textValue()
      SETTINGS.setValue(Settings.KEY_OPENAI_API_KEY(), api_key)

    if not SETTINGS.validApiKey:
      showNoApiKeyWarning()
    else:
      models = ai.getModels(['gpt'])
  else:
    showNoInternetConnectionWarning()
    return

  window = gpt_window.GPTWindow(models=models)
  window.show()
  app.exec_()
  return


if __name__ == '__main__':
  main()
