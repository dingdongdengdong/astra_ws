#!/usr/bin/env python3
"""
 simple acceleration test

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import time
import asyncio
import odrive  # type: ignore
import odrive.enums as enums  # type: ignore
from utils import check_error

from odrive_can.tools import UDP_Client


RAMP_RATE = 200
SETPOINT = 40

drv = odrive.find_any()

print(f"Found ODrive {drv.serial_number}")

drv.clear_errors()
drv.axis0.requested_state = enums.AxisState.CLOSED_LOOP_CONTROL

check_error(drv)

# configure velocity control
drv.axis0.controller.config.input_mode = enums.InputMode.VEL_RAMP
drv.axis0.controller.config.control_mode = enums.ControlMode.VELOCITY_CONTROL
drv.axis0.controller.config.vel_ramp_rate = RAMP_RATE  # this only works with VEL_RAMP
drv.axis0.controller.config.vel_limit = 150.0
drv.axis0.motor.config.current_lim = 10.0

# check correct setti


async def feedback_loop():
    ax = drv.axis0
    udp = UDP_Client()

    while True:
        check_error(drv)

        data = {
            "ts": time.time(),
            "sp": ax.controller.input_vel,
            "vel": ax.encoder.vel_estimate,
            "pos": ax.encoder.pos_estimate,
        }

        udp.send(data)
        await asyncio.sleep(0.05)


async def setpoint_loop():
    while True:
        drv.axis0.controller.input_vel = SETPOINT
        await asyncio.sleep(2)
        drv.axis0.controller.input_vel = -SETPOINT
        await asyncio.sleep(2)


async def main():
    await asyncio.gather(feedback_loop(), setpoint_loop())


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
finally:
    drv.axis0.controller.input_vel = 0
    drv.axis0.requested_state = enums.AxisState.IDLE
