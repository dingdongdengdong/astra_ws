#!/usr/bin/env python3
"""
 Timing utilities

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""
import asyncio
import time
import logging
from functools import wraps


def timeit(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(
            f"Async function {func.__name__!r} executed in {end_time - start_time:.4f} seconds"
        )
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(
            f"Function {func.__name__!r} executed in {end_time - start_time:.4f} seconds"
        )
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class Timer:
    """Timer class, including timeout"""

    def __init__(self, timeout):
        self.timeout = timeout
        self.start_time = time.time()

    def is_timeout(self):
        """Check if timeout has expired"""
        return time.time() - self.start_time > self.timeout

    def reset(self):
        """Reset timer"""
        self.start_time = time.time()

    def elapsed(self):
        """Return elapsed time since timer was started"""
        return time.time() - self.start_time
