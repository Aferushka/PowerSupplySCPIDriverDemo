import socket

from .ILowInterface import ILowInterface


class AlmostRealInterface(ILowInterface):
    def connect(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((self.host, self.port))

    def send_text(self, command: str, **kwargs) -> str:
        self.connection.sendall(command.encode())
        return self.connection.recv(4096).decode()

    def disconnect(self):
        self.connection.close()
