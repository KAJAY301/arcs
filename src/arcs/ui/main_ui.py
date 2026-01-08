import time
import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QDockWidget, QVBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QPushButton, QSizePolicy, QMessageBox, 
    QTableWidget, QTableWidgetItem, QHeaderView
    )
from PyQt5.QtCore import Qt, QTimer, QEvent, QSize
from PyQt5.QtGui import QPixmap
from pypylon import pylon

from arcs.ui.custom_title_bar import CustomTitleBar, title_bar_height
from arcs.ui.log_dock import LogDock
from arcs.utils.image_processor import save_image_timed, qimage_to_cv2
from arcs.utils.config_manager import load_model_path, load_env_config, load_json_config, save_json_config_atomic
from arcs.core.camera_cotroller import Camera
from arcs.core.inference_thread import InferenceThread
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

        # Parameters initialization
        self.last_send_time = 0
        self.next_seq = 1
        self.is_detecting = False
        self.initial_pos = None

        # Init Inference Thread
        self.infer_thread = self.camera.infer_thread
        self.infer_thread.result_ready.connect(self.handle_inference_result)

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

        #SAVE IMG NO MATCH FOLDER
        self.save_dir = "data/no_match_img"
        self.max_save_count = 500
        self.last_save_time = 0      # 記錄上次存檔的時間戳
        self.cooldown_seconds = 5    # 冷卻時間
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.current_save_count = len(os.listdir(self.save_dir))

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
        left_dock = QDockWidget("Setting", self)
        left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        left_widget = QWidget()
        left_dock.setWidget(left_widget)
        left_layout = QVBoxLayout(left_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)
        view_menu.addAction(left_dock.toggleViewAction())
            # Settings Area
        setting_group = QWidget()
        setting_layout = QGridLayout(setting_group)
        left_layout.addWidget(setting_group, stretch=4)

        setting_layout.addWidget(QLabel("Workpiece Length (cm):"), 0, 0)
        self.length_cm_input = QLineEdit()
        setting_layout.addWidget(self.length_cm_input, 0, 1)

        setting_layout.addWidget(QLabel("Workpiece Length (inch):"), 1, 0)
        self.length_inch_input = QLineEdit()
        setting_layout.addWidget(self.length_inch_input, 1 ,1)

        setting_layout.addWidget(QLabel("Workpiece Speed (m/min):"), 2, 0)
        self.speed_input = QLineEdit()
        setting_layout.addWidget(self.speed_input, 2, 1)

        setting_layout.addWidget(QLabel("Pixel Size (mm):"), 3, 0)
        self.pixel_input = QLineEdit()
        setting_layout.addWidget(self.pixel_input, 3, 1)

        self.length_cm_input.textChanged.connect(self.update_length_from_cm)
        self.length_inch_input.textChanged.connect(self.update_length_from_inch)

        self.length_cm_input.textChanged.connect(self.sync_ui_to_camera)
        self.length_inch_input.textChanged.connect(self.sync_ui_to_camera)
        self.speed_input.textChanged.connect(self.sync_ui_to_camera)
        self.pixel_input.textChanged.connect(self.sync_ui_to_camera)


            # Camera start/stop button
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.start_btn.clicked.connect(self.toggle_camera)
        left_layout.addWidget(self.start_btn, stretch=2)

            #Alarm panel
        Alarm_widget = QWidget()
        Alarm_layout = QGridLayout(Alarm_widget)
        Alarm_layout.addWidget(QLabel("Alarm Distance (mm):       "), 0, 0)
        self.threshold_input = QLineEdit()
        Alarm_layout.addWidget(self.threshold_input, 0, 1)
        left_layout.addWidget(Alarm_widget, stretch=1)

            #Auto detect button
        self.detect_btn = QPushButton("Start Detect")
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.detect_btn.setCheckable(True)
        self.detect_btn.toggled.connect(self.toggle_detection)
        left_layout.addWidget(self.detect_btn, stretch=2)

            #manual PLC control buttons
        diraction_widget = QWidget()
        diraction_layout = QGridLayout(diraction_widget)
        left_layout.addWidget(diraction_widget, stretch=6)

        btn_up = QPushButton("Up")
        btn_up.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_up.clicked.connect(lambda: self.manual_direction("UP"))
        diraction_layout.addWidget(btn_up, 0, 1, 1, 2)

        btn_left = QPushButton("L")
        btn_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_left.clicked.connect(lambda: self.manual_direction("LEFT"))
        diraction_layout.addWidget(btn_left, 1, 0, 1, 2)

        btn_right = QPushButton("R")
        btn_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_right.clicked.connect(lambda: self.manual_direction("RIGHT"))
        diraction_layout.addWidget(btn_right, 1, 2, 1, 2)

        btn_down = QPushButton("Down")
        btn_down.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_down.clicked.connect(lambda: self.manual_direction("DOWN"))
        diraction_layout.addWidget(btn_down, 2, 1, 1, 2)

            # Apply congif value
        setting = self.cfg.get('setting', {})
        self.length_cm_input.setText(str(setting.get('length_cm')))
        self.speed_input.setText(str(setting.get('speed_m_min')))
        self.pixel_input.setText(str(setting.get('pixel_mm')))
        self.threshold_input.setText(str(setting.get('alarm_dist')))

        # Main panel
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.img_label = QLabel("Camera Feed")
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background-color: #000000; border: 2px solid #555555;")
        main_layout.addWidget(self.img_label, stretch=1)

        # Monitor Dock
        monitor_dock = QDockWidget("Monitor", self)
        monitor_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, monitor_dock)
        view_menu.addAction(monitor_dock.toggleViewAction())
        monitor_dock.hide()

        self.monitor_table = QTableWidget(4, 2)
        self.monitor_table.setFrameShape(QTableWidget.NoFrame)
        self.monitor_table.verticalHeader().setVisible(False)
        self.monitor_table.horizontalHeader().setVisible(False)
        monitor_dock.setWidget(self.monitor_table)

        self.monitor_table.setItem(0, 0, QTableWidgetItem("Parameter"))
        self.monitor_table.setItem(0, 1, QTableWidgetItem("Value"))

        self.monitor_table.setItem(1, 0, QTableWidgetItem("Line Rate"))
        self.monitor_table.setItem(1, 1, QTableWidgetItem("None"))
        self.monitor_table.setItem(2, 0, QTableWidgetItem("Exposure Time"))
        self.monitor_table.setItem(2, 1, QTableWidgetItem("None"))
        self.monitor_table.setItem(3, 0, QTableWidgetItem("Height"))
        self.monitor_table.setItem(3, 1, QTableWidgetItem("None"))
        self.monitor_table.setItem(4, 0, QTableWidgetItem("Width"))
        self.monitor_table.setItem(4, 1, QTableWidgetItem("None"))

        self.monitor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 

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
            cm_value = float(self.length_cm_input.text())
            inch_value = cm_value * 0.3937
            self.length_inch_input.blockSignals(True)
            self.length_inch_input.setText(f"{inch_value:.2f}")
            self.length_inch_input.blockSignals(False)
        except:
            pass

    def update_length_from_inch(self):
        try:
            inch_value = float(self.length_inch_input.text())
            cm_value = inch_value * 2.54
            self.length_cm_input.blockSignals(True)
            self.length_cm_input.setText(f"{cm_value:.2f}")
            self.length_cm_input.blockSignals(False)
        except:
            pass

    def sync_ui_to_camera(self):
        try:
            ui_input = {
                'length_cm_input': float(self.length_cm_input.text()),
                'speed_input': float(self.speed_input.text()),
                'pixel_input': float(self.pixel_input.text())
            }
            self.camera.update_camera_params(ui_input)
        except ValueError:
            pass

    # Toggle
    def toggle_camera(self):
        if self.camera.is_running:
            try:
                self.camera.stop_grabbing()
                self.camera.close()
                self.start_btn.setText("Start Camera")
                self.start_btn.setStyleSheet("background-color: #4CAF50;")
                self.status_bar.showMessage("Camera Stopped")
            except Exception as e:
                QMessageBox.critical(self, "Camera Stop Failed", str(e))
        else:
            try:
                self.camera.open()
                self.sync_ui_to_camera()
                self.camera.start_grabbing()
                self.start_btn.setText("Stop Camera")
                self.start_btn.setStyleSheet("background-color: #E03C3C;")
                self.status_bar.showMessage("Camera Running")
            except Exception as e:
                QMessageBox.critical(self, "Camera Init Failed", str(e))

    def toggle_detection(self, checked):
        self.is_detecting = checked
        if checked:
            self.detect_btn.setText("Stop Detect")
            self.detect_btn.setStyleSheet("background-color: #E03C3C;")
        else:
            self.detect_btn.setText("Start Detect")
            self.detect_btn.setStyleSheet("background-color: #4CAF50;")
            #self.warning_label.hide()
            #self.warning_image_label.hide()

    def manual_direction(self, direction):
        manual_move_mm = self.cfg.get('setting', {}).get('manual_move_mm')
        mm_per_pulses_x = load_env_config().get('motor_mm_per_pulse_x')
        mm_per_pulses_y = load_env_config().get('motor_mm_per_pulse_y')
        pulses_x = int(manual_move_mm / mm_per_pulses_x)
        pulses_y = int(manual_move_mm / mm_per_pulses_y)
        dx, dy, px, py = 0, 0, 0, 0

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
    def handle_inference_result(self, data, q_img):
        if not q_img.isNull():
            self.img_label.setPixmap(QPixmap.fromImage(q_img))
            """
            self.img_label.setPixmap(QPixmap.scaled(self.img_label.size(), 
                                                   Qt.KeepAspectRatio,
                                                   Qt.SmoothTransformation))
            """
        if self.is_detecting:
            f_pt = data.get('first')
            s_pt = data.get('second')

            if f_pt and s_pt:
                pixel_mm = float(self.pixel_input.text())
                dx_mm = (s_pt[0] - f_pt[0]) * pixel_mm
                dy_mm = (s_pt[1] - f_pt[1]) * pixel_mm
                #LogDock.update_plot(dx_mm, dy_mm)

                """
                if abs(dx_mm) > alarm_dist or abs(dy_mm) > alarm_dist:
                    self.warning_label.show()
                    self.warning_image_label.show()
                    if not self.alert_sound.isPlaying():
                        self.alert_sound.play()
                else:
                    self.warning_label.hide()
                    self.warning_image_label.hide()
                """
                print(f"Offset[x:{round(dx_mm, 2)}, y:{round(dy_mm, 2)}]")
                deadband_mm = float(self.threshold_input.text())
                if abs(dx_mm) < deadband_mm: dx_mm = 0
                if abs(dy_mm) < deadband_mm: dy_mm = 0

                mm_per_pulses_x = load_env_config().get('motor_mm_per_pulse_x')
                mm_per_pulses_y = load_env_config().get('motor_mm_per_pulse_y')
                now = time.time() * 1000
                if (now - self.last_send_time) > 500:     #only move every 500ms
                    if dx_mm != 0 or dy_mm != 0:          #dx, dy: 1 = +,  2 = -
                        dx, dy = 1, 1
                        if dx_mm < 0:
                            dx_mm *= -1
                            dx = 2
                        if dy_mm < 0:
                            dy_mm *= -1
                            dy = 2

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
                current_time = time.time()
                if (current_time - self.last_save_time >= self.cooldown_seconds) and \
                   (self.current_save_count < self.max_save_count):
                    
                    img = qimage_to_cv2(q_img)
                    save_image_timed(img, base_path="data/no_match_img")
                    
                    # 更新狀態
                    self.last_save_time = current_time
                    self.current_save_count += 1
                    print(f"目前負樣本數: {self.current_save_count}/500")

                #save img to no_match folder

                #self.warning_label.hide()
                #self.warning_image_label.hide()

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