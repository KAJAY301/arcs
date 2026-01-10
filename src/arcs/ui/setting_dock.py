from PyQt5.QtWidgets import (
    QWidget, QDockWidget, QVBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QPushButton, QSizePolicy, QSpinBox, QDoubleSpinBox
    )
from arcs.utils.config_manager import load_json_config

class SettingDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Setting", parent)
        left_widget = QWidget()
        self.setWidget(left_widget)
        left_layout = QVBoxLayout(left_widget)

        # Settings Area
        setting_group = QWidget()
        setting_layout = QGridLayout(setting_group)
        left_layout.addWidget(setting_group, stretch=4)

        setting_layout.addWidget(QLabel("Workpiece Length:     "), 0, 0)
        self.length_cm_input = QDoubleSpinBox()
        setting_layout.addWidget(self.length_cm_input, 0, 1)

        setting_layout.addWidget(QLabel("Workpiece Length:    "), 1, 0)
        self.length_inch_input = QDoubleSpinBox()
        setting_layout.addWidget(self.length_inch_input, 1 ,1)

        setting_layout.addWidget(QLabel("Workpiece Speed:     "), 2, 0)
        self.speed_input = QDoubleSpinBox()
        setting_layout.addWidget(self.speed_input, 2, 1)

        setting_layout.addWidget(QLabel("Pixel Size:  "), 3, 0)
        self.pixel_input = QDoubleSpinBox()
        setting_layout.addWidget(self.pixel_input, 3, 1)

        # Camera start/stop button
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.start_btn.setCheckable(True)
        left_layout.addWidget(self.start_btn, stretch=2)

        # Alarm panel
        Alarm_widget = QWidget()
        Alarm_layout = QGridLayout(Alarm_widget)
        Alarm_layout.addWidget(QLabel("Alarm Distance:"), 0, 0)
        self.threshold_input = QDoubleSpinBox()
        Alarm_layout.addWidget(self.threshold_input, 0, 1)
        left_layout.addWidget(Alarm_widget, stretch=1)

        # Auto detect button
        self.detect_btn = QPushButton("Start Detect")
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.detect_btn.setCheckable(True)
        left_layout.addWidget(self.detect_btn, stretch=2)

        # Manual PLC control buttons
        diraction_widget = QWidget()
        diraction_layout = QGridLayout(diraction_widget)
        left_layout.addWidget(diraction_widget, stretch=6)

        self.btn_up = QPushButton("Up")
        self.btn_up.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        diraction_layout.addWidget(self.btn_up, 0, 1, 1, 2)

        self.btn_left = QPushButton("L")
        self.btn_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        diraction_layout.addWidget(self.btn_left, 1, 0, 1, 2)

        self.btn_right = QPushButton("R")
        self.btn_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        diraction_layout.addWidget(self.btn_right, 1, 2, 1, 2)

        self.btn_down = QPushButton("Down")
        self.btn_down.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        diraction_layout.addWidget(self.btn_down, 2, 1, 1, 2)

        # Connect and Apply congif rule & values
        self.length_cm_input.textChanged.connect(self.update_length_from_cm)
        self.length_inch_input.textChanged.connect(self.update_length_from_inch)
        
        self.length_cm_input.setRange(0, 5000)
        self.length_inch_input.setRange(0, 5000)
        self.speed_input.setRange(0, 1000)
        self.pixel_input.setRange(0, 10)
        self.threshold_input.setRange(0, 5000)

        self.length_cm_input.setSingleStep(0.1)
        self.length_inch_input.setSingleStep(0.1)
        self.speed_input.setSingleStep(1)
        self.pixel_input.setSingleStep(0.001)
        self.threshold_input.setSingleStep(0.1)

        self.length_cm_input.setDecimals(2)
        self.length_inch_input.setDecimals(2)
        self.speed_input.setDecimals(1)
        self.pixel_input.setDecimals(3)
        self.threshold_input.setDecimals(1)

        self.length_cm_input.setSuffix(" cm")
        self.length_inch_input.setSuffix(" inch")
        self.speed_input.setSuffix(" m/min")
        self.pixel_input.setSuffix(" mm")
        self.threshold_input.setSuffix(" mm")
        
        self.cfg = load_json_config()
        setting = self.cfg.get('setting', {})
        self.length_cm_input.setValue(setting.get('length_cm'))
        self.speed_input.setValue(setting.get('speed_m_min'))
        self.pixel_input.setValue(setting.get('pixel_mm'))
        self.threshold_input.setValue(setting.get('alarm_dist'))

    def update_length_from_cm(self):
        try:
            cm_value = float(self.length_cm_input.value())
            inch_value = cm_value * 0.3937
            self.length_inch_input.blockSignals(True)
            self.length_inch_input.setValue(inch_value)
            self.length_inch_input.blockSignals(False)
        except:
            pass

    def update_length_from_inch(self):
        try:
            inch_value = float(self.length_inch_input.value())
            cm_value = inch_value * 2.54
            self.length_cm_input.blockSignals(True)
            self.length_cm_input.setValue(cm_value)
            self.length_cm_input.blockSignals(False)
        except:
            pass







