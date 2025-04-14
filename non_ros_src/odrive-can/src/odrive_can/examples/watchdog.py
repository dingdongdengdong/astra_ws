#!/usr/bin/env python3
"""
 Watchdog demo.

 1. Set costant velocity and continue sending setpoints
 2. pause sending for 3 seconds
 3. check for watchdog, reset if needed and resume sending setpoints

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging

from odrive_can.odrive import ODriveCAN

from odrive_can.tools import UDP_Client
from odrive_can.utils import run_main_async

from odrive_can.examples.position_control import feedback_callback

VERSION = "2024.02.17"

SETPOINT_DELAY = 0.1


log = logging.getLogger("watchdog")
udp = UDP_Client()

setpoint_enabled = True


async def configure_controller(drv: ODriveCAN):
    """setup control parameters"""

    log.info("Configuring controller")

    drv.clear_errors()

    # reset encoder
    drv.set_linear_count(0)

    drv.set_controller_mode("VELOCITY_CONTROL", "VEL_RAMP")

    # set position control mode
    await drv.wait_for_heartbeat()
    drv.check_errors()
    await drv.set_axis_state("CLOSED_LOOP_CONTROL")
    # await drv.wait_for_heartbeat()


async def setpoint_loop(drv: ODriveCAN, setpoint: float):
    """send setpoints if enabled"""

    log.info("Sending setpoints")
    while True:

        drv.check_errors()

        if setpoint_enabled:
            drv.set_input_vel(setpoint)

        await asyncio.sleep(SETPOINT_DELAY)


async def setpoint_enabler():
    """enable setpoints after 3 seconds"""

    global setpoint_enabled

    while True:
        log.info("Enabling setpoints")
        setpoint_enabled = True
        await asyncio.sleep(3)
        log.info("Disabling setpoints")
        setpoint_enabled = False
        await asyncio.sleep(3)


async def main(axis_id: int, interface: str, amplitude: float = 40.0):
    """velocity control demo"""
    global setpoint_enabled

    log.info(f"Running watchdog demo on axis {axis_id} using {interface}")

    drv = ODriveCAN(axis_id, interface)

    drv.feedback_callback = feedback_callback
    await drv.start()

    await configure_controller(drv)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(setpoint_loop(drv, amplitude))
            tg.create_task(setpoint_enabler())
    except ExceptionGroup as e:  # Catch the ExceptionGroup
        for exception in e.exceptions:  # Access and handle subexceptions
            log.error(exception)
    finally:
        drv.stop()
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    run_main_async(main(1, "can0"))
