import socket
import struct

from PyQt5.QtCore import QObject

from arcs.utils.config_manager import load_env_config

class FX3U_PLC(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = None
        self.ip = load_env_config().get("plc_ip")
        self.port = load_env_config().get("plc_port")

        self.is_connected = False
        self.is_running = False

    def connect(self) -> bool:
        """
        Try connect PLC
        """
        try:
            temp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_client.settimeout(1)
            temp_client.connect((self.ip, self.port))
            self.client = temp_client
            self.is_connected = True
            print("PLC Connected")
            return True
        except (socket.timeout, ConnectionRefusedError, Exception) as e:
            print(f"Connect fail: {e}")
            # 確保失敗時 self.client 是 None
            if 'temp_client' in locals():
                temp_client.close()
            self.client = None 
            self.is_connected = False
            return False

    def run(self) -> bool:
        """
        PLC Remote RUN
        """
        #FX3U-ENET-L USER'S MANUAL P.189
        if self.is_connected and not self.is_running:
            try:
                data = b'\x13\xFF\x0A\x00'
                self.client.sendall(data)
                response = self.client.recv(1024)
                if response == b'\x93\x00':
                    self.is_running = True
                    return True
                else:
                    return False
            except Exception as e:
                raise e

    def stop(self) -> bool:
        """
        PLC Remote STOP
        """
        #FX3U-ENET-L USER'S MANUAL P.189
        if self.is_connected and self.is_running:
            try:
                data = b'\x14\xFF\x0A\x00'
                self.client.sendall(data)
                response = self.client.recv(1024)
                if response == b'\x94\x00':
                    self.is_running = False
                    return True
                else:
                    return False
            except Exception as e:
                raise e

    def disconnect(self):
        if self.is_connected:
            try:
                self.client.shutdown(socket.SHUT_RDWR)
            except (OSError, socket.error):
                pass
            self.client.close()
            self.is_connected = False
            self.client = None
            print("PLC Disconnected")

    def write_D(self, D_start: int, D_point:int, values: list) -> bool:
        """
        Write values to D registers
        """
        data_to_write = b''
        for val in values:
            data_to_write += struct.pack('<H', val)
        frame = b'\x03\xFF\x0A\x00\x64\x00\x00\x00\x20\x44\x04\x00' + data_to_write
        try:
            self.client.sendall(frame)
            response = self.client.recv(1024)
            if response == b'\x83\x00':
                return True
            else:
                return False
        except Exception as e:
            raise e

    def read_M(self, M_number: int) -> int:
        """
        Read a single M register
        """
        number = struct.pack("<I", M_number)
        frame = b'\x00\xFF\x0A\x00' + number + b'\x20\x4D\x01\x00'
        try:
            self.client.sendall(frame)
            response = self.client.recv(1024)
            if response == b'\x80\x00\x10':
                return 1
            elif response == b'\x80\x00\x00':
                return 0
        except Exception as e:
            raise e
        