#!/usr/bin/env python3
"""
 utils for odrive testing

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""


class OdriveError(Exception):
    """custom exception"""


def check_error(drv):
    """check if there are any errors"""

    ax = drv.axis0

    errors = [
        ("ax.error", ax.error),
        ("ax.motor.error", ax.motor.error),
        ("ax.encoder.error", ax.encoder.error),
        ("ax.controller.error", ax.controller.error),
        ("ax.sensorless_estimator.error", ax.sensorless_estimator.error),
    ]

    for var_name, var_value in errors:
        if var_value > 0:
            raise OdriveError(f"Error in {var_name}: {var_value}")
