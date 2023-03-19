import asyncio
import json
import uuid
from datetime import datetime

from aiohttp import web
from aiohttp.web import middleware

from high_level_interface import IHighInterface
from settings import DRIVER_TELEMETRY_DELAY, DRIVER_SHOW_TELEMETRY, REST_API_PORT, DRIVER_TELEMETRY_LOG_FILENAME


class Driver:
    def __init__(self, interface: IHighInterface):
        self.interface = interface

    @middleware
    async def add_method_trace(self, request, handler):
        """
        Добавить в response мета-данные о конечном методе
        """
        resp = await handler(request)
        resp.headers['Method-Routing'] = handler.__name__
        return resp

    @middleware
    async def add_uuid(self, request, handler):
        """
        Добавить в метод и в response уникальный идентификатор запроса
        """
        uid = str(uuid.uuid4())
        resp = await handler(request, uid)
        resp.headers['Uuid'] = uid
        return resp

    async def gather_telemetry(self):
        """
        Метод сбора и сохранения телеметрии с состоянием каналов блока питания в файл
        """
        while True:
            tele_task = asyncio.create_task(self.interface.get_telemetry())
            await tele_task
            if DRIVER_SHOW_TELEMETRY:
                print(tele_task.result())
            with open(DRIVER_TELEMETRY_LOG_FILENAME, 'a') as file:
                file.write(f'{datetime.strftime(datetime.now(), "%Y.%m.%d %H-%M-%S-%f")} Telemetry:\n')
                for key, data in tele_task.result().items():
                    file.write(f'    Channel {key}:\n')
                    file.write(f'        State: {data["state"]}\n')
                    file.write(f'        Current: {data["current"]}A\n')
                    file.write(f'        Voltage: {data["voltage"]}V\n')
                    file.write(f'        Power: {data["power"]}W\n')
                    file.write(f'        Timestamp: {data["timestamp"]}\n')
                file.write('\n\n')
            await asyncio.sleep(DRIVER_TELEMETRY_DELAY)

    async def telemetry(self, _, uid: str = None):
        """
        REST метод получения телеметрии
        """
        return web.Response(text=json.dumps({'telemetry': await self.interface.get_telemetry(uuid=uid)}), status=200)

    async def turn_channel_on(self, request, uid: str = None):
        """
        REST метод включения/обновления параметров канала
        """
        data = await request.json()
        if not all(param in data for param in ('channel', 'current', 'voltage')):
            return web.Response(text=json.dumps({'error': 'You need to pass channel, current and voltage as body!'}),
                                status=400)

        await self.interface.turn_on_channel(
            channel_number=data['channel'],
            voltage=data['voltage'],
            current=data['current'],
            uuid=uid
        )

        return web.Response(status=200)

    async def turn_channel_off(self, request, uid: str = None):
        """
        REST метод отключения канала
        """
        data = await request.json()
        if 'channel' not in data:
            return web.Response(text=json.dumps({'error': 'You need to pass channel as body!'}), status=400)

        await self.interface.turn_off_channel(
            channel_number=data['channel'],
            uuid=uid
        )

        return web.Response(status=200)

    async def start_rest_api(self):
        """
        Инициализация и запуск REST API
        """
        rest_api = web.Application(
            middlewares=[
                self.add_method_trace,
                self.add_uuid,
            ]
        )

        rest_api.add_routes([
            web.get('/', self.telemetry),
            web.post('/channel_on', self.turn_channel_on),
            web.post('/channel_off', self.turn_channel_off)
        ])

        await web._run_app(rest_api, port=REST_API_PORT, print=lambda _: None)

    async def run(self):
        """
        Запуск сбора телеметрии и REST API
        """
        await asyncio.gather(
            self.gather_telemetry(),
            self.start_rest_api(),
        )
