#!/usr/bin/env python3
"""
 Example of setpoint generation using linear model

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
from odrive_can.tools import UDP_Client
from odrive_can.setpoints import sawtooth_generator


DELAY = 0.1


async def main():
    """main"""

    udp = UDP_Client()

    generator = sawtooth_generator(roc=5.0)

    while True:
        setpoint = next(generator)
        udp.send({"setpoint": setpoint})
        await asyncio.sleep(DELAY)
        # print(".", end="", flush=True)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nexiting")
