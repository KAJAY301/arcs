import time
import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QDockWidget, QVBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QPushButton, QSizePolicy, QMessageBox, 
    QTableWidget, QTableWidgetItem, QHeaderView
    )
from PyQt5.QtCore import Qt, QTimer, QEvent, QSize
from PyQt5.QtGui import QPixmap

from arcs.ui.custom_title_bar import CustomTitleBar, title_bar_height
from arcs.ui.log_dock import LogDock
from arcs.ui.setting_dock import SettingDock
from arcs.ui.monitor_dock import MonitorDock
from arcs.utils.config_manager import load_env_config, load_json_config, save_json_config_atomic
from arcs.core.camera_cotroller import Camera
from arcs.core.plc_client_thread import PLCClientThread

class main_ui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyYOLO Scan System V1.2")
        self.setGeometry(80, 80, 1200, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Config setup
        self.cfg = load_json_config()

        # Camera Setup
        self.camera = Camera()

        #initial ui, media
        self.init_ui()
        self.init_media()
        self.sync_ui_params()

        # Parameters initialization
        #self.last_send_time = 0
        #self.next_seq = 1
        self.is_detecting = False
        self.initial_pos = None

        # Init Inference Thread
        self.infer_thread = self.camera.infer_thread
        self.infer_thread.result_img.connect(self.handle_inference_result)
        
        # Init PLC Thread
        plc_cfg = load_env_config()
        self.plc_thread = PLCClientThread(
            ip = plc_cfg.get("plc_ip"), 
            port = plc_cfg.get("plc_port")
        )
        self.plc_thread.ack_received.connect(self.on_plc_ack)
        self.plc_thread.error.connect(lambda m: self.status_bar.showMessage(f"PLC ERR: {m}"))
        self.plc_thread.status.connect(lambda m: self.status_bar.showMessage(f"PLC: {m}"))
        self.plc_thread.start()

    """    Initialization Functions    """
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

        self.setting_dock.start_btn.clicked.connect(self.toggle_camera)
        self.setting_dock.detect_btn.toggled.connect(self.toggle_detection)
        
        self.setting_dock.btn_up.clicked.connect(lambda: self.manual_direction("UP"))
        self.setting_dock.btn_down.clicked.connect(lambda: self.manual_direction("DOWN"))
        self.setting_dock.btn_left.clicked.connect(lambda: self.manual_direction("LEFT"))
        self.setting_dock.btn_right.clicked.connect(lambda: self.manual_direction("RIGHT"))

        # Main panel
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.img_label = QLabel("Camera Feed")
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background-color: #000000; border: 2px solid #555555;")
        main_layout.addWidget(self.img_label, stretch=1)

        # Monitor Dock
        self.monitor_dock = MonitorDock(self)
        self.monitor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.monitor_dock)
        view_menu.addAction(self.monitor_dock.toggleViewAction())
        self.monitor_dock.hide()

        # Log Dock
        log_dock = LogDock(self)
        log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        log_dock.setMaximumHeight(250)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
        view_menu.addAction(log_dock.toggleViewAction())
        log_dock.hide()

    def init_media(self):
        # image, ssound initializations
        pass

    """    Logic Functions    """
    # Update
    def update_length_from_cm(self):
        try:
            cm_value = float(self.setting_dock.length_cm_input.text())
            inch_value = cm_value * 0.3937
            self.setting_dock.length_inch_input.blockSignals(True)
            self.setting_dock.length_inch_input.setText(f"{inch_value:.2f}")
            self.setting_dock.length_inch_input.blockSignals(False)
        except:
            pass

    def update_length_from_inch(self):
        try:
            inch_value = float(self.setting_dock.length_inch_input.text())
            cm_value = inch_value * 2.54
            self.setting_dock.length_cm_input.blockSignals(True)
            self.setting_dock.length_cm_input.setText(f"{cm_value:.2f}")
            self.setting_dock.length_cm_input.blockSignals(False)
        except:
            pass

    def sync_ui_params(self):
        try:
            length_cm_input = float(self.setting_dock.length_cm_input.text())
            speed_input = float(self.setting_dock.speed_input.text())
            pixel_input = float(self.setting_dock.pixel_input.text())
            threshold_input = float(self.setting_dock.threshold_input.text())
        except ValueError:
            pass
        try:
            ui_input = {
                'length_cm_input': length_cm_input,
                'speed_input': speed_input,
                'pixel_input': pixel_input
            }
            self.camera.update_camera_params(ui_input)
            self.monitor_dock.update_params(ui_input)
            self.infer_thread.update_params(pixel_input, threshold_input)
            
            #self.update_monitor_table()
        except Exception as e:
            print(f"Error syncing UI params: {e}")
            pass

    # Toggle
    def toggle_camera(self):
        if self.camera.is_running:
            try:
                self.camera.stop_grabbing()
                self.camera.close()
                self.setting_dock.start_btn.setText("Start Camera")
                self.status_bar.showMessage("Camera Stopped")
            except Exception as e:
                QMessageBox.critical(self, "Camera Stop Failed", str(e))
        else:
            try:
                self.camera.open()
                self.sync_ui_params()
                self.camera.start_grabbing()
                self.setting_dock.start_btn.setText("Stop Camera")
                self.status_bar.showMessage("Camera Running")
            except Exception as e:
                QMessageBox.critical(self, "Camera Init Failed", str(e))

    def toggle_detection(self, checked):
        self.is_detecting = checked
        if checked:
            self.setting_dock.detect_btn.setText("Stop Detect")
            self.infer_thread.is_detacting = True
        else:
            self.setting_dock.detect_btn.setText("Start Detect")
            self.infer_thread.is_detacting = False

    def manual_direction(self, direction):
        manual_move_mm = self.cfg.get('setting', {}).get('manual_move_mm')
        mm_per_pulses_x = load_env_config().get('motor_mm_per_pulse_x')
        mm_per_pulses_y = load_env_config().get('motor_mm_per_pulse_y')
        pulses_x = int(manual_move_mm / mm_per_pulses_x)
        pulses_y = int(manual_move_mm / mm_per_pulses_y)
        dx, dy, px, py = 2, 2, 0, 0

        if   direction == "UP"   : 
            py = pulses_y
            dy = 2
        elif direction == "DOWN" : 
            py = pulses_y
            dy = 1
        elif direction == "LEFT" : 
            px = pulses_x
            dx = 2
        elif direction == "RIGHT": 
            px = pulses_x
            dx = 1

        self.plc_thread.enqueue_move(dx, dy, px, py)
        #self.next_seq += 1
        #self.status_bar.showMessage(f"Manual: {direction}(next_seq:{self.next_seq}, px:{px}, py:{py})")

    # Something else
    def handle_inference_result(self, q_img):
        if not q_img.isNull():
            self.img_label.setPixmap(QPixmap.fromImage(q_img))
        """
            self.img_label.setPixmap(QPixmap.scaled(self.img_label.size(), 
                                                   Qt.KeepAspectRatio,
                                                   Qt.SmoothTransformation))
            
        if self.is_detecting:
            f_pt = data.get('first')
            s_pt = data.get('second')

            if f_pt and s_pt:
                pixel_mm = float(self.pixel_input.text())
                dx_mm = (s_pt[0] - f_pt[0]) * pixel_mm
                dy_mm = (s_pt[1] - f_pt[1]) * pixel_mm
                #LogDock.update_plot(dx_mm, dy_mm)

                
                if abs(dx_mm) > alarm_dist or abs(dy_mm) > alarm_dist:
                    self.warning_label.show()
                    self.warning_image_label.show()
                    if not self.alert_sound.isPlaying():
                        self.alert_sound.play()
                else:
                    self.warning_label.hide()
                    self.warning_image_label.hide()
                
                print(f"Offset[x:{round(dx_mm, 2)}, y:{round(dy_mm, 2)}]")
                deadband_mm = float(self.threshold_input.text())
                if abs(dx_mm) < deadband_mm: dx_mm = 0
                if abs(dy_mm) < deadband_mm: dy_mm = 0

                mm_per_pulses_x = load_env_config().get('motor_mm_per_pulse_x')
                mm_per_pulses_y = load_env_config().get('motor_mm_per_pulse_y')
                now = time.time() * 1000
                if (now - self.last_send_time) > 500:     #only move every 500ms
                    if dx_mm != 0 or dy_mm != 0:          #dx, dy: 1 = -,  2 = +
                        dx, dy = 2, 2
                        if dx_mm < 0:
                            dx_mm *= -1
                            dx = 1
                        if dy_mm < 0:
                            dy_mm *= -1
                            dy = 1

                        pulses_x = int(dx_mm / mm_per_pulses_x)
                        pulses_y = int(dy_mm / mm_per_pulses_y)
                        
                        pulses_x = min(32767, pulses_x)
                        pulses_y = min(32767, pulses_y)
                        #print(f"PLC[dx:{dx}, dy:{dy}, x:{pulses_x}, y:{pulses_y}]")
                        if self.plc_thread.enqueue_move(dx, dy, pulses_x, pulses_y):
                            self.last_send_time = now
                            self.status_bar.showMessage(f"Auto: X={pulses_x} Y={pulses_y}")
        
            
            else:
                self.status_bar.showMessage("No Match Found")

                #save img to no_match folder

                #self.warning_label.hide()
                #self.warning_image_label.hide()
        """

    def on_plc_ack(self):
        pass

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
        except: pass

        self.infer_thread.stop()
        self.plc_thread.stop()
        if self.camera.is_running:
            try: 
                self.camera.stop_grabbing()
                self.camera.close()
            except:
                pass
        event.accept()

    def read_ui_to_cfg(self):
        cfg = self.cfg.copy()
        try:
            cfg.setdefault("setting", {})
            cfg["setting"]["length_cm"] = float(self.length_cm_input.text())
            cfg["setting"]["speed_m_min"] = float(self.speed_input.text())
            cfg["setting"]["pixel_mm"] = float(self.pixel_input.text())
            cfg["setting"]["alarm_dist"] = float(self.threshold_input.text())
        except:
            pass