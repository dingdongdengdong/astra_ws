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
