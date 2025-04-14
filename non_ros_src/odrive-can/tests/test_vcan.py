import asyncio
from contextlib import asynccontextmanager
import os
import pytest
from odrive_can.mock import ODriveCANMock

from odrive_can.odrive import ODriveCAN, CanMsg


AXIS_ID = 1
CHANNEL = "vcan0"

# enable tests if vcan0 is available
if not os.path.exists("/sys/class/net/vcan0"):
    pytestmark = pytest.mark.skip(reason="No vcan0 present.")


class Feedback:
    """feedback collection class"""

    def __init__(self):
        self.pos = 0
        self.vel = 0

    def feedback_callback(self, msg: CanMsg, caller: ODriveCAN):

        data = msg.data
        self.pos = data["Pos_Estimate"]
        self.vel = data["Vel_Estimate"]


# tried to use a fixture, but it did not work. so using a context manager
@asynccontextmanager
async def odrive_can_context(axis_id=AXIS_ID, channel=CHANNEL):
    odrv = ODriveCANMock(axis_id=axis_id, channel=channel)
    odrv_task = asyncio.create_task(odrv.main())
    await asyncio.sleep(1)  # Allow some time for the mock to initialize
    try:
        yield odrv
    finally:
        odrv_task.cancel()
        try:
            await odrv_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_velocity_control():
    async with odrive_can_context():

        fbk = Feedback()

        drv = ODriveCAN(axis_id=AXIS_ID, interface=CHANNEL)
        drv.feedback_callback = fbk.feedback_callback
        await drv.start()

        drv.check_alive()
        # reset encoder
        drv.set_linear_count(0)

        drv.set_controller_mode("VELOCITY_CONTROL", "VEL_RAMP")

        # set position control mode
        await drv.set_axis_state("CLOSED_LOOP_CONTROL")
        drv.check_errors()

        setpoint = 5
        drv.set_input_vel(setpoint)
        await asyncio.sleep(1)
        assert fbk.vel == setpoint
