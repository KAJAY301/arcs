from PyQt5.QtWidgets import (
    QFrame, QSpinBox, QWidget, QDockWidget, QVBoxLayout, QGridLayout, 
    QLabel, QPushButton, QSizePolicy, QDoubleSpinBox, QLineEdit
    )
from PyQt5.QtGui import QIntValidator
from arcs.utils.config_manager import load_json_config

class ColorSettingDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Color Setting", parent)
        main_widget = QWidget()
        self.setWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Settings Area
        setting_group = QWidget()
        setting_layout = QGridLayout(setting_group)
        main_layout.addWidget(setting_group, stretch=3)

        setting_layout.addWidget(QLabel("First Cross Basic Color:"), 0, 0)

        self.color_preview = QFrame()
        self.color_preview.setFixedSize(100, 100)
        self.color_preview.setFrameShape(QFrame.StyledPanel)
        setting_layout.addWidget(self.color_preview, 1, 0, 3, 1)

        setting_layout.addWidget(QLabel("B:"), 1, 1)
        self.b_input = QSpinBox()
        setting_layout.addWidget(self.b_input, 1, 2)

        setting_layout.addWidget(QLabel("G:"), 2, 1)
        self.g_input = QSpinBox()
        setting_layout.addWidget(self.g_input, 2, 2)

        setting_layout.addWidget(QLabel("R:"), 3, 1)
        self.r_input = QSpinBox()
        setting_layout.addWidget(self.r_input, 3, 2)

        # Binary threshold
        binary_widget = QWidget()
        binary_layout = QGridLayout(binary_widget)
        main_layout.addWidget(binary_widget, stretch=1)
        
        binary_layout.addWidget(QLabel("Binary Threshold:"), 0, 0)
        self.binary_input = QSpinBox()
        binary_layout.addWidget(self.binary_input, 0, 1)

        # Apply congif rule & values

        self.b_input.setRange(0, 255)
        self.g_input.setRange(0, 255)
        self.r_input.setRange(0, 255)
        self.binary_input.setRange(0, 255)

        self.b_input.setValue(26)
        self.g_input.setValue(39)
        self.r_input.setValue(42)
        self.binary_input.setValue(55)

        self.b_input.setFixedWidth(100)
        self.g_input.setFixedWidth(100)
        self.r_input.setFixedWidth(100)
        self.binary_input.setFixedWidth(100)