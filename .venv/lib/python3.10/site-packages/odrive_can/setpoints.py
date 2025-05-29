#!/usr/bin/env python3
"""
 Handy setpoint generators for testing etc.

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import time
from odrive_can.linear_model import LinearModel


def sawtooth_generator(roc: float = 10.0, max_val: float = 20.0):
    model = LinearModel(
        roc=roc, val=0.0, setpoint=100.0, min_val=-max_val, max_val=max_val
    )
    t = time.time()

    while True:
        dt = time.time() - t  # Calculate time elapsed since last update of t

        model.step(dt)
        # print(f"{dt=}, {model.val=} {t=}")
        if model.val >= max_val:
            model.val = -max_val

        t = time.time()
        yield model.val  # Yield the current value
