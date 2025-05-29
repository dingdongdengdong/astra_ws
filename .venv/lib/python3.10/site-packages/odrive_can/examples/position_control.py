#!/usr/bin/env python3
"""
 Demonstration of position control using CAN interface

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
import time
import logging
from odrive_can.odrive import ODriveCAN, CanMsg
from odrive_can.tools import UDP_Client

SETTLE_TIME = 5.0  # settle time in [s]


log = logging.getLogger("pos_ctl")
udp = UDP_Client()


def feedback_callback(msg: CanMsg, caller: ODriveCAN):
    """position callback, send data to UDP client"""
    data = msg.data
    data["setpoint"] = caller.setpoint
    data["ts"] = time.time()
    udp.send({f"axis_{msg.axis_id}": data}, add_timestamp=False)


async def configure_controller(
    drv: ODriveCAN, input_mode: str = "POS_FILTER", accel: float = 120.0
):
    """setup control parameters"""

    # set parameters
    drv.set_pos_gain(5.0)

    drv.set_traj_vel_limit(40.0)
    drv.set_traj_accel_limits(accel, accel)

    # reset encoder
    drv.set_linear_count(0)

    drv.set_controller_mode("POSITION_CONTROL", input_mode)

    # set position control mode
    await drv.set_axis_state("CLOSED_LOOP_CONTROL")
    drv.check_errors()


async def main_loop(
    drv: ODriveCAN, input_mode: str = "POS_FILTER", amplitude: float = 40.0
):
    """position demo"""

    log.info("-----------Running position control-----------------")

    await drv.start()

    await asyncio.sleep(0.5)
    drv.check_alive()
    drv.clear_errors()
    drv.check_errors()

    drv.feedback_callback = feedback_callback

    await configure_controller(drv, input_mode)

    # start running

    drv.set_input_pos(amplitude)
    await asyncio.sleep(2)

    idx = 0
    try:
        while True:
            drv.check_errors()

            drv.set_input_pos(amplitude)
            idx += 1
            await asyncio.sleep(SETTLE_TIME)
            amplitude = -amplitude

    except KeyboardInterrupt:
        log.info("Stopping")
    finally:
        drv.stop()
        await asyncio.sleep(0.5)


def main(
    axis_id: int,
    interface: str,
    input_mode: str = "POS_FILTER",
    amplitude: float = 40.0,
):
    print("Starting position control demo, press CTRL+C to exit")
    drv = ODriveCAN(axis_id, interface)

    try:
        asyncio.run(main_loop(drv, input_mode, amplitude))
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt")


if __name__ == "__main__":
    import coloredlogs  # type: ignore
    from odrive_can import LOG_FORMAT, TIME_FORMAT  # pylint: disable=ungrouped-imports

    coloredlogs.install(level="INFO", fmt=LOG_FORMAT, datefmt=TIME_FORMAT)

    main(1, "slcan0")
