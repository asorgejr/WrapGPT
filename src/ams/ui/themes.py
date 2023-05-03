
from PySide2.QtGui import QPalette

def DarkPalette() -> QPalette:
  from PySide2.QtGui import QColor, QBrush
  palette = QPalette()
  palette.setColor(QPalette.WindowText, QColor(180, 180, 180))
  palette.setColor(QPalette.Button, QColor(53, 53, 53))
  palette.setColor(QPalette.Light, QColor(180, 180, 180))
  palette.setColor(QPalette.Midlight, QColor(90, 90, 90))
  palette.setColor(QPalette.Dark, QColor(35, 35, 35))
  palette.setColor(QPalette.Mid, QColor(40, 40, 40))
  palette.setColor(QPalette.Text, QColor(180, 180, 180))
  palette.setColor(QPalette.Highlight, QColor(30, 180, 180))
  palette.setColor(QPalette.BrightText, QColor(180, 180, 180))
  palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
  palette.setColor(QPalette.ButtonText, QColor(180, 180, 180))
  palette.setColor(QPalette.Base, QColor(42, 42, 42))
  palette.setColor(QPalette.Window, QColor(53, 53, 53))
  palette.setColor(QPalette.Link, QColor(0, 180, 218))
  palette.setColor(QPalette.LinkVisited, QColor(0, 100, 120))
  palette.setBrush(QPalette.Disabled, QPalette.WindowText, QBrush(QColor(127, 127, 127)))
  palette.setBrush(QPalette.Disabled, QPalette.Text, QBrush(QColor(127, 127, 127)))
  palette.setBrush(QPalette.Disabled, QPalette.ButtonText, QBrush(QColor(127, 127, 127)))
  palette.setBrush(QPalette.Disabled, QPalette.Light, QBrush(QColor(53, 53, 53)))
  palette.setBrush(QPalette.Disabled, QPalette.Midlight, QBrush(QColor(40, 40, 40)))
  palette.setBrush(QPalette.Disabled, QPalette.Dark, QBrush(QColor(35, 35, 35)))
  palette.setBrush(QPalette.Disabled, QPalette.Mid, QBrush(QColor(40, 40, 40)))
  palette.setBrush(QPalette.Disabled, QPalette.Window, QBrush(QColor(53, 53, 53)))
  palette.setBrush(QPalette.Disabled, QPalette.Base, QBrush(QColor(42, 42, 42)))
  return palette

def DarkStyle() -> str:
  # dark tooltips
  return """
  QToolTip { color: #ffffff; background-color: #424242; border: 1px solid white; }
  """

# Light Theme

def LightPalette() -> QPalette:
  from PySide2.QtGui import QColor, QBrush
  palette = QPalette()
  palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
  palette.setColor(QPalette.Button, QColor(240, 240, 240))
  palette.setColor(QPalette.Light, QColor(180, 180, 180))
  palette.setColor(QPalette.Midlight, QColor(200, 200, 200))
  palette.setColor(QPalette.Dark, QColor(225, 225, 225))
  palette.setColor(QPalette.Mid, QColor(210, 210, 210))
  palette.setColor(QPalette.Text, QColor(0, 0, 0))
  palette.setColor(QPalette.BrightText, QColor(0, 0, 0))
  palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
  palette.setColor(QPalette.Base, QColor(237, 237, 237))
  palette.setColor(QPalette.Window, QColor(240, 240, 240))
  palette.setBrush(QPalette.Disabled, QPalette.WindowText, QBrush(QColor(115, 115, 115)))
  palette.setBrush(QPalette.Disabled, QPalette.Text, QBrush(QColor(115, 115, 115)))
  palette.setBrush(QPalette.Disabled, QPalette.ButtonText, QBrush(QColor(115, 115, 115)))
  palette.setBrush(QPalette.Disabled, QPalette.Light, QBrush(QColor(180, 180, 180)))
  palette.setBrush(QPalette.Disabled, QPalette.Midlight, QBrush(QColor(200, 200, 200)))
  palette.setBrush(QPalette.Disabled, QPalette.Dark, QBrush(QColor(225, 225, 225)))
  palette.setBrush(QPalette.Disabled, QPalette.Mid, QBrush(QColor(210, 210, 210)))
  palette.setBrush(QPalette.Disabled, QPalette.Window, QBrush(QColor(240, 240, 240)))
  palette.setBrush(QPalette.Disabled, QPalette.Base, QBrush(QColor(237, 237, 237)))
  return palette
