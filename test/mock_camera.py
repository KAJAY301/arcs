import cv2
import time
import traceback
from itertools import cycle
from pathlib import Path
from unittest.mock import patch, MagicMock
from arcs.main import main

class MockGrabResult:
    def __init__(self, image_array):
        self.Array = image_array

    def GrabSucceeded(self):
        return True

    def Release(self):
        pass

class MockInstantCamera:
    def __init__(self, *args, **kwargs):
        self.frame_interval = 0.5  # Test frame rate control in worker thread

        self.img_dir = Path("test/test_img")
        self.img_extensions = ('.jpg')
        
        self.img_paths = [
            str(p) for p in self.img_dir.glob("*") 
            if p.suffix.lower() in self.img_extensions
        ]
        
        if not self.img_paths:
            raise FileNotFoundError(f"Can't find any image at {self.img_dir} ")
        
        self.image_cycle = cycle(self.img_paths)
        print(f"Mocking camera with {len(self.img_paths)} image")

    def Open(self):
        print("camera open")

    def StartGrabbing(self, strategy=None):
        print("camera start grabbing")

    def IsGrabbing(self): 
        return True

    def RetrieveResult(self, timeout, grab_strategy):
        img_path = next(self.image_cycle)
        if img_path is None:
            return MagicMock(GrabSucceeded=lambda: False)
            
        frame = cv2.imread(img_path)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return MockGrabResult(frame)

    def StopGrabbing(self): 
        print("stop grabbing")

    def Close(self): 
        print("close")

mock_factory = MagicMock()
mock_factory.CreateFirstDevice.return_value = "Mock_Basler_Device"


with patch('pypylon.pylon.TlFactory.GetInstance', return_value=mock_factory), \
     patch('pypylon.pylon.InstantCamera', new=MockInstantCamera):
    
    print("active ARCS (mock camera)...")
    try:
        main()
    except Exception:
        traceback.print_exc()