import sys
from PyQt5.QtWidgets import QApplication

from arcs.utils.config_manager import load_stylesheet, load_json_config
from arcs.ui.main_ui import main_ui

def main():
    theme = load_json_config().get("ui").get("theme")
    style = load_stylesheet("dark")

    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    win = main_ui()
    win.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()