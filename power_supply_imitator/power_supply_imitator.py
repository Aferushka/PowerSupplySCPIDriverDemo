from datetime import datetime
from functools import wraps

from settings import SCPI_COMMAND_TRANSLATION_LOGS, IMITATOR_ACTION_EXECUTION_LOGS
from .scpi_translator import SCPITranslator


class PowerSupplyImitator:
    """
    GPP-4323
    The 4 channel programmable DC power supply
    """

    # Ограничения по току и напряжению по каналам
    channel_limitations = {
        1: {
            'V': 32.0,
            'A': 3.0
        },
        2: {
            'V': 32.0,
            'A': 3.0
        },
        3: {
            'V': 5.0,
            'A': 1.0
        },
        4: {
            'V': 15.0,
            'A': 1.0
        },
    }

    def __init__(self):
        # Установка начального состояния модели
        self.state = {channel_number + 1: {
            'voltage': 0.0,
            'current': 0.0,
            'state': 'OFF'
        } for channel_number in range(4)}

        self.scpi_translator = SCPITranslator()

    def eat_message(self, command: str) -> str:
        """
        Получить SCPI команду и преобразовать через транслятор SCPI в название метода и параметры
        """
        translated_command = self.scpi_translator.translate(command)
        if SCPI_COMMAND_TRANSLATION_LOGS:
            print(f'SCPI: {command} ---> {translated_command}')

        return self.__getattribute__(translated_command['command'])(**translated_command['kwargs'])

    def validate_params(action):
        """
        Декоратор для валидации номера канала, величин тока и напряжения
        В случае превышения - ограничение максимальным значением для данного канала
        """
        @wraps(action)
        def wrapper(self, *args, **kwargs):
            channel = kwargs.get('channel', 1)
            if channel not in self.state:
                raise WrongChannelException(f'Available channels: {self.state.keys()}')
            if 'current' in kwargs:
                current = kwargs['current']
                max = self.channel_limitations[channel]['A']
                if current > max:
                    kwargs['current'] = max
            if 'voltage' in kwargs:
                voltage = kwargs['voltage']
                max = self.channel_limitations[channel]['V']
                if voltage > max:
                    kwargs['voltage'] = max
            if IMITATOR_ACTION_EXECUTION_LOGS:
                print(f'IMITATOR: Execute {action.__name__} with {kwargs}')
            return action(self, *args, **kwargs)

        return wrapper

    @validate_params
    def set_current(self, channel, current):
        """
        Установить величину тока на выбранном канале
        """
        self.state[channel]['current'] = current

    @validate_params
    def set_voltage(self, channel, voltage):
        """
        Установить величину напряжения на выбранном канале
        """
        self.state[channel]['voltage'] = voltage

    @validate_params
    def set_channel(self, channel, state):
        """
        Включить/отключить выбранный канал
        """
        self.state[channel]['state'] = state

    @validate_params
    def get_all_measure_from_channel(self, channel):
        """
        Отдать величины тока, напряжения, мощности по выбранному каналу с указанием метки времени измерения
        """
        state = self.state[channel]
        if state['state'] == 'ON':
            power = state['current'] * state['voltage']
        else:
            power = 0.0

        return {**state, 'power': power, 'timestamp': datetime.strftime(datetime.now(), '%Y.%m.%d %H-%M-%S-%f')}


class WrongChannelException(Exception):
    pass
