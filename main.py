import asyncio

from driver import Driver
from high_level_interface import DefaultHighInterface
from low_level_interface import MockedInterface
from power_supply_imitator import PowerSupplyImitator

if __name__ == '__main__':
    driver = Driver(
        DefaultHighInterface(
            low_interface=MockedInterface(
                host='',
                port=0,
                power_supply_model_object=PowerSupplyImitator()
            )
        ))

    asyncio.run(driver.run())
