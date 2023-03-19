import asyncio
import copy
import json
from abc import ABC

import aiohttp

from driver import Driver
from high_level_interface import DefaultHighInterface
from low_level_interface import MockedInterface
from power_supply_imitator import PowerSupplyImitator
from settings import REST_API_PORT


def get_test_instances() -> (Driver, PowerSupplyImitator):
    """
    Инициализировать и вернуть объекты драйвера, интерфейса и модели блока питания
    """
    imitator = PowerSupplyImitator()
    low_interface = MockedInterface(
        host='',
        port=0,
        power_supply_model_object=imitator
    )
    driver = Driver(
        DefaultHighInterface(
            low_interface=low_interface
        ))

    return driver, low_interface, imitator


class AbstractTestCase(ABC):
    """
    Интерфейс тест кейсов с методами стартовой инициализации объектов и асинхронных запросов к REST API
    """
    driver, low_interface, imitator = get_test_instances()

    async def get_request_result(self, path, method: str = 'get', data: dict = None):
        """
        Запустить драйвер, выполнить запрос, после чего остановить драйвер и вернуть результат запроса
        """
        driver_task = asyncio.create_task(self.driver.run())
        request_task = asyncio.create_task(self.make_request(path, method, data))
        request_task.add_done_callback(driver_task.cancel)

        await asyncio.gather(
            driver_task,
            request_task,
            return_exceptions=True
        )

        return request_task.result()

    @staticmethod
    async def make_request(path: str, method: str = 'get', data: dict = None):
        """
        Выполнить запрос к REST API и вернуть результат
        """
        async with aiohttp.ClientSession() as session:
            session_method = session.post if method == 'post' else session.get
            kwargs = {'url': path}
            if data:
                kwargs['data'] = json.dumps(data)
            async with session_method(**kwargs) as resp:
                res = await resp.read()
                return resp.status, json.loads(res) if res else '', resp.headers


class TestCheckPowerSupplyStateChange(AbstractTestCase):
    """
    Проверка логики обновления состояния модели
    """
    @staticmethod
    def remove_timestamp(data: dict):
        new_data = copy.deepcopy(data)
        for value_dict in new_data.values():
            value_dict.pop('timestamp')
        return new_data

    async def test_state_change(self):
        # Получаем начальное состояние телеметрии
        status_code, data, _ = await self.get_request_result(f'http://localhost:{REST_API_PORT}/')

        assert status_code == 200
        assert self.remove_timestamp(data['telemetry']) == {
            '1': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '2': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '3': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '4': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0}}

        # Включаем 1 канал
        status_code, _, _ = await self.get_request_result(
            f'http://localhost:{REST_API_PORT}/channel_on',
            'post',
            {'channel': 1, 'current': 2.0, 'voltage': 10.0}
        )

        assert status_code == 200

        # Проверяем, что состояние канала обновлилось нужными данными
        status_code, data, _ = await self.get_request_result(f'http://localhost:{REST_API_PORT}/')

        assert status_code == 200
        assert self.remove_timestamp(data['telemetry']) == {
            '1': {'voltage': 10.0, 'current': 2.0, 'state': 'ON', 'power': 20.0},
            '2': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '3': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '4': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0}}

        # Отключаем 1 канал
        status_code, _, _ = await self.get_request_result(
            f'http://localhost:{REST_API_PORT}/channel_off',
            'post',
            {'channel': 1}
        )

        assert status_code == 200

        # Проверяем, что состояние канала обновлилось
        status_code, data, _ = await self.get_request_result(f'http://localhost:{REST_API_PORT}/')

        assert status_code == 200
        assert self.remove_timestamp(data['telemetry']) == {
            '1': {'voltage': 10.0, 'current': 2.0, 'state': 'OFF', 'power': 0.0},
            '2': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '3': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0},
            '4': {'voltage': 0.0, 'current': 0.0, 'state': 'OFF', 'power': 0.0}}


class TestDriverRouting(AbstractTestCase):
    """
    Проверка корректности роутинга API
    """
    async def test_route_telemetry(self):
        status_code, _, headers = await self.get_request_result(f'http://localhost:{REST_API_PORT}/')

        assert status_code == 200
        assert headers['Method-Routing'] == 'telemetry'

    async def test_route_channel_on(self):
        status_code, _, headers = await self.get_request_result(
            f'http://localhost:{REST_API_PORT}/channel_on',
            'post',
            {'channel': 1, 'current': 2.0, 'voltage': 10.0}
        )

        assert status_code == 200
        assert headers['Method-Routing'] == 'turn_channel_on'

    async def test_route_channel_off(self):
        status_code, _, headers = await self.get_request_result(
            f'http://localhost:{REST_API_PORT}/channel_off',
            'post',
            {'channel': 1}
        )

        assert status_code == 200
        assert headers['Method-Routing'] == 'turn_channel_off'


class TestSentSCPICommands(AbstractTestCase):
    """
    Проверка корректности отправленных команд
    """
    async def test_telemetry(self):
        status_code, _, headers = await self.get_request_result(f'http://localhost:{REST_API_PORT}/')

        assert status_code == 200
        assert self.low_interface.get_command_logs_by_uuid(headers['uuid']) == [':MEASure1:ALL', ':MEASure2:ALL',
                                                                                ':MEASure3:ALL', ':MEASure4:ALL']

    async def test_channel_on(self):
        status_code, _, headers = await self.get_request_result(
            f'http://localhost:{REST_API_PORT}/channel_on',
            'post',
            {'channel': 1, 'current': 2.0, 'voltage': 10.0}
        )

        assert status_code == 200
        assert self.low_interface.get_command_logs_by_uuid(headers['uuid']) == [':SOURce1:CURRent 2.0',
                                                                                ':SOURce1:VOLTage 10.0',
                                                                                ':OUTPut1:STATe ON']

    async def test_channel_off(self):
        status_code, _, headers = await self.get_request_result(
            f'http://localhost:{REST_API_PORT}/channel_off',
            'post',
            {'channel': 1}
        )

        assert status_code == 200
        assert self.low_interface.get_command_logs_by_uuid(headers['uuid']) == [':OUTPut1:STATe OFF']
