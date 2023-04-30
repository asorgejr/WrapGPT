# main.py
from PySide2 import QtGui, QtWidgets
from src.ams.ui import themes
import ams.ai as gpt
import ams.gpt_window as gpt_window
from src.ams.settings import Settings, ShowNoApiKeyDialog

ORG_NAME = 'AMS'
APP_NAME = 'GPFree'
APP_VERSION = '1.0.0'


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



def main():
  app = QtWidgets.QApplication([])
  app.setApplicationName(APP_NAME)
  app.setOrganizationName(ORG_NAME)
  app.setWindowIcon(QtGui.QIcon(':/ams.ico'))
  app.setApplicationVersion(APP_VERSION)
  app.setStyle(AppStyle('Fusion'))
  app.setPalette(themes.DarkPalette())
  app.setStyleSheet(themes.DarkStyle())
  SETTINGS = Settings.instance(application=app)

  # get the openai api key from OPENAI_API_KEY env var
  # api_key = os.getenv('OPENAI_API_KEY')
  api_key = SETTINGS.value(Settings.KEY_OPENAI_API_KEY(), None)
  # initialize the app

  if not api_key or api_key == '':
    # mb = QtWidgets.QMessageBox.critical(None, 'Error', '''The OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key.\nYou can get your API key from \nhttps://platform.openai.com/account/api-keys''')
    dialog = QtWidgets.QInputDialog()
    dialog.setLabelText(
      '<p>Please enter your OpenAI API key</p><p>(You can get your API key from <a href="https://platform.openai.com/account/api-keys">https://platform.openai.com/account/api-keys</a>)</p>')
    dialog.setModal(True)
    dialog.exec_()
    api_key = dialog.textValue()
    SETTINGS.setValue(Settings.KEY_OPENAI_API_KEY(), api_key)
  models = []
  if not SETTINGS.validApiKey:
    ShowNoApiKeyDialog()
  else:
    models = gpt.getModels(['gpt'])

  window = gpt_window.GPTWindow(models=models)
  window.show()
  # prefsDialog = gpt_window.GPTPrefsWindow(window)
  # prefsDialog.show()
  app.exec_()
  return


if __name__ == '__main__':
  main()
