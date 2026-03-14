from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue, Empty
import time

from arcs.driver.plc_controller import FX3U_PLC

class PLCClientThread(QThread):
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.plc = FX3U_PLC()

        self.command_q = Queue(maxsize=2)
        self.running = True
        
    def enqueue_move(self, dx, dy, px, py):
        try:
            self.command_q.put_nowait((dx, dy, px, py))
            return True
        except:
            try:
                _ = self.command_q.get_nowait()
            except:
                pass
            try:
                self.command_q.put_nowait((dx, dy, px, py))
                return True
            except:
                return False
    
    def run(self):
        while self.running:
            # Connect
            if self.plc.client is None:
                if not self.plc.is_connected:
                    self.plc.connect()
                    time.sleep(2) # wait 2 sec if connect fail
                    continue

            # Get Data
            try:
                dx, dy, px, py = self.command_q.get(timeout=0.1)
            except Empty:
                continue
            
            # Send Data
            try:
                state = self.plc.read_M(10)
                if state == 1:
                    continue
                elif state == 0:
                    success = self.plc.write_D(100, 4, [dx, dy, px, py])
                time.sleep(0.1)

            except Exception as e:
                print(f"PLC Send Error: {e}")
                if self.plc.client:
                    try: 
                        self.plc.disconnect()
                    except: 
                        pass

        if self.plc.client:
            self.plc.disconnect()

    def stop(self):
        self.running = False
        self.wait()