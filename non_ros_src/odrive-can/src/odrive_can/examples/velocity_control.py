#!/usr/bin/env python3
"""
 Demonstration of velocity control using CAN interface

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging

from odrive_can.odrive import ODriveCAN
from odrive_can.setpoints import sawtooth_generator
from odrive_can.tools import UDP_Client
from odrive_can.utils import run_main_async

from odrive_can.examples.position_control import feedback_callback

VERSION = "2024.02.17"

SETPOINT_DELAY = 0.1


log = logging.getLogger("pos_ctl")
udp = UDP_Client()


async def configure_controller(drv: ODriveCAN):
    """setup control parameters"""

    # reset encoder
    drv.set_linear_count(0)

    drv.set_controller_mode("VELOCITY_CONTROL", "VEL_RAMP")

    # set position control mode
    await drv.set_axis_state("CLOSED_LOOP_CONTROL")
    await drv.wait_for_heartbeat()
    drv.check_errors()


async def main(axis_id: int, interface: str, amplitude: float = 40.0):
    """velocity control demo"""

    log.info(f"Running velocity control demo on axis {axis_id} using {interface}")

    drv = ODriveCAN(axis_id, interface)

    drv.feedback_callback = feedback_callback
    await drv.start()

    await asyncio.sleep(0.5)
    drv.check_alive()
    log.info("Clearing errors")
    drv.clear_errors()
    await drv.wait_for_heartbeat()
    drv.check_errors()

    await configure_controller(drv)

    # make setpoint generator
    setpoint_gen = sawtooth_generator(roc=10.0, max_val=40.0)

    log.info("Running velocity control")
    try:
        while True:
            drv.check_errors()
            setpoint = next(setpoint_gen)

            drv.set_input_vel(setpoint)
            await asyncio.sleep(SETPOINT_DELAY)

    finally:
        drv.stop()
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    run_main_async(main(1, "can0"))
