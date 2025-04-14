from dataclasses import dataclass, field, replace

import cv2
import numpy as np
import torch

from astra_controller.astra_controller import AstraController

from lerobot.common.robot_devices.utils import RobotDeviceAlreadyConnectedError, RobotDeviceNotConnectedError
from lerobot.common.robot_devices.robots.configs import AstraRobotConfig

########################################################################
# Astra robot arm
########################################################################


class AstraRobot:
    """
    Example of highest frequency teleoperation without camera:
    ```python
    # Defines how to communicate with the motors of the leader and follower arms
    astra_controller = AstraController(
        
    )
    robot = AstraRobot(astra_controller)
    # Connect motors buses and cameras if any (Required)
    robot.connect()
    while True:
        robot.teleop_step()
    ```
    Example of highest frequency data collection without camera:
    ```python
    # Assumes leader and follower arms have been instantiated already (see first example)
    robot = AstraRobot(astra_controller)
    robot.connect()
    while True:
        observation, action = robot.teleop_step(record_data=True)
    ```
    Example of highest frequency data collection with cameras:
    ```python
    # Defines how to communicate with 2 cameras connected to the computer.
    # Here, the webcam of the mackbookpro and the iphone (connected in USB to the macbookpro)
    # can be reached respectively using the camera indices 0 and 1. These indices can be
    # arbitrary. See the documentation of `OpenCVCamera` to find your own camera indices.
    cameras = {
        "macbookpro": OpenCVCamera(camera_index=0, fps=30, width=640, height=480),
        "iphone": OpenCVCamera(camera_index=1, fps=30, width=640, height=480),
    }
    # Assumes leader and follower arms have been instantiated already (see first example)
    robot = AstraRobot(astra_controller)
    robot.connect()
    while True:
        observation, action = robot.teleop_step(record_data=True)
    ```
    Example of controlling the robot with a policy (without running multiple policies in parallel to ensure highest frequency):
    ```python
    # Assumes leader and follower arms + cameras have been instantiated already (see previous example)
    robot = AstraRobot(astra_controller)
    robot.connect()
    while True:
        # Uses the follower arms and cameras to capture an observation
        observation = robot.capture_observation()
        # Assumes a policy has been instantiated
        with torch.inference_mode():
            action = policy.select_action(observation)
        # Orders the robot to move
        robot.send_action(action)
    ```
    Example of disconnecting which is not mandatory since we disconnect when the object is deleted:
    ```python
    robot.disconnect()
    ```
    """

    def __init__(
        self,
        config: AstraRobotConfig | None = None,
        **kwargs,
    ):
        if config is None:
            config = AstraRobotConfig()
        # Overwrite config arguments using kwargs
        self.config = replace(config, **kwargs)
        
        self.robot_type = self.config.type

        self.astra_controller: AstraController = AstraController(
            space=self.config.space
        )
        self.is_connected = False
        self.logs = {}

    @property
    def camera_features(self) -> dict:
        cam_ft = {}
        for cam_key in ["head", "wrist_left", "wrist_right"]:
            key = f"observation.images.{cam_key}"
            cam_ft[key] = {
                "shape": (360, 640, 3),
                "names": ["height", "width", "channels"],
                "info": None,
            }
        return cam_ft

    @property
    def motor_features(self) -> dict:
        features = {
            "action.arm_l": {
                "dtype": "float32",
                "shape": (6,),
                "names": list(range(6)),
            },
            "action.gripper_l": {
                "dtype": "float32",
                "shape": (1,),
                "names": list(range(1)),
            },
            "action.arm_r": {
                "dtype": "float32",
                "shape": (6,),
                "names": list(range(6)),
            },
            "action.gripper_r": {
                "dtype": "float32",
                "shape": (1,),
                "names": list(range(1)),
            },
            "action.base": {
                "dtype": "float32",
                "shape": (2,),
                "names": list(range(6)),
            },
            "action.eef_l": {
                "dtype": "float32",
                "shape": (7,),
                "names": list(range(7)),
            },
            "action.eef_r": {
                "dtype": "float32",
                "shape": (7,),
                "names": list(range(7)),
            },

            "action.head": {
                "dtype": "float32",
                "shape": (2,),
                "names": list(range(2)),
            },
            
            "observation.state.arm_l": {
                "dtype": "float32",
                "shape": (6,),
                "names": list(range(6)),
            },
            "observation.state.gripper_l": {
                "dtype": "float32",
                "shape": (1,),
                "names": list(range(1)),
            },
            "observation.state.arm_r": {
                "dtype": "float32",
                "shape": (6,),
                "names": list(range(6)),
            },
            "observation.state.gripper_r": {
                "dtype": "float32",
                "shape": (1,),
                "names": list(range(1)),
            },
            "observation.state.base": {
                "dtype": "float32",
                "shape": (2,),
                "names": list(range(6)),
            },
            "observation.state.eef_l": {
                "dtype": "float32",
                "shape": (7,),
                "names": list(range(7)),
            },
            "observation.state.eef_r": {
                "dtype": "float32",
                "shape": (7,),
                "names": list(range(7)),
            },
            "observation.state.odom": {
                "dtype": "float32",
                "shape": (7,),
                "names": list(range(7)),
            },

            "observation.state.head": {
                "dtype": "float32",
                "shape": (2,),
                "names": list(range(2)),
            },
        }
        
        if self.astra_controller.space == "joint":
            return {
                "action": {
                    "dtype": "float32",
                    "shape": (6+1+6+1+2+2,),
                    "names": list(range(6+1+6+1+2+2)),
                },
                "observation.state": {
                    "dtype": "float32",
                    "shape": (6+1+6+1+2+2,),
                    "names": list(range(6+1+6+1+2+2)),
                },
                **features,
            }
        elif self.astra_controller.space == "cart":
            raise NotImplementedError("Cartesian space is not supported for now")
        else:
            return features

    @property
    def features(self):
        return {**self.motor_features, **self.camera_features}

    def connect(self):
        if self.is_connected:
            raise RobotDeviceAlreadyConnectedError(
                "AstraRobot is already connected. Do not run `robot.connect()` twice."
            )

        if not self.astra_controller:
            raise ValueError(
                "AstraRobot doesn't have any device to connect. See example of usage in docstring of the class."
            )

        # Connect the arms
        self.astra_controller.connect()

        self.is_connected = True

    def wait_for_reset(self):
        self.astra_controller.wait_for_reset()

    def teleop_step(
        self, record_data=False
    ) -> None | tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
        if not self.is_connected:
            raise RobotDeviceNotConnectedError(
                "AstraRobot is not connected. You need to run `robot.connect()`."
            )

        assert record_data, "Please use Astra Web Teleop"

        # Prepare to assign the positions of the leader to the follower
        action, action_arm_l, action_gripper_l, action_arm_r, action_gripper_r, action_base, action_eef_l, action_eef_r, action_head = self.astra_controller.read_leader_present_position()

        # Leader-follower process will be automatically handle in astra controller.
        # Reason for that is we want to deliver image from device camera to the operator as soon as possible.
        # Also, delay of arm is all over the place. Strictly do as aloha does may not be necessary.
        # TODO delay consideration

        obs_dict = self.capture_observation()

        action_dict = {}
        if self.astra_controller.space == 'joint' or self.astra_controller.space == 'cartesian':
            action_dict["action"] = torch.from_numpy(np.array(action)).to(torch.float32)
        action_dict["action.arm_l"] = torch.from_numpy(np.array(action_arm_l)).to(torch.float32)
        action_dict["action.gripper_l"] = torch.from_numpy(np.array(action_gripper_l)).to(torch.float32)
        action_dict["action.arm_r"] = torch.from_numpy(np.array(action_arm_r)).to(torch.float32)
        action_dict["action.gripper_r"] = torch.from_numpy(np.array(action_gripper_r)).to(torch.float32)
        action_dict["action.base"] = torch.from_numpy(np.array(action_base)).to(torch.float32)
        action_dict["action.eef_l"] = torch.from_numpy(np.array(action_eef_l)).to(torch.float32)
        action_dict["action.eef_r"] = torch.from_numpy(np.array(action_eef_r)).to(torch.float32)
        action_dict["action.head"] = torch.from_numpy(np.array(action_head)).to(torch.float32)

        return obs_dict, action_dict

    def capture_observation(self):
        """The returned observations do not have a batch dimension."""
        if not self.is_connected:
            raise RobotDeviceNotConnectedError(
                "AstraRobot is not connected. You need to run `robot.connect()`."
            )

        # TODO(rcadene): Add velocity and other info
        # Read follower position
        state, state_arm_l, state_gripper_l, state_arm_r, state_gripper_r, state_base, state_eef_l, state_eef_r, state_odom, state_head = self.astra_controller.read_present_position()

        # Capture images from cameras
        images = self.astra_controller.read_cameras()

        # Populate output dictionnaries and format to pytorch
        obs_dict = {}
        if self.astra_controller.space == 'joint' or self.astra_controller.space == 'cartesian':
            obs_dict["observation.state"] = torch.from_numpy(np.array(state)).to(torch.float32)
        obs_dict["observation.state.arm_l"] = torch.from_numpy(np.array(state_arm_l)).to(torch.float32)
        obs_dict["observation.state.gripper_l"] = torch.from_numpy(np.array(state_gripper_l)).to(torch.float32)
        obs_dict["observation.state.arm_r"] = torch.from_numpy(np.array(state_arm_r)).to(torch.float32)
        obs_dict["observation.state.gripper_r"] = torch.from_numpy(np.array(state_gripper_r)).to(torch.float32)
        obs_dict["observation.state.base"] = torch.from_numpy(np.array(state_base)).to(torch.float32)
        obs_dict["observation.state.eef_l"] = torch.from_numpy(np.array(state_eef_l)).to(torch.float32)
        obs_dict["observation.state.eef_r"] = torch.from_numpy(np.array(state_eef_r)).to(torch.float32)
        obs_dict["observation.state.odom"] = torch.from_numpy(np.array(state_odom)).to(torch.float32)
        obs_dict["observation.state.head"] = torch.from_numpy(np.array(state_head)).to(torch.float32)

        # Convert to pytorch format: channel first and float32 in [0,1]
        for name in images:
            obs_dict[f"observation.images.{name}"] = torch.from_numpy(images[name])
            
        obs_dict["done"] = self.astra_controller.done
        self.astra_controller.done = False

        return obs_dict

    def send_action(self, action: torch.Tensor):
        """The provided action is expected to be a vector."""
        if not self.is_connected:
            raise RobotDeviceNotConnectedError(
                "AstraRobot is not connected. You need to run `robot.connect()`."
            )

        self.astra_controller.write_goal_position(action.tolist())
        
        action_dict = {}
        action_dict["action"] = action
        action_dict["action.arm_l"] = torch.zeros(6).to(torch.float32)
        action_dict["action.gripper_l"] = torch.zeros(1).to(torch.float32)
        action_dict["action.arm_r"] = torch.zeros(6).to(torch.float32)
        action_dict["action.gripper_r"] = torch.zeros(1).to(torch.float32)
        action_dict["action.base"] = torch.zeros(2).to(torch.float32)
        action_dict["action.eef_l"] = torch.zeros(7).to(torch.float32)
        action_dict["action.eef_r"] = torch.zeros(7).to(torch.float32)
        action_dict["action.head"] = torch.zeros(2).to(torch.float32)
        
        return action_dict

    def log_control_info(self, log_dt):
        pass

    def disconnect(self):
        if not self.is_connected:
            raise RobotDeviceNotConnectedError(
                "AstraRobot is not connected. You need to run `robot.connect()` before disconnecting."
            )

        self.astra_controller.disconnect()

        self.is_connected = False

    def __del__(self):
        if getattr(self, "is_connected", False):
            self.disconnect()