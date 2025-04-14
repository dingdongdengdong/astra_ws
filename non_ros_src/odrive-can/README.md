# Asyncio driver for ODrive V3.6


Command ODrive over CAN with a simple interface.


**Source code:** [https://gitlab.com/roxautomation/components/odrive-can](https://gitlab.com/roxautomation/components/odrive-can)

**Documentation:** [https://roxautomation.gitlab.io/components/odrive-can](https://roxautomation.gitlab.io/components/odrive-can)


## Features

* designed to work with `asyncio`
* implements full odrive can protocol.
* includes `OdriveMock` class for device simulation
* cli tools for message inspection, backup and demo's.

## Installation

    pip install odrive-can

## Basic usage

```python
import asyncio
from odrive_can import ODriveCAN, CanMsg
from odrive_can.tools import UDP_Client

AXIS_ID = 0
INTERFACE = "vcan0"
SETPOINT = 50

udp = UDP_Client()  # send data to UDP server for plotting


def feedback_callback_fcn(msg: CanMsg, caller: ODriveCAN):
    """called on position estimate"""
    print(msg)
    udp.send(msg.data)


async def main():
    """connect to odrive"""
    drv = ODriveCAN(axis_id=AXIS_ID, interface=INTERFACE)

    # set up callback (optional)
    drv.feedback_callback = feedback_callback_fcn

    # start
    await drv.start()

    # check errors (raises exception if any)
    drv.check_errors()

    # set controller mode
    drv.set_controller_mode("POSITION_CONTROL", "POS_FILTER")

    # reset encoder
    drv.set_linear_count(0)

    # set axis state
    await drv.set_axis_state("CLOSED_LOOP_CONTROL")

    # set position gain
    drv.set_pos_gain(3.0)

    for _ in range(2):
        # setpoint
        drv.set_input_pos(SETPOINT)
        await asyncio.sleep(5.0)
        drv.set_input_pos(-SETPOINT)
        await asyncio.sleep(5.0)

    drv.set_input_pos(0.0)


asyncio.run(main())


```


## CLI interface

    Usage: odrive_can [OPTIONS] COMMAND [ARGS]...

    Options:
    --help  Show this message and exit.

    Commands:
    backup   Backup config to config folder
    demo     demonstration of control modes
    info     Print package info
    inspect  Inspect and decode ODrive CAN messages
    mock     Mock ODrive CAN interface


## Using virtual devices

1. create a virtual can adapter (see [docs](https://odrive-can-roxautomation-components-9f5f4b809336bc0ecbd5b8cd8e4.gitlab.io/can_tools/#virtual-can))
2. in first terminal run `odrive_can mock`
3. in second terminal run `odrive_can inspect vcan0`



## Position control demo

    odrive_can demo position --interface vcan0

### Live plotting data

Demo scripts send data as `json` to `udp://localhost:5005` .
This data can be visualized with [plotjuggler](https://plotjuggler.io/)

(sender code is found in `tools.UDP_Client`)




## Development

### Virtual environment

create virtual envrionment with   `make venv`

### Devcontainer

* `docker` folder contains devcontainer environment.
* `.devcontainer` is VSCode devcontainer environment



## Support

commercial support is available through [www.roxautomation.com](https://www.roxautomation.com)
