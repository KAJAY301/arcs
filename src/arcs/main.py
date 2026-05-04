import os
import sys

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap

from arcs.utils.config_manager import load_stylesheet, load_json_config
from arcs.ui.main_ui import MainUi
from arcs.core.main_core import MainCore

def main():
    theme = load_json_config().get("ui").get("theme")
    style = load_stylesheet(theme)

    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    # Splash Screen
    splash_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "splash.png"))
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    app.processEvents()

    # Initialize core
    core = MainCore()

    # Create main window
    win = MainUi(core)
    win.show()
    splash.finish(win)

    code = app.exec_()
    core.stop()
    sys.exit(code)

if __name__ == "__main__":
    main()