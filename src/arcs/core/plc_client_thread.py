from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue, Empty
import struct
import socket
import time

from arcs.core.camera_cotroller import Camera
from arcs.core.plc_controller import FX3U_PLC

class PLCClientThread(QThread):
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, ip, port, parent=None):
        super().__init__(parent)

        self.plc = FX3U_PLC()

        self.command_q = Queue(maxsize=2)
        self.running = True

        self.camera = Camera()

        self.infer_thread = self.camera.infer_thread
        self.infer_thread.plc_command_signal.connect(self.enqueue_move)

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
            if self.plc.client is None:
                if not self.plc.is_connected:
                    self.plc.connect()
                    time.sleep(2) # wait 2 sec if connect fail
                    continue

            try:
                dx, dy, px, py = self.command_q.get(timeout=0.1)
            except Empty:
                continue
            
            # send Modbus 
            try:
                success = self.plc.write_D(100, 4, [dx, dy, px, py])
                print({"status": "SUCCESS" if success else "FAIL"})
            except Exception as e:
                self.error.emit(f"PLC Send Error: {e}")
                # Send Error, force close to reconnect
                if self.plc.client:
                    try: self.plc.disconnect()
                    except: pass

        if self.plc.client:
            self.plc.disconnect()
    """
    def _send_move_command(self, dx, dy, px, py):
        # write in register
        data_to_write = struct.pack('<H', dx)+struct.pack('<H', dy)+struct.pack('<H', px)+struct.pack('<H', py)
        frame = b'\x03\xFF\x0A\x00\x64\x00\x00\x00\x20\x44\x04\x00' + data_to_write
        try:
            self.client.sendall(frame)
            response = self.client.recv(1024)
            if response == b'\x83\x00':
                self.status.emit(f"Succes Sent {dx}, {dy}, {px}, {py}")
                return True
            else:
                return False

        except Exception as e:
            raise e
        
    def connect_plc(self):
        #Try connect PLC
        print("try to connect PLC...")
        try:
            temp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_client.settimeout(1)
            temp_client.connect((self.ip, self.port))
            self.client = temp_client
            print("PLC Connected")
            return True
        except (socket.timeout, ConnectionRefusedError, Exception) as e:
            print(f"Connect fail: {e}")
            # 確保失敗時 self.client 是 None
            if 'temp_client' in locals():
                temp_client.close()
            self.client = None 
            return False
    """
    def stop(self):
        self.running = False
        self.wait()