#!/usr/bin/env python3
# pylint: disable=broad-except, redefined-outer-name
import asyncio
import logging
import argparse
import coloredlogs  # type: ignore

from odrive_can import LOG_FORMAT, TIME_FORMAT
from odrive_can.odrive import ODriveCAN
from odrive_can.timer import timeit

log = logging.getLogger()
coloredlogs.install(level="INFO", fmt=LOG_FORMAT, datefmt=TIME_FORMAT)

# set can logger to INFO
logger_can = logging.getLogger("can").setLevel(logging.INFO)  # type: ignore


def parse_args():
    parser = argparse.ArgumentParser(description="ODrive CAN test script")
    parser.add_argument("--axis-id", type=int, default=0, help="ODrive axis ID")
    parser.add_argument("--interface", type=str, default="vcan0", help="CAN interface")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


@timeit
async def request(drv: ODriveCAN, method: str):
    """request data from ODrive"""
    log.info(f"Requesting {method}")
    fcn = getattr(drv, method)
    data = await fcn()
    log.info(f"{data=}")


async def main(args):
    if args.debug:
        coloredlogs.set_level("DEBUG")

    try:
        drv = ODriveCAN(axis_id=args.axis_id, interface=args.interface)
        await drv.start()

        drv.check_alive()
        drv.check_errors()

        for param in [
            "get_bus_voltage_current",
            "get_motor_error",
            "get_encoder_error",
            "get_sensorless_error",
            "get_encoder_estimates",
            "get_encoder_count",
            "get_iq",
            "get_sensorless_estimates",
            "get_adc_voltage",
            "get_controller_error",
        ]:
            await request(drv, param)

        # set velocity control mode
        log.info("Setting velocity control mode")
        await drv.set_axis_state("CLOSED_LOOP_CONTROL")
        log.info(f"Currrent axis state: {drv.axis_state}")
        await asyncio.sleep(1)

    except Exception as e:  # pylint: disable=broad-except
        log.error(e)
    finally:
        drv.stop()
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt")
    except Exception as e:
        log.error(e)
