from abc import ABC

from low_level_interface import ILowInterface


class IHighInterface(ABC):
    """
    Интерфейс высокоуровнего интерфейса, задача которого абстрагировать набор SCPI команд для конкретных действий (
    например обновить ток и напряжение и включить канал)
    """
    def __init__(self, low_interface: ILowInterface):
        self.low_interface = low_interface

    async def get_telemetry(self, uuid: str = None):
        return {channel + 1: self.low_interface.send_text(f':MEASure{channel + 1}:ALL', uuid=uuid) for channel in range(4)}

    async def turn_on_channel(self, channel_number: int, voltage: float, current: float, uuid: str = None):
        root = f':SOURce{channel_number}'
        # Set channel current level
        self.low_interface.send_text(f'{root}:CURRent {current}', uuid=uuid)

        # Set channel voltage level
        self.low_interface.send_text(f'{root}:VOLTage {voltage}', uuid=uuid)

        # Set channel state to ON
        self.low_interface.send_text(f':OUTPut{channel_number}:STATe ON', uuid=uuid)

    async def turn_off_channel(self, channel_number, uuid: str = None):
        # Set channel state to OFF
        self.low_interface.send_text(f':OUTPut{channel_number}:STATe OFF', uuid=uuid)
