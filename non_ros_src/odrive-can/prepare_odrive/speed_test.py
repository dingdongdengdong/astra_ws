#!/usr/bin/env python3
"""
 simple test of velocity control

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import time

import odrive  # type: ignore
import odrive.enums as enums  # type: ignore
from utils import check_error

from odrive_can.tools import UDP_Client

# send data to plotjuggler
udp = UDP_Client()

drv = odrive.find_any()


print(f"Found ODrive {drv.serial_number}")

drv.clear_errors()
drv.axis0.controller.config.control_mode = enums.ControlMode.VELOCITY_CONTROL
drv.axis0.requested_state = enums.AxisState.CLOSED_LOOP_CONTROL
drv.axis0.config.enable_watchdog = False

# limit acceleration
drv.axis0.controller.config.vel_ramp_rate = 10


# set positiion to zero
drv.axis0.encoder.set_linear_count(0)


SMOOTH_PROFILE = (
    list(range(0, 50))
    + 20 * [50]
    + list(range(50, -50, -1))
    + 20 * [-50]
    + list(range(-50, 0))
)


def follow_curve(setpoints, delay=0.02):
    """follow curve consisting of velocity setpoints"""

    for setpoint in setpoints:
        check_error(drv)

        drv.axis0.controller.input_vel = setpoint

        data = {
            "ts": time.time(),
            "sp": setpoint,
            "vel": drv.axis0.encoder.vel_estimate,
            "pos": drv.axis0.encoder.pos_estimate,
        }

        udp.send(data)
        time.sleep(delay)


try:
    print("---------------------Smooth profile---------------------")
    i = 0
    while True:
        print(f"run {i}")
        follow_curve(SMOOTH_PROFILE)
        i += 1


except KeyboardInterrupt:
    print("interrupted")
finally:
    drv.axis0.controller.input_vel = 0
    drv.axis0.requested_state = enums.AxisState.IDLE
