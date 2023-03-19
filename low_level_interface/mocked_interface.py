from functools import wraps

from power_supply_imitator import PowerSupplyImitator
from settings import LOW_INTERFACE_SENT_COMMAND_LOG_BUFFER_SIZE
from .ILowInterface import ILowInterface
from .exceptions import NotEnoughParamsException


class MockedInterface(ILowInterface):
    def __init__(self, host: str, port: int, *args, **kwargs):
        super().__init__(host, port, *args, **kwargs)

        self.sent_command_logs = {}
        self.command_logs_buffer_size = LOW_INTERFACE_SENT_COMMAND_LOG_BUFFER_SIZE

        if 'power_supply_model_object' not in kwargs:
            raise NotEnoughParamsException('You need to give a power supply imitator object for mocking!!')

        self._power_supply: PowerSupplyImitator = kwargs['power_supply_model_object']

    def log_income_commands(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if 'uuid' in kwargs and kwargs['uuid']:
                uid = kwargs['uuid']
                command = args[0]
                if uid in self.sent_command_logs:
                    self.sent_command_logs[uid].append(command)
                else:
                    self.sent_command_logs[uid] = [command]
                if len(self.sent_command_logs) > self.command_logs_buffer_size:
                    self.sent_command_logs.pop(next(iter(self.sent_command_logs)))

            return func(self, *args, **kwargs)
        return wrapper

    def connect(self):
        pass

    @log_income_commands
    def send_text(self, command: str, uuid: str = None) -> str:
        return self._power_supply.eat_message(command)

    def disconnect(self):
        pass

    def get_command_logs_by_uuid(self, uuid: str):
        if uuid in self.sent_command_logs:
            return self.sent_command_logs[uuid]
        return None
