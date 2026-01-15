import sys
from PyQt5.QtWidgets import QApplication

from arcs.utils.config_manager import load_stylesheet, load_json_config
from arcs.ui.main_ui import MainUi
from arcs.core.main_core import MainCore

def main():
    theme = load_json_config().get("ui").get("theme")
    style = load_stylesheet("dark")

    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    core = MainCore()

    win = MainUi(core)
    win.show()

    code = app.exec_()
    core.stop()
    sys.exit(code)

if __name__ == "__main__":
    main()