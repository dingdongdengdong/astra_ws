#!/usr/bin/env python3
"""
 Home odrive

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
from time import sleep

import odrive  # type: ignore
import odrive.enums as enums  # type: ignore

from utils import check_error


drv = odrive.find_any()
print(f"Found ODrive {drv.serial_number}")

drv.clear_errors()
check_error(drv)

ax = drv.axis0

# enable endstop
ax.min_endstop.config.enabled = True
ax.min_endstop.config.is_active_high = True
ax.min_endstop.config.offset = 25.0

ax.requested_state = enums.AxisState.HOMING
sleep(1)
print("Homing...")
while ax.current_state != enums.AxisState.IDLE:
    sleep(1)
    print(".", end="", flush=True)

try:
    check_error(drv)
except Exception as e:
    print(e)
    print("Homing failed")
    exit(1)

print("Homing OK")

# get current position
pos = ax.encoder.pos_estimate
print(f"Current position: {pos}")
