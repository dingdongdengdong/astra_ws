#!/usr/bin/env python3
"""
 simple acceleration test

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import asyncio
import odrive  # type: ignore
import odrive.enums as enums  # type: ignore
from utils import check_error

from odrive_can.tools import UDP_Client

DURATION = 5
SETPOINT = 20

drv = odrive.find_any()
ax = drv.axis0

print(f"Found ODrive {drv.serial_number}")

drv.clear_errors()

check_error(drv)

ax.controller.config.control_mode = enums.ControlMode.POSITION_CONTROL
ax.controller.config.input_mode = enums.InputMode.TRAP_TRAJ
ax.requested_state = enums.AxisState.CLOSED_LOOP_CONTROL
ax.controller.config.input_filter_bandwidth = 4.0
ax.motor.config.current_lim = 15.0
ax.controller.config.vel_limit = 50.0


# trajectory control
ax.trap_traj.config.vel_limit = 40.0
ax.trap_traj.config.accel_limit = 40.0
ax.trap_traj.config.decel_limit = 40.0


# position control
ax.controller.config.pos_gain = 3.0

# set positiion to zero
ax.encoder.set_linear_count(0)


async def feedback_loop():
    udp = UDP_Client()

    while True:
        check_error(drv)

        data = {
            "sp": ax.controller.input_pos,
            "vel": ax.encoder.vel_estimate,
            "pos": ax.encoder.pos_estimate,
        }

        udp.send(data)
        await asyncio.sleep(0.05)


async def setpoint_loop():
    while True:
        ax.controller.input_pos = SETPOINT
        await asyncio.sleep(DURATION)
        ax.controller.input_pos = -SETPOINT
        await asyncio.sleep(DURATION)


async def main():
    await asyncio.gather(feedback_loop(), setpoint_loop())


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
finally:
    ax.controller.input_vel = 0
    ax.requested_state = enums.AxisState.IDLE
