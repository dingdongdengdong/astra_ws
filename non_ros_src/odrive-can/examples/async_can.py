#!/usr/bin/env python3
"""
 async can usage example

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
import can

# pylint: disable=abstract-class-instantiated
BUS = can.interface.Bus(
    channel="vcan0", interface="socketcan", receive_own_messages=True
)


# Callback function to process received messages
def print_message(msg):
    print(f"callback: {msg}")


# Coroutine to send messages
async def send_messages():
    for i in range(10):
        message = can.Message(arbitration_id=i, data=[i] * 8)
        BUS.send(message)
        print(f"Sent: {message}")
        await asyncio.sleep(0.1)  # Delay to simulate processing

    raise StopIteration("done sending")


# Coroutine to receive messages
async def receive_messages(reader):
    while True:
        msg = await reader.get_message()
        print(f"awaited {msg}")


async def main():
    # Start the sending and receiving coroutines

    reader = can.AsyncBufferedReader()
    notifier = can.Notifier(BUS, [print_message, reader])

    try:
        await asyncio.gather(send_messages(), receive_messages(reader))
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        print("Cleaning up")
        notifier.stop()  # Stop the notifier when done
        BUS.shutdown()


# Run the main coroutine
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
