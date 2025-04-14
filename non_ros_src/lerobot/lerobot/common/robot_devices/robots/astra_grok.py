from dataclasses import dataclass, field, replace
import cv2
import numpy as np
import torch
from astra_controller.astra_controller import AstraController
from lerobot.common.robot_devices.utils import RobotDeviceAlreadyConnectedError, RobotDeviceNotConnectedError
from lerobot.common.robot_devices.robots.configs import AstraRobotConfig

# Define the AstraRobot class for controlling the Astra robot.
class AstraRobot:
    def __init__(self, config: AstraRobotConfig | None = None, **kwargs):
        # Use default config if none provided, and override with kwargs.
        if config is None:
            config = AstraRobotConfig()
        self.config = replace(config, **kwargs)  # Replace config fields with any provided kwargs.
        self.robot_type = self.config.type  # Store robot type (e.g., "astra", "astra_joint").
        self.astra_controller: AstraController = AstraController(space=self.config.space)  # Initialize controller.
        self.is_connected = False  # Track connection status.
        self.logs = {}  # Placeholder for logs (not implemented).

    @property
    def camera_features(self) -> dict:
        # Define features for head, wrist_left, and wrist_right cameras.
        cam_ft = {}
        for cam_key in ["head", "wrist_left", "wrist_right"]:
            key = f"observation.images.{cam_key}"
            cam_ft[key] = {
                "shape": (360, 640, 3),  # Image dimensions: height, width, channels.
                "names": ["height", "width", "channels"],  # Dimension names.
                "info": None,  # Additional info (currently unused).
            }
        return cam_ft

    @property
    def motor_features(self) -> dict:
        # Define motor features for actions and observations (e.g., arm, gripper, base).
        features = {
            "action.arm_l": {"dtype": "float32", "shape": (6,), "names": list(range(6))},  # Left arm action.
            "action.gripper_l": {"dtype": "float32", "shape": (1,), "names": list(range(1))},  # Left gripper action.
            "action.arm_r": {"dtype": "float32", "shape": (6,), "names": list(range(6))},  # Right arm action.
            "action.gripper_r": {"dtype": "float32", "shape": (1,), "names": list(range(1))},  # Right gripper action.
            "action.base": {"dtype": "float32", "shape": (2,), "names": list(range(2))},  # Base action.
            "action.eef_l": {"dtype": "float32", "shape": (7,), "names": list(range(7))},  # Left end-effector action.
            "action.eef_r": {"dtype": "float32", "shape": (7,), "names": list(range(7))},  # Right end-effector action.
            "action.head": {"dtype": "float32", "shape": (2,), "names": list(range(2))},  # Head action.
            "observation.state.arm_l": {"dtype": "float32", "shape": (6,), "names": list(range(6))},  # Left arm state.
            "observation.state.gripper_l": {"dtype": "float32", "shape": (1,), "names": list(range(1))},  # Left gripper state.
            "observation.state.arm_r": {"dtype": "float32", "shape": (6,), "names": list(range(6))},  # Right arm state.
            "observation.state.gripper_r": {"dtype": "float32", "shape": (1,), "names": list(range(1))},  # Right gripper state.
            "observation.state.base": {"dtype": "float32", "shape": (2,), "names": list(range(2))},  # Base state.
            "observation.state.eef_l": {"dtype": "float32", "shape": (7,), "names": list(range(7))},  # Left end-effector state.
            "observation.state.eef_r": {"dtype": "float32", "shape": (7,), "names": list(range(7))},  # Right end-effector state.
            "observation.state.odom": {"dtype": "float32", "shape": (7,), "names": list(range(7))},  # Odometry state.
            "observation.state.head": {"dtype": "float32", "shape": (2,), "names": list(range(2))},  # Head state.
        }
        # If in joint space, concatenate action and state features into single vectors.
        if self.astra_controller.space == "joint":
            return {
                "action": {"dtype": "float32", "shape": (6+1+6+1+2+2,), "names": list(range(6+1+6+1+2+2))},
                "observation.state": {"dtype": "float32", "shape": (6+1+6+1+2+2,), "names": list(range(6+1+6+1+2+2))},
                **features,
            }
        elif self.astra_controller.space == "cart":
            raise NotImplementedError("Cartesian space is not supported for now")
        else:
            return features

    @property
    def features(self):
        # Combine motor and camera features into a single dictionary.
        return {**self.motor_features, **self.camera_features}

    def connect(self):
        # Establish connection to the robot’s controller.
        if self.is_connected:
            raise RobotDeviceAlreadyConnectedError("AstraRobot is already connected.")
        if not self.astra_controller:
            raise ValueError("AstraRobot doesn't have any device to connect.")
        self.astra_controller.connect()
        self.is_connected = True

    def wait_for_reset(self):
        # Wait for the robot to reset, delegating to the controller.
        self.astra_controller.wait_for_reset()

    def teleop_step(self, record_data=False) -> None | tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
        # Perform a teleoperation step, optionally recording data.
        if not self.is_connected:
            raise RobotDeviceNotConnectedError("AstraRobot is not connected.")
        assert record_data, "Please use Astra Web Teleop"  # Enforces data recording for this method.
        # Read leader positions for teleoperation.
        action, action_arm_l, action_gripper_l, action_arm_r, action_gripper_r, action_base, action_eef_l, action_eef_r, action_head = self.astra_controller.read_leader_present_position()
        obs_dict = self.capture_observation()  # Capture current observation.
        action_dict = {}
        # Populate action dictionary based on control space.
        if self.astra_controller.space in ['joint', 'cartesian']:
            action_dict["action"] = torch.from_numpy(np.array(action)).to(torch.float32)
        action_dict["action.arm_l"] = torch.from_numpy(np.array(action_arm_l)).to(torch.float32)
        action_dict["action.gripper_l"] = torch.from_numpy(np.array(action_gripper_l)).to(torch.float32)
        action_dict["action.arm_r"] = torch.from_numpy(np.array(action_arm_r)).to(torch.float32)
        action_dict["action.gripper_r"] = torch.from_numpy(np.array(action_gripper_r)).to(torch.float32)
        action_dict["action.base"] = torch.from_numpy(np.array(action_base)).to(torch.float32)
        action_dict["action.eef_l"] = torch.from_numpy(np.array(action_eef_l)).to(torch.float32)
        action_dict["action.eef_r"] = torch.from_numpy(np.array(action_eef_r)).to(torch.float32)
        action_dict["action.head"] = torch.from_numpy(np.array(action_head)).to(torch.float32)
        return obs_dict, action_dict  # Return observation and action dictionaries.

    def capture_observation(self):
        # Capture current state and images from the robot.
        if not self.is_connected:
            raise RobotDeviceNotConnectedError("AstraRobot is not connected.")
        # Read current positions from the controller.
        state, state_arm_l, state_gripper_l, state_arm_r, state_gripper_r, state_base, state_eef_l, state_eef_r, state_odom, state_head = self.astra_controller.read_present_position()
        images = self.astra_controller.read_cameras()  # Capture camera images.
        obs_dict = {}
        # Populate observation dictionary based on control space.
        if self.astra_controller.space in ['joint', 'cartesian']:
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
        # Add images to the observation dictionary.
        for name in images:
            obs_dict[f"observation.images.{name}"] = torch.from_numpy(images[name])
        obs_dict["done"] = self.astra_controller.done  # Include done flag from controller.
        self.astra_controller.done = False  # Reset done flag.
        return obs_dict

    def send_action(self, action: torch.Tensor):
        # Send an action to the robot’s controller.
        if not self.is_connected:
            raise RobotDeviceNotConnectedError("AstraRobot is not connected.")
        self.astra_controller.write_goal_position(action.tolist())  # Send action to controller.
        # Return a dictionary with the action (detailed breakdown is placeholder zeros).
        action_dict = {
            "action": action,
            "action.arm_l": torch.zeros(6).to(torch.float32),
            "action.gripper_l": torch.zeros(1).to(torch.float32),
            "action.arm_r": torch.zeros(6).to(torch.float32),
            "action.gripper_r": torch.zeros(1).to(torch.float32),
            "action.base": torch.zeros(2).to(torch.float32),
            "action.eef_l": torch.zeros(7).to(torch.float32),
            "action.eef_r": torch.zeros(7).to(torch.float32),
            "action.head": torch.zeros(2).to(torch.float32),
        }
        return action_dict

    def log_control_info(self, log_dt):
        pass  # Placeholder for logging (not implemented).

    def disconnect(self):
        # Disconnect from the robot’s controller.
        if not self.is_connected:
            raise RobotDeviceNotConnectedError("AstraRobot is not connected.")
        self.astra_controller.disconnect()
        self.is_connected = False

    def __del__(self):
        # Ensure disconnection when the object is deleted.
        if getattr(self, "is_connected", False):
            self.disconnect()