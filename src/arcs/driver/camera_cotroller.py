from pypylon import pylon
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

from arcs.utils.config_manager import load_json_config, load_model_path
from arcs.core.camera_thread import CameraGrabberThread

class Camera(QObject):
    raw_frame_signal = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_opened = False
        self.is_running = False
        self.pylon_camera = None
        self.cfg = load_json_config()
        
        self.grab_thread = CameraGrabberThread(self)
        self.grab_thread.raw_frame_signal.connect(self._forward_frame)

    def open(self):
        """
        Open the camera connection.
        """
        factory = pylon.TlFactory.GetInstance()
        self.pylon_camera = pylon.InstantCamera(factory.CreateFirstDevice())
        self.pylon_camera.Open()
        self.is_opened = True

    def start_grabbing(self):
        """Start camera and frame grabbing thread"""
        self.pylon_camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        self.is_running = True
        self.grab_thread.is_running = True
        self.grab_thread.start()

    def stop_grabbing(self):
        """Stop frame grabbing and thread"""
        self.grab_thread.is_running = False
        self.grab_thread.wait()
        
        if self.pylon_camera.IsGrabbing():
            self.pylon_camera.StopGrabbing()
        self.is_running = False

    def close(self):
        """
        Close the camera connection.
        """
        self.pylon_camera.Close()
        self.is_opened = False

    def update_params(self, ui_input: dict) -> None:
        """
        Update camera parameters based on UI input and config.json.
        """
        if not self.is_opened:
            self.open()
        try:
            camera_param = self.cfg.get('camera')
            cm_value     = ui_input.get('length_cm_input')     #cm
            speed_value  = ui_input.get('speed_input')         #m/min
            pixel_value  = ui_input.get('pixel_input')         #mm  

            line_rate_hz = (speed_value*1000) / (pixel_value*60)   #line/s
            exposure_us  = max(1, int(1e6 / line_rate_hz))         #us
            target_height= int((cm_value*10) / pixel_value)        #pixels

            try:
                #self.pylon_camera.PixelFormat.SetValue(camera_param.get('Pixel_format'))
                #self.pylon_camera.GevSCPSPacketSize.SetValue(9014)
                self.pylon_camera.PixelFormat.SetValue("RGB8")
                self.pylon_camera.ReverseX.SetValue(camera_param.get('reverse_x'))
                self.pylon_camera.Width.SetValue(camera_param.get('width'))

                self.pylon_camera.AcquisitionLineRate.SetValue(line_rate_hz)
                self.pylon_camera.ExposureTime.SetValue(exposure_us)
                self.pylon_camera.Height.SetValue(target_height)
                print("success")
            except Exception as e:
                print(f"Error updating camera params: {e}")
                pass
        except Exception as e:
            print(f"Error updating camera params: {e}")

    def grab_frame(self):
        """Legacy method - kept for compatibility"""
        pass
    
    def _forward_frame(self, frame):
        """Forward frame signal from grabber thread"""
        self.raw_frame_signal.emit(frame)
"""
        class MyCameraHandler(pylon.ImageEventHandler):
            def __init__(self, yolo_thread):
                super().__init__()
                self.yolo_thread = yolo_thread

            def OnImageGrabbed(self, camera, grabResult):
                if grabResult.GrabSucceeded():
                    img = grabResult.Array
                    self.yolo_thread.submit_frame(img)
                else:
                    print(f"抓取失敗: {grabResult.ErrorCode}")
        self.handler = MyCameraHandler(self.yolo_thread)
        self.pylon_camera.RegisterImageEventHandler(
            self.handler, 
            pylon.RegistrationMode_ReplaceAll, 
            pylon.Cleanup_Delete
        )
        self.pylon_camera.StartGrabbing(
            pylon.GrabStrategy_LatestImageOnly, 
            pylon.GrabLoop_ProvidedByInstantCamera
        )
"""
    