from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QSizePolicy, QMessageBox, 
    QSpinBox, QDoubleSpinBox, QLineEdit
    )
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPixmap

from arcs.ui.custom_title_bar import CustomTitleBar, title_bar_height
from arcs.ui.log_dock import LogDock
from arcs.ui.setting_dock import SettingDock
from arcs.ui.monitor_dock import MonitorDock

from arcs.utils.config_manager import load_json_config, save_json_config_atomic

class MainUi(QMainWindow):
    def __init__(self, core):
        super().__init__()
        self.setWindowTitle("PyYOLO Scan System V1.2")
        self.setGeometry(80, 80, 1920, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.core = core
        self.core.frame_ready.connect(self.handle_inference_result)
        self.core.alarm_trigger.connect(self.toggle_warning)
        self.core.log_data.connect(lambda d: self.log_dock.update_plot(d))
        self.core.status_msg.connect(lambda m: self.status_bar.showMessage(m))
        self.core.error_occurred.connect(lambda t, m: QMessageBox.critical(self, t, m))

        #initial ui, media
        self.init_ui()
        self.init_media()
        self.sync_ui_params()

        # Parameters initialization
        self.initial_pos = None
        self.cfg = load_json_config()

    def init_ui(self):
        # Header
        self.header = CustomTitleBar(self)
        self.setContentsMargins(0, title_bar_height, 0, 0)

        # Central_Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Menu Bar
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu(" View ")

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Left Dock Widget
        self.setting_dock = SettingDock(self)
        self.setting_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.setting_dock)
        view_menu.addAction(self.setting_dock.toggleViewAction())

        self.setting_dock.length_cm_input.editingFinished.connect(self.sync_ui_params)
        self.setting_dock.length_inch_input.editingFinished.connect(self.sync_ui_params)
        self.setting_dock.speed_input.editingFinished.connect(self.sync_ui_params)
        self.setting_dock.pixel_input.editingFinished.connect(self.sync_ui_params)
        self.setting_dock.threshold_input.editingFinished.connect(self.sync_ui_params)

        self.setting_dock.start_btn.toggled.connect(self.toggle_camera)
        self.setting_dock.detect_btn.toggled.connect(self.toggle_detection)
        self.setting_dock.control_btn.toggled.connect(self.toggle_control)
        
        self.setting_dock.btn_up.clicked.connect(lambda: self.core.manual_move("UP"))
        self.setting_dock.btn_down.clicked.connect(lambda: self.core.manual_move("DOWN"))
        self.setting_dock.btn_left.clicked.connect(lambda: self.core.manual_move("LEFT"))
        self.setting_dock.btn_right.clicked.connect(lambda: self.core.manual_move("RIGHT"))

        # Main panel
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.img_label = QLabel("Camera Feed")
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background-color: #000000; border: 10px solid #222222;")
        main_layout.addWidget(self.img_label, stretch=1)

        # Monitor Dock
        self.monitor_dock = MonitorDock(self)
        self.monitor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.monitor_dock)
        view_menu.addAction(self.monitor_dock.toggleViewAction())
        self.monitor_dock.hide()

        # Log Dock
        self.log_dock = LogDock(self)
        self.log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.log_dock.setMaximumHeight(250)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        view_menu.addAction(self.log_dock.toggleViewAction())
        self.log_dock.hide()

    def init_media(self):
        # image, sound initializations
        pass

    # Update
    def sync_ui_params(self):
        try:
            length_cm_input = float(self.setting_dock.length_cm_input.value())
            speed_input = float(self.setting_dock.speed_input.value())
            pixel_input = float(self.setting_dock.pixel_input.value())
            threshold_input = float(self.setting_dock.threshold_input.value())
        except ValueError:
            pass
        try:
            ui_input = {
                'length_cm_input': length_cm_input,
                'speed_input': speed_input,
                'pixel_input': pixel_input,
                'threshold_input': threshold_input
            }
            self.core.update_system_parameters(ui_input)
            self.monitor_dock.update_params(ui_input)
        except Exception as e:
            print(f"Error syncing UI params: {e}")
            pass

    # Toggle
    def toggle_camera(self, checked):
        success = self.core.toggle_camera(checked)
        if not success:
            self.setting_dock.start_btn.blockSignals(True)
            self.setting_dock.start_btn.setChecked(not checked)
            self.setting_dock.start_btn.blockSignals(False)
            return
        text = "Stop Camera" if checked else "Start Camera"
        self.setting_dock.start_btn.setText(text)

    def toggle_detection(self, checked):
        success = self.core.toggle_detection(checked)
        if not success:
            self.setting_dock.detect_btn.blockSignals(True)
            self.setting_dock.detect_btn.setChecked(not checked)
            self.setting_dock.detect_btn.blockSignals(False)
            return
        text = "Stop Detect" if checked else "Start Detect"
        self.setting_dock.detect_btn.setText(text)

    def toggle_control(self, checked):
        success = self.core.toggle_control(checked)
        if not success:
            self.setting_dock.control_btn.blockSignals(True)
            self.setting_dock.control_btn.setChecked(not checked)
            self.setting_dock.control_btn.blockSignals(False)
            return
        text = "Auto Control" if checked else "Manual Control"
        self.setting_dock.control_btn.setText(text)    


    # Inference result
    def handle_inference_result(self, q_img):
        self.img_label.setPixmap(QPixmap.fromImage(q_img))

    def toggle_warning(self, should_alarm:bool):
        if should_alarm:
            # Alarm
            self.img_label.setStyleSheet("background-color: #000000; border: 10px solid #E03C3C;")
            # can add alarm sound
        else:
            # Normal
            self.img_label.setStyleSheet("background-color: #000000; border: 10px solid #222222;")

    # Event
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.initial_pos = event.pos()
        focused_widget = self.focusWidget()
        if isinstance(focused_widget, (QSpinBox, QDoubleSpinBox, QLineEdit)):
            focused_widget.clearFocus()
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.initial_pos is not None:
            delta = event.pos() - self.initial_pos
            self.window().move(
                self.window().x() + delta.x(),
                self.window().y() + delta.y(),
            )
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.initial_pos = None
        super().mouseReleaseEvent(event)
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event) 
        if hasattr(self, 'header'):
            window_width = self.width()
            self.header.setGeometry(
                0, 
                0, 
                window_width, 
                title_bar_height
            )
            self.header.raise_()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self.header.window_state_changed(self.windowState())
        super().changeEvent(event)
        event.accept()

    def closeEvent(self, event):
        try:
            self.read_ui_to_cfg()
            save_json_config_atomic(self.cfg)
            self.core.stop()
            event.accept()
            
        except Exception as e:
            print(f"UI: error while closing: {e}")
            event.accept()

    def read_ui_to_cfg(self):
        cfg = self.cfg.copy()
        try:
            cfg.setdefault("setting", {})
            cfg["setting"]["length_cm"] = float(self.setting_dock.length_cm_input.value())
            cfg["setting"]["speed_m_min"] = float(self.setting_dock.speed_input.value())
            cfg["setting"]["pixel_mm"] = float(self.setting_dock.pixel_input.value())
            cfg["setting"]["alarm_dist"] = float(self.setting_dock.threshold_input.value())
        except:
            pass