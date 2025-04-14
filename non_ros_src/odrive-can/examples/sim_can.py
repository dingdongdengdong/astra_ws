#!/usr/bin/env python3
"""
 simulate CAN messages for ODrive

 1. setup virtual CAN interface on host. Use `install/setup_vcan_service.sh` script for that.
 2. terminal1: `candump vcan0`
 3. terminal2: `python3 sim_can.py`

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""


import asyncio
import can

import odrive_can

# pylint: disable=abstract-class-instantiated
BUS = can.interface.Bus(channel="vcan0", interface="socketcan")


async def send_heartbeat(dbc, axis_id):
    print("Starting heartbeat loop")

    # Fetch the "Axis0_Heartbeat" message from the DBC database
    heartbeat_msg = dbc.get_message_by_name(f"Axis{axis_id}_Heartbeat")

    while True:
        # Construct the data payload using the DBC message definition
        data = heartbeat_msg.encode(
            {
                "Axis_Error": 0,
                "Axis_State": 0,
                "Motor_Error_Flag": 0,
                "Encoder_Error_Flag": 0,
                "Controller_Error_Flag": 0,
                "Trajectory_Done_Flag": 0,
            }
        )

        # Send the message
        message = can.Message(
            arbitration_id=heartbeat_msg.frame_id, data=data, is_extended_id=False
        )
        BUS.send(message)

        await asyncio.sleep(1)


async def encoder_loop(dbc, axis_id, delay=0.1):
    print("Starting encoder loop")
    position = 0.0
    while True:
        encoder_msg = dbc.get_message_by_name(f"Axis{axis_id}_Get_Encoder_Estimates")
        data = encoder_msg.encode({"Pos_Estimate": position, "Vel_Estimate": 0.0})
        message = can.Message(
            arbitration_id=encoder_msg.frame_id, data=data, is_extended_id=False
        )
        BUS.send(message)
        position += 0.01  # Increment position to simulate movement
        await asyncio.sleep(delay)


async def main():
    # Load the DBC file
    dbc = odrive_can.get_dbc()

    axis_id = 0  # Change to your desired axis ID

    async with asyncio.TaskGroup() as tg:
        tg.create_task(send_heartbeat(dbc, axis_id))
        tg.create_task(encoder_loop(dbc, axis_id))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        BUS.shutdown()
