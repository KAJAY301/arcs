import math

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage

from arcs.core.plc_client_thread import PLCClientThread
from arcs.core.inference_thread import InferenceThread

from arcs.driver.camera_cotroller import Camera
from arcs.driver.plc_controller import FX3U_PLC

from arcs.utils.config_manager import load_json_config, load_env_config

class MainCore(QObject):
    """
    Core logic handler for the application.  
    Manages camera, PLC communication, and Inference processing.
    """
    # === Signals to UI === #
    frame_ready = pyqtSignal(QImage)
    log_data = pyqtSignal(list)
    alarm_trigger = pyqtSignal(bool)
    status_msg = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.camera = Camera()
        self.plc = FX3U_PLC()
        self.plc_thread = PLCClientThread()
        self.inference_thread = InferenceThread()
        
        # 1. Camera -> InferenceThread
        self.camera.raw_frame_signal.connect(self.inference_thread.submit_frame)
        # 2. InferenceThread -> PLCClientThread
        self.inference_thread.plc_command_signal.connect(self.plc_thread.enqueue_move)
        # 3. InferenceThread -> Core -> UI
        self.inference_thread.ui_signal.connect(self.process_inference_data)

        # Init parameters
        cfg = load_json_config()
        env = load_env_config()

        manual_move_mm = cfg.get('setting').get('manual_move_mm')
        mm_per_pulses_x = env.get('motor_mm_per_pulse_x')
        mm_per_pulses_y = env.get('motor_mm_per_pulse_y')
        self.pulses_x = int(manual_move_mm / mm_per_pulses_x)
        self.pulses_y = int(manual_move_mm / mm_per_pulses_y)

        self.pixel_size = cfg.get('camera').get('pixel_size_mm')

        self.is_warning = False

        self.plc_thread.start()
        self.inference_thread.start()

    def update_system_parameters(self, ui_input: dict) -> None:
        """
        Update parameters from UI input to InferenceThread and Camera.  
        ui_input = {  
                'length_cm_input': length_cm_input,  
                'speed_input'    : speed_input,  
                'pixel_input'    : pixel_input,  
                'threshold_input': threshold_input  
            }
        """
        try:
            self.inference_thread.update_params(ui_input)
            self.camera.update_params(ui_input)
            self.pixel_size = ui_input["pixel_input"]
            self.status_msg.emit("Synced Parameters Successfully")
        except Exception as e:
            self.error_occurred.emit("Synced Parameters Failed", str(e))
                                 
    # Buttom
    def toggle_camera(self, checked: bool) -> bool:
        if checked:
            if not self.camera.is_opened:
                try:
                    self.camera.open()
                except Exception as e:
                    self.error_occurred.emit("Camera Open Failed", str(e))
                    return False
            try:
                self.camera.start_grabbing()
                self.status_msg.emit("Camera Started")
                return True
            except Exception as e:
                self.error_occurred.emit("Camera Start Failed", str(e))
                return False
        else:
            try:
                self.camera.stop_grabbing()
                self.status_msg.emit("Camera Stopped")
                return True
            except Exception as e:
                self.error_occurred.emit("Camera Stop Failed", str(e))
                return False
            
    def toggle_detection(self, checked: bool) -> bool:
        if checked:
            self.inference_thread.is_detacting = True
            return True
        else:
            self.inference_thread.is_detacting = False
            return True
        
    def toggle_control(self, checked: bool) -> bool:
        if checked:
            self.inference_thread.auto_control = True
            return True
        else:
            self.inference_thread.auto_control = False
            return True

    def manual_move(self, direction: str) -> None:
        """ Manual move command to PLC based on direction. """
        dx, dy, px, py = 2, 2, 0, 0

        if   direction == "UP"   : 
            py = self.pulses_y
            dy = 2
        elif direction == "DOWN" : 
            py = self.pulses_y
            dy = 1
        elif direction == "LEFT" : 
            px = self.pulses_x
            dx = 2
        elif direction == "RIGHT": 
            px = self.pulses_x
            dx = 1

        self.plc_thread.enqueue_move(dx, dy, px, py)

    # Data processing
    def process_inference_data(self, q_img: QImage, data: list) -> None:
        """
        Process inference data and emit signals to UI.  
        """
        if not q_img.isNull():
            self.frame_ready.emit(q_img)
        if data:
            self.log_data.emit(data)
            
            alarm_distance = 1.0 #float(self.setting_dock.alarm_input.value())
            dis_pix = math.dist(data[0], data[1])
            dis_mm = dis_pix * float(self.pixel_size)
            should_alarm = dis_mm > alarm_distance
            if should_alarm != self.is_warning:
                self.is_warning = should_alarm
                self.alarm_trigger.emit(should_alarm)

    def stop(self) -> None:
        if hasattr(self, 'inference_thread') and self.inference_thread.isRunning():
            self.inference_thread.stop()
            self.inference_thread.wait()

        if hasattr(self, 'plc_thread') and self.plc_thread.isRunning():
            self.plc_thread.stop()
            self.plc_thread.wait()

        if hasattr(self, 'camera'):
            if self.camera.is_running:
                self.camera.stop_grabbing()
            if self.camera.is_opened:
                self.camera.close()










