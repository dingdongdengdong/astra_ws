#!/usr/bin/env python3
"""
 Inspect and decode ODrive CAN messages

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import can
import odrive_can

TIMEOUT = 1.0


def receive_and_decode(bus):
    dbc = odrive_can.get_dbc()
    nr_timeouts = 0
    idx = 0  # message index
    while True:
        msg = bus.recv(TIMEOUT)  # type: ignore

        if msg is None:
            print(".", end="", flush=True)
            nr_timeouts += 1
            continue
            # raise TimeoutError("Timeout occurred, no message.")

        # start new line if there were timeouts
        if nr_timeouts > 0:
            print("\n")
            nr_timeouts = 0

        axis_id = odrive_can.get_axis_id(msg)

        print(f"[{idx}] ", end="")

        if msg.is_remote_frame:
            # RTR messages are requests for data, they don't have a data payload
            db_msg = dbc.get_message_by_frame_id(msg.arbitration_id)
            print(f"Axis{axis_id} RTR: {db_msg.name}")
            continue

        try:
            # Attempt to decode the message using the DBC file
            db_msg = dbc.get_message_by_frame_id(msg.arbitration_id)
            decoded_message = db_msg.decode(
                msg.data
            )  # Remove msg.arbitration_id as it's not needed for decoding
            print(f"{db_msg.name}:{decoded_message}")
        except KeyError:
            # If the message ID is not in the DBC file, print the raw message
            print(f"Axis{axis_id} Raw Message: {msg}")

        idx += 1


def main(interface: str = "vcan0"):
    # Load the DBC file

    bus = can.Bus(channel=interface, interface="socketcan", receive_own_messages=True)

    try:
        receive_and_decode(bus)
    except KeyboardInterrupt:
        print("Stopped")
    except TimeoutError as error:
        print(error)
    finally:
        bus.shutdown()


if __name__ == "__main__":
    main()
