#!/usr/bin/env python3
"""
 mock ODrive CAN interface

 This is just a rough mock, not a complete simulation. This model uses
 infinite acceleration for example

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging
from typing import Optional

import can
import coloredlogs  # type: ignore

from odrive_can import LOG_FORMAT, TIME_FORMAT, get_axis_id, get_dbc
from odrive_can.linear_model import LinearModel

# pylint: disable=abstract-class-instantiated, unnecessary-lambda, broad-except

# set can logger to INFO
logger_can = logging.getLogger("can").setLevel(logging.INFO)  # type: ignore


class OdriveMock:
    """mock physical ODrive device, excluding CAN interface"""

    def __init__(self, roc: float = 10.0, logger: Optional[logging.Logger] = None):
        """mock ODrive device

        Args:
            roc (float, optional): rate of change (velocity of poisition). Defaults to 10.0.
            logger (Optional[logging.Logger], optional): logger object. Defaults to None.
        """
        self.log = logger or logging.getLogger("odrive_mock")
        self.model = LinearModel(roc=roc)

        self.axis_state = "IDLE"
        self.input_mode = "INACTIVE"
        self.control_mode = "VELOCITY_CONTROL"

        self._accum_pos = 0.0  # accumulated position, when in velocity mode
        self._accum_pos_prev = 0.0  # previous accumulated position

        # velocity estimate when in position mode
        self._velocity_estimate = 0.0

    async def set_axis_state(self, data: dict):
        """set axis state"""
        state = data["Axis_Requested_State"]
        self.log.info(f"Setting axis state to {state}")
        await asyncio.sleep(0.5)
        self.axis_state = state
        self.log.info(f"Axis state is now {self.axis_state}")

    def set_controller_mode(self, data: dict):
        """set controller mode"""
        self.log.info(f"Setting controller mode to {data}")
        self.control_mode = data["Control_Mode"]
        self.input_mode = data["Input_Mode"]

    def set_input_pos(self, pos: float):
        """position setpoint"""
        if self.control_mode != "POSITION_CONTROL":
            self.log.warning("Ignoring setpoint. Not in position control mode")
            return
        self.log.debug(f"Setting input pos to {pos}")
        self.model.setpoint = pos

    def set_input_vel(self, vel: float):
        """velocity setpoint"""
        if self.control_mode != "VELOCITY_CONTROL":
            self.log.warning("Ignoring setpoint. Not in velocity control mode")
            return
        self.log.debug(f"Setting input vel to {vel}")
        self.model.setpoint = vel

    @property
    def position(self) -> float:
        """position"""
        if self.control_mode == "POSITION_CONTROL":
            return self.model.val
        elif self.control_mode == "VELOCITY_CONTROL":
            return self._accum_pos
        else:
            return 0.0

    @property
    def velocity(self) -> float:
        """velocity"""
        if self.control_mode == "POSITION_CONTROL":
            return self._velocity_estimate
        elif self.control_mode == "VELOCITY_CONTROL":
            return self.model.val
        else:
            return 0.0

    def update(self):
        """update model"""
        dt = self.model.step()
        if self.control_mode == "VELOCITY_CONTROL":
            self._accum_pos += self.model.val * dt
        elif self.control_mode == "POSITION_CONTROL":
            self._accum_pos = self.model.val

        self._velocity_estimate = (self._accum_pos - self._accum_pos_prev) / dt
        self._accum_pos_prev = self._accum_pos


class ODriveCANMock:
    """class to mock ODrive CAN interface"""

    def __init__(
        self, axis_id: int = 0, channel: str = "vcan0", interface: str = "socketcan"
    ):
        self.log = logging.getLogger(f"odrive.mock.{axis_id}")

        self.log.info(f"Starting mock {axis_id=} , {channel=} , {interface=}")
        self.dbc = get_dbc()
        self.axis_id = axis_id

        self.bus = can.interface.Bus(channel=channel, interface=interface)
        self.can_reader = can.AsyncBufferedReader()
        self.notifier = can.Notifier(self.bus, [self.can_reader])

        self.odrive = OdriveMock(logger=self.log)

    async def message_handler(self):
        """handle received message"""

        self.log.info("Starting message handler")

        while True:
            try:
                msg = await self.can_reader.get_message()

                if get_axis_id(msg) != self.axis_id:
                    # Ignore messages that aren't for this axis
                    continue

                db_msg = self.dbc.get_message_by_frame_id(msg.arbitration_id)

                if msg.is_remote_frame:
                    # RTR messages are requests for data, they don't have a data payload
                    self.log.debug(f"Get: {db_msg.name}")
                    # echo RTR messages back with data
                    self.send_message(db_msg.name)
                    continue

                # decode message data
                data = db_msg.decode(msg.data)
                cmd = db_msg.name.split("_", 1)[1]  # remove "AxisX_" prefix

                await self.execute_cmd(cmd, data)

            except KeyError:
                # If the message ID is not in the DBC file, print the raw message
                self.log.warning(f"Could not decode: {msg}")
            except Exception as e:
                self.log.error(f"Error: {e}")

    async def execute_cmd(self, cmd: str, data: dict):
        """execute command"""
        self.log.debug(f"Set: {cmd}: {data}")

        if cmd == "Set_Axis_State":
            await self.odrive.set_axis_state(data)
        elif cmd == "Set_Controller_Mode":
            self.odrive.set_controller_mode(data)
        elif cmd == "Set_Input_Pos":
            self.odrive.set_input_pos(data["Input_Pos"])
        elif cmd == "Set_Input_Vel":
            self.odrive.set_input_vel(data["Input_Vel"])

    def send_message(
        self, msg_name: str, msg_dict: Optional[dict] = None, rtr: bool = False
    ):
        """send message by name. If no msg_dict is provided, use zeros"""
        msg = self.dbc.get_message_by_name(msg_name)
        if rtr:
            # For RTR messages, don't specify the data field
            msg = can.Message(
                arbitration_id=msg.frame_id,
                is_extended_id=False,
                is_remote_frame=True,
            )
        else:
            full_msg_dict = {signal.name: 0 for signal in msg.signals}
            if msg_dict is not None:
                full_msg_dict.update(msg_dict)

            data = msg.encode(full_msg_dict)
            msg = can.Message(
                arbitration_id=msg.frame_id,
                data=data,
                is_extended_id=False,
            )

        self.bus.send(msg)  # type: ignore

    async def heartbeat_loop(self, delay: float = 0.2):
        """send heartbeat message"""
        self.log.info("Starting heartbeat loop")

        # Fetch the "Axis0_Heartbeat" message from the DBC database
        heartbeat_msg = self.dbc.get_message_by_name(f"Axis{self.axis_id}_Heartbeat")

        while True:
            # Construct the data payload using the DBC message definition
            data = heartbeat_msg.encode(
                {
                    "Axis_Error": 0,
                    "Axis_State": self.odrive.axis_state,
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
            self.bus.send(message)

            await asyncio.sleep(delay)

    async def encoder_loop(self, delay: float = 0.1):
        """send encoder message"""
        self.log.info("Starting encoder loop")

        msg = self.dbc.get_message_by_name(f"Axis{self.axis_id}_Get_Encoder_Estimates")

        while True:
            self.odrive.update()
            data = msg.encode(
                {
                    "Pos_Estimate": self.odrive.position,
                    "Vel_Estimate": self.odrive.velocity,
                }
            )
            message = can.Message(
                arbitration_id=msg.frame_id, data=data, is_extended_id=False
            )
            self.bus.send(message)

            await asyncio.sleep(delay)

    async def main(self):
        """main loop"""

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.heartbeat_loop())
            tg.create_task(self.encoder_loop())
            tg.create_task(self.message_handler())

    def start(self):
        """start the main loop"""
        asyncio.run(self.main())

    def __del__(self):
        """destructor"""
        self.notifier.stop()
        self.bus.shutdown()


def main(axis_id: int = 0, interface: str = "vcan0"):
    try:
        mock = ODriveCANMock(axis_id, interface)
        mock.start()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")


if __name__ == "__main__":
    coloredlogs.install(level="DEBUG", fmt=LOG_FORMAT, datefmt=TIME_FORMAT)
    main()
