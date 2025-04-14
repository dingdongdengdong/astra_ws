#!/usr/bin/env python3
"""
 demonstrate usage of OdriveCAN class

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging

import coloredlogs  # type: ignore

from odrive_can import LOG_FORMAT, TIME_FORMAT
from odrive_can.odrive import CommandId, ODriveCAN
from odrive_can.tools import UDP_Client
from odrive_can.timer import timeit

log = logging.getLogger()
coloredlogs.install(level="DEBUG", fmt=LOG_FORMAT, datefmt=TIME_FORMAT)


AXIS_ID = 1
INTERFACE = "slcan0"

udp = UDP_Client()


def position_callback(data):
    """position callback, send data to UDP client"""
    udp.send(data)


async def get_bus_voltage_current(drv: ODriveCAN):
    """request bus voltage and current"""

    @timeit
    async def request(drv: ODriveCAN):
        data = await drv.get_bus_voltage_current()
        log.info(f"{data=}")

    log.info("Requesting bus voltage and current")
    # request bus voltage and current
    for _ in range(4):
        log.info("------------------------------")
        try:
            await request(drv)

        except Exception as e:  # pylint: disable=broad-except
            log.warning(e)
        await asyncio.sleep(0.1)


async def position_control(drv: ODriveCAN):
    """simple position control loop"""

    log.info("-----------Running position control-----------------")

    # set positiion to zero
    drv.set_linear_count(0)

    drv.set_controller_mode("POSITION_CONTROL", "POS_FILTER")
    drv.set_pos_gain(3.0)

    # setpoint
    setpoint = 20
    duration = 5

    for _ in range(4):
        try:
            drv.check_errors()
            log.info(f"Setting position setpoint to {setpoint}")
            drv.set_input_pos(setpoint)
            await asyncio.sleep(duration)
            log.info(f"Setting position setpoint to {-setpoint}")
            drv.set_input_pos(-setpoint)
            await asyncio.sleep(duration)

        except Exception as e:  # pylint: disable=broad-except
            log.warning(e)


async def main():
    drv = ODriveCAN(axis_id=AXIS_ID, interface=INTERFACE)
    drv.feedback_callback = position_callback
    await drv.start()

    # log some messages
    await asyncio.sleep(1.0)

    await drv.set_axis_state("CLOSED_LOOP_CONTROL")

    # set log level to INFO
    coloredlogs.set_level(logging.INFO)

    # ignore encoder estimate messages
    drv.ignore_message(CommandId.ENCODER_ESTIMATE)

    # request bus voltage and current
    await get_bus_voltage_current(drv)

    # enable encoder feedback
    drv.allow_message(CommandId.ENCODER_ESTIMATE)

    # reset encoder
    drv.set_linear_count(0)
    await asyncio.sleep(1.0)

    # run position control
    await position_control(drv)

    # shutdown
    drv.stop()
    await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
