from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue, Empty
import struct
import socket
import time

class PLCClientThread(QThread):
    ack_received = pyqtSignal(dict)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, ip, port, parent=None):
        super().__init__(parent)
        self.ip = ip
        self.port = port
        self.command_q = Queue(maxsize=2)
        self.running = True
        self.client = None

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

    def run(self):
        while self.running:
            # reconnect
            if self.client is None:
                if not self.connect_plc():
                    time.sleep(2) # wait 2 sec if connect fail
                    continue

            try:
                dx, dy, px, py = self.command_q.get(timeout=0.1)
            except Empty:
                continue
            
            # send Modbus 
            try:
                ok = self._send_move_command(int(dx), int(dy), int(px), int(py))
                self.ack_received.emit({"status": "OK" if ok else "FAIL"})
            except Exception as e:
                self.error.emit(f"PLC Send Error: {e}")
                # Send Error, force close to reconnect
                if self.client:
                    try: self.client.close()
                    except: pass
                self.client = None

        if self.client:
            self.client.close()

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

    def stop(self):
        self.running = False
        self.wait()