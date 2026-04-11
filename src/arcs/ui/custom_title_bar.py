from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QPushButton, QWidget,
)

from arcs.utils.config_manager import load_resource_path

title_bar_height = 50

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(title_bar_height) 
        self.setStyleSheet("""
            background-color: #222222;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        
        # Logo 
        title_logo = QLabel()
        logo_pixmap = QPixmap(load_resource_path("logo.png"))
        title_logo.setPixmap(logo_pixmap)
        layout.addWidget(title_logo)
        # Name
        title_name = QLabel("ARCS")
        title_name.setStyleSheet("""
            color: #999999; 
            font-family: Consolas;
            font-weight: 700;
            font-size: 30px;
            letter-spacing: 2px;
            padding-top: 2px;
        """)
        layout.addWidget(title_name)

        # V line
        vertical_line = QFrame()
        vertical_line.setFrameShape(QFrame.VLine)
        vertical_line.setLineWidth(5)
        vertical_line.setStyleSheet("""
            color: #DFA05D;
        """)
        layout.addWidget(vertical_line)

        #Version
        title_version = QLabel("1.2.0")
        title_version.setStyleSheet("""
            color: #999999; 
            font-family: Consolas;
            font-weight: 200;
            font-size: 14px;
            padding-top: 10px;
        """)
        layout.addWidget(title_version, 1)

        # Min Buttom
        self.min_button = QPushButton(self)
        min_icon = QIcon()
        min_icon.addFile(load_resource_path("min.png"))
        self.min_button.setIcon(min_icon)
        self.min_button.clicked.connect(self.window().showMinimized)
        self.min_button.setStyleSheet("""
            QPushButton { 
                icon-size: 50px;
                padding: 0px;
                border-radius: 0px;
        }
            QPushButton:hover { 
                background-color: #555555; 
        }
        """)
        layout.addWidget(self.min_button)

        # Max button
        self.max_button = QPushButton(self)
        max_icon = QIcon()
        max_icon.addFile(load_resource_path("max.png"))
        self.max_button.setIcon(max_icon)
        self.max_button.clicked.connect(self.window().showMaximized)
        self.max_button.setStyleSheet("""
            QPushButton { 
                icon-size: 50px;
                padding: 0px;
                border-radius: 0px;
        }
            QPushButton:hover { 
                background-color: #555555; 
        }
        """)
        layout.addWidget(self.max_button)

        # Normal button
        self.normal_button = QPushButton(self)
        normal_icon = QIcon()
        normal_icon.addFile(load_resource_path("normal.png"))
        self.normal_button.setIcon(normal_icon)
        self.normal_button.clicked.connect(self.window().showNormal)
        self.normal_button.setStyleSheet("""
            QPushButton { 
                icon-size: 50px;
                padding: 0px;
                border-radius: 0px;
        }
            QPushButton:hover { 
                background-color: #555555; 
        }
        """)
        self.normal_button.setVisible(False)
        layout.addWidget(self.normal_button)

        # Close button
        self.close_button = QPushButton(self)
        close_icon = QIcon()
        close_icon.addFile(load_resource_path("close.png"))
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(self.window().close)
        self.close_button.setStyleSheet("""
            QPushButton { 
                icon-size: 50px;
                padding: 0px;
                border-radius: 0px;
        }
            QPushButton:hover { 
                background-color: #DD2222; 
        }
        """)
        layout.addWidget(self.close_button)
    
    def window_state_changed(self, state):
        if state == Qt.WindowState.WindowMaximized:
            self.normal_button.setVisible(True)
            self.max_button.setVisible(False)
        else:
            self.normal_button.setVisible(False)
            self.max_button.setVisible(True)
    



