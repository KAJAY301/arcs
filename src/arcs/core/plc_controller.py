import socket

from arcs.utils.config_manager import load_env_config

class FX3U_PLC:
    def __init__(self):
        self.client = None
        self.ip = load_env_config().get("PLC_IP")
        self.port = load_env_config().get("PLC_PORT")

        self.is_connected = False
        self.is_running = False

    def connect(self):
        """
        Try connect PLC
        """
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(30)
            self.client.connect((self.ip, self.port))
            self.is_connected = True
            print("PLC Connected")
        except socket.timeout:
            print("PLC Connect Timeout")
            return False
        except ConnectionRefusedError:
            print("PLC Refuse Connect")
            return False
        except Exception as e:
            print(f"Other Error: {e}")
            return False

    def run(self):
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

    def stop(self):
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
            print("PLC Disconnected")

    def write(self):
        pass

    def read(self):
        pass