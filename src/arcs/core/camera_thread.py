from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import time
from pypylon import pylon


class CameraGrabberThread(QThread):
    """Frame acquisition thread - prevents UI blocking from camera delays"""
    raw_frame_signal = pyqtSignal(np.ndarray)
    
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.is_running = False
        self.frame_interval = 0.05
    
    def run(self):
        """Main loop: grab frames in dedicated thread"""
        last_grab_time = 0
        
        while self.is_running:
            try:
                current_time = time.time()
                elapsed = current_time - last_grab_time
                
                # Use frame_interval from mock camera if available
                frame_interval = getattr(self.camera.pylon_camera, 'frame_interval', self.frame_interval)
                
                if elapsed < frame_interval and last_grab_time > 0:
                    time.sleep(frame_interval - elapsed)
                
                res = self.camera.pylon_camera.RetrieveResult(500, pylon.TimeoutHandling_ThrowException)
                if res.GrabSucceeded():
                    img = res.Array
                    self.raw_frame_signal.emit(img)
                res.Release()
                last_grab_time = time.time()
            except Exception:
                pass
