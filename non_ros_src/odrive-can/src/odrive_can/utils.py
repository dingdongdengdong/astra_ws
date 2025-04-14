#!/usr/bin/env python3
"""
 support functions

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import asyncio
import logging
import os
from functools import wraps
from pathlib import Path
from typing import Any, Coroutine

import can
import cantools
import coloredlogs  # type: ignore

LOG_FORMAT = "%(asctime)s [%(name)s] %(filename)s:%(lineno)d - %(message)s"
TIME_FORMAT = "%H:%M:%S.%f"


def get_axis_id(msg: can.Message) -> int:
    """get axis id from message"""
    return msg.arbitration_id >> 5


def extract_ids(can_id: int) -> tuple[int, int]:
    """get axis_id and cmd_id from can_id"""
    cmd_id = can_id & 0x1F  # Extract lower 5 bits for cmd_id
    axis_id = can_id >> 5  # Shift right by 5 bits to get axis_id
    return axis_id, cmd_id


# pylint: disable=import-outside-toplevel
def get_dbc(name: str = "odrive-cansimple-0.5.6"):
    """get the cantools database"""

    # get relative path to db file
    dbc_path = Path(__file__).parent / f"dbc/{name}.dbc"

    return cantools.database.load_file(dbc_path.as_posix())


def run_main_async(coro: Coroutine[Any, Any, None]) -> None:
    """convenience function to avoid code duplication"""
    loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
    coloredlogs.install(level=loglevel, fmt=LOG_FORMAT, datefmt=TIME_FORMAT)
    logging.info(f"Log level set to {loglevel}")

    try:
        asyncio.run(coro)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(e)


def async_timeout(timeout: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout)
            except asyncio.TimeoutError:
                func_name = func.__name__
                # Include the function name in the error message
                raise TimeoutError(f"{func_name} timed out after {timeout} seconds")

        return wrapper

    return decorator
