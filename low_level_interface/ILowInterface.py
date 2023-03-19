from abc import ABC, abstractmethod


class ILowInterface(ABC):
    """
    Интерфейс низкоуровнего интерфейса, задача которого принять SCPI команду и передать её конечному устройству
    """
    def __init__(self, host: str, port: int, *args, **kwargs):
        self.host = host
        self.port = port
        self.connection = None

    @abstractmethod
    def connect(self):
        """
        Connect to a programmable instrument
        :return: None
        """
        ...

    @abstractmethod
    def send_text(self, command: str, uuid: str = None) -> str:
        """
        Send a text command to device
        :param uuid: uuid of request
        :param command: str with a command
        :return: str with an answer
        """
        ...

    @abstractmethod
    def disconnect(self):
        """
        Disconnect from the device
        :return: None
        """
        ...
