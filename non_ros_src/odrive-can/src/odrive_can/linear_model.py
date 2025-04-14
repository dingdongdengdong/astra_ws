#!/usr/bin/env python3
"""
 Simple linear model for generating setpoints.

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""


from typing import Optional
import math
import time


def sign(x):
    """sign of a number"""
    if x == 0:
        return 0
    return math.copysign(1, x)


class LinearModel:
    """Simple linear model for generating setpoints."""

    __slots__ = ("val", "roc", "setpoint", "min_val", "max_val", "_last_update")

    def __init__(
        self,
        roc: float,
        val: float = 0.0,
        setpoint: Optional[float] = None,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ):
        """
        Args:
            roc (float): rate of change / sec
            val (float): current value
            setpoint (float, optional): target value.
            max_val (float, optional): maximum value
            min_val (float, optional): minimum value
        """

        self.val = val
        self.roc = roc
        if setpoint is None:
            self.setpoint = val
        else:
            self.setpoint = setpoint

        self.min_val = min_val
        self.max_val = max_val
        self._last_update = time.time()

    def step(self, dt: Optional[float] = None) -> float:
        """perform timestep, return actual dt"""

        if dt is None:
            dt = time.time() - self._last_update
            self._last_update = time.time()

        if dt < 0:
            raise ValueError(f"dt must be positive, got {dt=} ")

        error = self.setpoint - self.val
        step = sign(error) * self.roc * dt

        if abs(step) > abs(error):
            self.val += error
        else:
            self.val += step

        if self.max_val is not None:
            self.val = min(self.val, self.max_val)

        if self.min_val is not None:
            self.val = max(self.val, self.min_val)

        return dt

    def __repr__(self) -> str:
        return f"LinearModel(val={self.val}, setpoint={self.setpoint}, roc={self.roc})"
