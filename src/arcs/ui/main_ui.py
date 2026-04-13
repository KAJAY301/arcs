from PyQt5.QtWidgets import (
    QAction, QActionGroup, QMainWindow, QMenu, QWidget, QVBoxLayout, 
    QLabel, QSizePolicy, QMessageBox, 
    QSpinBox, QDoubleSpinBox, QLineEdit
    )
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPixmap

from arcs.ui.custom_title_bar import CustomTitleBar, title_bar_height
from arcs.ui.log_dock import LogDock
from arcs.ui.setting_dock import SettingDock
from arcs.ui.monitor_dock import MonitorDock
from arcs.ui.color_setting_dock import ColorSettingDock

from arcs.utils.config_manager import load_json_config, save_json_config_atomic

class MainUi(QMainWindow):
    def __init__(self, core):
        super().__init__()
        self.setWindowTitle("PyYOLO Scan System V1.2")
        self.setGeometry(80, 80, 1280, 720)
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
        self.update_color()

        # Parameters initialization
        self.initial_pos = None
        self.cfg = load_json_config()
        
        # Start in fullscreen
        self.showFullScreen()

    def init_ui(self):
        # Header
        self.header = CustomTitleBar(self)
        self.setContentsMargins(0, title_bar_height, 0, 0)

        # Central_Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Setting Dock Widget
        self.setting_dock = SettingDock(self)
        self.setting_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.setting_dock)

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

        # Color setting Dock Widget
        self.color_setting_dock = ColorSettingDock(self)
        self.color_setting_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.color_setting_dock)

        self.color_setting_dock.b_input.valueChanged.connect(self.update_color)
        self.color_setting_dock.g_input.valueChanged.connect(self.update_color)
        self.color_setting_dock.r_input.valueChanged.connect(self.update_color)
        self.color_setting_dock.binary_input.valueChanged.connect(self.update_color)

        # Main panel
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.img_label = QLabel("Camera Offline")
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background-color: #000000; border: 10px solid #222222;")
        main_layout.addWidget(self.img_label, stretch=1)

        # Monitor Dock
        self.monitor_dock = MonitorDock(self)
        self.monitor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.monitor_dock)
        
        self.monitor_dock.hide()

        # Log Dock
        self.log_dock = LogDock(self)
        self.log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.log_dock.setMaximumHeight(250)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        self.log_dock.hide()

        # Menu Bar
        menu_bar = self.menuBar()

            # View Menu
        view_menu = menu_bar.addMenu(" View ")
        view_menu.addAction(self.setting_dock.toggleViewAction())
        view_menu.addAction(self.color_setting_dock.toggleViewAction())
        view_menu.addAction(self.monitor_dock.toggleViewAction())
        view_menu.addAction(self.log_dock.toggleViewAction())
        
            # Display Mode Submenu
        settings_submenu = QMenu('Image', self)
        view_menu.addMenu(settings_submenu)

        settings_submenu.addAction("Close", lambda: self.set_display_mode("close"))
        settings_submenu.addAction("Raw", lambda: self.set_display_mode("raw"))
        settings_submenu.addAction("Zoom in", lambda: self.set_display_mode("zoom_in"))
        settings_submenu.addAction("CV2-gray", lambda: self.set_display_mode("cv2_gray"))
        settings_submenu.addAction("CV2-binary", lambda: self.set_display_mode("cv2_binary"))
        settings_submenu.addAction("CV2-horizon", lambda: self.set_display_mode("cv2_horizon"))
        settings_submenu.addAction("CV2-vertical", lambda: self.set_display_mode("cv2_vertical"))

            # Inference Menu
        inference_menu = menu_bar.addMenu(" Inference ")

                #first inference model
        first_inference_submenu = QMenu('First Inference', self)
        inference_menu.addMenu(first_inference_submenu)
        first_inference_submenu.addAction("YOLOv8", lambda: self.set_first_inference_model("yolo_v8"))
        
                # second inference model
        second_inference_submenu = QMenu('Second Inference', self)
        inference_menu.addMenu(second_inference_submenu)
        second_inference_submenu.addAction("YOLOv11 Box", lambda: self.set_second_inference_model("yolo_v11_box"))
        second_inference_submenu.addAction("YOLOv11 Pose", lambda: self.set_second_inference_model("yolo_v11_pose"))
        second_inference_submenu.addAction("CV2", lambda: self.set_second_inference_model("cv2"))

            # Calibration Menu
        calibration_menu = menu_bar.addMenu(" Calibration ")
        # Color calibration
        # distance calibration, etc

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

    def update_color(self):
        try:
            b_value = self.color_setting_dock.b_input.value()
            g_value = self.color_setting_dock.g_input.value()
            r_value = self.color_setting_dock.r_input.value()
            binary_value = self.color_setting_dock.binary_input.value()

            style = f"background-color: rgb({r_value}, {g_value}, {b_value}); border: 1px solid black; border-radius: 10px;"
            self.color_setting_dock.color_preview.setStyleSheet(style)
            # update inference parameters(BGR and binary threshold)
            self.core.update_color_parameters({
                'white_b': b_value,
                'white_g': g_value,
                'white_r': r_value,
                'binary_threshold': binary_value
            })
        except:
            pass

    # Toggle
    def toggle_camera(self, checked):
        success = self.core.toggle_camera(checked)
        if not success:
            self.setting_dock.start_btn.blockSignals(True)
            self.setting_dock.start_btn.setChecked(not checked)
            self.setting_dock.start_btn.blockSignals(False)
            return
        text = "Camera Running" if checked else "Camera Stopped"
        self.setting_dock.start_btn.setText(text)
    
    def toggle_detection(self, checked):
        success = self.core.toggle_detection(checked)
        if not success:
            self.setting_dock.detect_btn.blockSignals(True)
            self.setting_dock.detect_btn.setChecked(not checked)
            self.setting_dock.detect_btn.blockSignals(False)
            return
        text = "Detection Running" if checked else "Detection Stopped"
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

    # Change Mode
    def set_display_mode(self, mode: str):
            print(f"Switching display mode to {mode}")
            if mode in ["cv2_gray", "cv2_binary", "cv2_horizon", "cv2_vertical"]:
                if self.core.inference_thread.second_inference_model in ["yolo_v11_box", "yolo_v11_pose"]:
                    reply = QMessageBox.question(
                        self, 
                        'Switch Inference Model', 
                        "You need to use CV2 as second inference model to use CV2 display mode. \n\n"
                        "Do you want to switch second inference model to CV2?",
                        QMessageBox.Yes | QMessageBox.No, 
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.core.set_second_inference_model("cv2")
                        self.core.set_display_mode(mode)

                if not self.core.inference_thread.is_detecting:
                    reply = QMessageBox.question(
                        self,
                        'Start Detection',
                        "You need to start detection to use CV2 display mode. \n\n"
                        "Do you want to start detection?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.toggle_detection(True)
                        self.setting_dock.detect_btn.setChecked(True)
                        self.core.set_display_mode(mode)
            else:
                self.core.set_display_mode(mode)
            
    def set_first_inference_model(self, model: str):
            print(f"Switching first inference model to {model}")
            self.core.set_first_inference_model(model)
    
    def set_second_inference_model(self, model: str):
            print(f"Switching second inference model to {model}")
            if model in ["yolo_v11_box", "yolo_v11_pose"] and self.core.inference_thread.display_mode in ["cv2_gray", "cv2_binary", "cv2_horizon", "cv2_vertical"]:
                reply = QMessageBox.question(
                    self, 
                    'Switch Display Mode', 
                    "YOLO Models don't support CV2 display modes. \n\n"
                    "Do you want to switch display mode to Zoom in?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.core.set_display_mode("zoom_in")
                    self.core.set_second_inference_model(model)
            else:
                self.core.set_second_inference_model(model)

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