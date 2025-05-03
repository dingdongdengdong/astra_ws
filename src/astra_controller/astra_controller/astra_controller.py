import rclpy
import rclpy.node
import rclpy.qos
import rclpy.action
import sensor_msgs.msg
import std_msgs.msg
import astra_controller_interfaces.msg
#import astra_controller_interfaces.srv
import threading
import numpy as np
import time
import geometry_msgs.msg
import nav_msgs.msg
from tf2_ros.transform_listener import TransformListener
from tf2_ros.buffer import Buffer
import tf2_py as tf2

# Custom QoS profile for reliable sensor data
qos_profile_sensor_data_reliable = rclpy.qos.QoSProfile(**rclpy.impl.implementation_singleton.rclpy_implementation.rmw_qos_profile_t.predefined('qos_profile_sensor_data').to_dict())
qos_profile_sensor_data_reliable.reliability = 1  # Set reliability to RMW_QOS_POLICY_RELIABILITY_RELIABLE

def without_keys(d, keys):
    # Utility to exclude specified keys from a dictionary
    return {k: v for k, v in d.items() if k not in keys}

def pq_from_ros_pose(msg: geometry_msgs.msg.Pose):
    # Convert ROS Pose to position-quaternion list [x, y, z, w, qx, qy, qz]
    return [msg.position.x, msg.position.y, msg.position.z, msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z]

def pq_from_ros_transform(msg: geometry_msgs.msg.Transform):
    # Convert ROS Transform to position-quaternion list [x, y, z, w, qx, qy, qz]
    return [msg.translation.x, msg.translation.y, msg.translation.z, msg.rotation.w, msg.rotation.x, msg.rotation.y, msg.rotation.z]

class AstraController:
    def __init__(self, space=None):
        # Initialize the controller with an optional control space ('joint' or 'cartesian')
        rclpy.init()  # Initialize ROS
        self.space = space  # Define control mode
        self.node = rclpy.node.Node('arm_node')  # Create ROS node
        self.logger = self.node.get_logger()  # Get logger
        self.is_quit = threading.Event()  # Event to signal shutdown
        self.reset_buf()  # Initialize buffers

        def cb(msg):
            # Callback for reset flag
            assert msg.data  # Expect True
            self.reset = msg.data  # Set reset flag
        self.node.create_subscription(std_msgs.msg.Bool, 'reset', cb, rclpy.qos.qos_profile_sensor_data)

        def cb(msg):
            # Callback for done flag
            assert msg.data  # Expect True
            self.done = msg.data  # Set done flag
        self.node.create_subscription(std_msgs.msg.Bool, 'done', cb, rclpy.qos.qos_profile_sensor_data)

        def get_cb(name):
            # Factory function for image callbacks
            def cb(msg: sensor_msgs.msg.Image):
                assert msg.encoding == "rgb8"  # Expect RGB8 encoding
                assert msg.height == 360 and msg.width == 640  # Expect 360x640 resolution
                image = np.asarray(msg.data).reshape(360, 640, 3)  # Reshape to [H, W, C]
                self.images[name] = image  # Store image
            return cb
        # Subscribe to camera topics
        self.node.create_subscription(sensor_msgs.msg.Image, "cam_head/image_raw", get_cb("head"), qos_profile_sensor_data_reliable)
        self.node.create_subscription(sensor_msgs.msg.Image, "left/cam_wrist/image_raw", get_cb("wrist_left"), qos_profile_sensor_data_reliable)
        self.node.create_subscription(sensor_msgs.msg.Image, "right/cam_wrist/image_raw", get_cb("wrist_right"), qos_profile_sensor_data_reliable)

        tf_buffer = Buffer()  # Buffer for TF transforms
        TransformListener(tf_buffer, self.node)  # Listen for transforms

        def cb(msg: sensor_msgs.msg.JointState):
            # Callback for joint states
            self.joint_states.update(without_keys(dict(zip(msg.name, msg.position)), ["joint_r7l", "joint_l7l"]))  # Update joint states, exclude mirrored gripper joints
            try:
                if "joint_l6" in msg.name:
                    T_msg = tf_buffer.lookup_transform('base_link', 'link_lee_teleop', rclpy.time.Time())  # Get left end-effector transform
                    self.joint_states["eef_l"] = pq_from_ros_transform(T_msg.transform)
                if "joint_r6" in msg.name:
                    T_msg = tf_buffer.lookup_transform('base_link', 'link_ree_teleop', rclpy.time.Time())  # Get right end-effector transform
                    self.joint_states["eef_r"] = pq_from_ros_transform(T_msg.transform)
            except (tf2.LookupException, tf2.ConnectivityException, tf2.ExtrapolationException):
                pass  # Ignore TF errors
        self.node.create_subscription(sensor_msgs.msg.JointState, "joint_states", cb, rclpy.qos.qos_profile_sensor_data)

        def cb(msg: nav_msgs.msg.Odometry):
            # Callback for odometry
            self.joint_states["twist_linear"] = msg.twist.twist.linear.x  # Linear velocity
            self.joint_states["twist_angular"] = msg.twist.twist.angular.z  # Angular velocity
            self.joint_states["odom"] = pq_from_ros_pose(msg.pose.pose)  # Robot pose
        self.node.create_subscription(nav_msgs.msg.Odometry, "odom", cb, rclpy.qos.qos_profile_sensor_data)

        def cb(msg: astra_controller_interfaces.msg.JointCommand):
            # Callback for joint commands
            self.joint_commands.update(without_keys(dict(zip(msg.name, msg.position_cmd)), ["joint_r7l", "joint_l7l"]))  # Update commands
        # Subscribe to command topics
        for topic in ["left/lift/joint_command", "left/arm/joint_command", "left/arm/gripper_joint_command",
                      "right/lift/joint_command", "right/arm/joint_command", "right/arm/gripper_joint_command",
                      "head/joint_command"]:
            self.node.create_subscription(astra_controller_interfaces.msg.JointCommand, topic, cb, rclpy.qos.qos_profile_sensor_data)

        def get_cb(name):
            # Factory function for goal pose callbacks
            def cb(msg: geometry_msgs.msg.PoseStamped):
                self.joint_commands[name] = pq_from_ros_pose(msg.pose)  # Store end-effector goal pose
            return cb
        self.node.create_subscription(geometry_msgs.msg.PoseStamped, "left/goal_pose", get_cb("eef_l"), rclpy.qos.qos_profile_sensor_data)
        self.node.create_subscription(geometry_msgs.msg.PoseStamped, "right/goal_pose", get_cb("eef_r"), rclpy.qos.qos_profile_sensor_data)

        def cb(msg: geometry_msgs.msg.Twist):
            # Callback for velocity commands
            self.joint_commands["twist_linear"] = msg.linear.x  # Linear velocity command
            self.joint_commands["twist_angular"] = msg.angular.z  # Angular velocity command
        self.node.create_subscription(geometry_msgs.msg.Twist, "cmd_vel", cb, rclpy.qos.qos_profile_sensor_data)

        # Create publishers for commands
        self.left_arm_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "left/arm/joint_command", 10)
        self.left_lift_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "left/lift/joint_command", 10)
        self.left_arm_gripper_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "left/arm/gripper_joint_command", 10)
        self.right_arm_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "right/arm/joint_command", 10)
        self.right_lift_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "right/lift/joint_command", 10)
        self.right_arm_gripper_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "right/arm/gripper_joint_command", 10)
        self.head_joint_command_publisher = self.node.create_publisher(astra_controller_interfaces.msg.JointCommand, "head/joint_command", 10)
        self.left_goal_pose_publisher = self.node.create_publisher(geometry_msgs.msg.PoseStamped, "left/goal_pose", 10)
        self.right_goal_pose_publisher = self.node.create_publisher(geometry_msgs.msg.PoseStamped, "right/goal_pose", 10)
        self.cmd_vel_publisher = self.node.create_publisher(geometry_msgs.msg.Twist, 'cmd_vel', 10)

        # Start ROS spinning in a background thread
        self.t = threading.Thread(target=rclpy.spin, args=(self.node,), daemon=True).start()

    def reset_buf(self):
        # Reset all state and command buffers
        self.reset = False  # Reset flag
        self.done = False  # Done flag
        self.images = {"head": None, "wrist_left": None, "wrist_right": None}  # Camera images
        self.joint_states = {
            "joint_l1": None, "joint_l2": None, "joint_l3": None, "joint_l4": None, "joint_l5": None, "joint_l6": None, "joint_l7r": None,
            "joint_r1": None, "joint_r2": None, "joint_r3": None, "joint_r4": None, "joint_r5": None, "joint_r6": None, "joint_r7r": None,
            "joint_head_pan": None, "joint_head_tilt": None,
            "twist_linear": None, "twist_angular": None,
            "eef_l": None, "eef_r": None, "odom": None
        }  # Current joint states and robot pose
        self.joint_commands = {
            "joint_l1": None, "joint_l2": None, "joint_l3": None, "joint_l4": None, "joint_l5": None, "joint_l6": None, "joint_l7r": None,
            "joint_r1": None, "joint_r2": None, "joint_r3": None, "joint_r4": None, "joint_r5": None, "joint_r6": None, "joint_r7r": None,
            "joint_head_pan": None, "joint_head_tilt": None,
            "twist_linear": None, "twist_angular": None,
            "eef_l": None, "eef_r": None
        }  # Commanded joint positions

    def states_ready(self):
        # Check if all state data is available
        for k, v in self.images.items():
            if v is None:
                print(f"Waiting for image {k} to be ready")
                return False
        for k, v in self.joint_states.items():
            if v is None:
                print(f"Waiting for state {k} to be ready")
                return False
        return True

    def commands_ready(self):
        # Check if all command data is available
        for k, v in self.joint_commands.items():
            if v is None:
                print(f"Waiting for command {k} to be ready")
                return False
        return True

    def wait_for_reset(self):
        # Wait for reset signal and ensure states are ready
        print("Waiting for reset")
        while not self.reset:
            time.sleep(0.1)
        self.reset_buf()  # Reset buffers
        while not self.states_ready():
            time.sleep(0.1)

    def connect(self):
        # Placeholder for connection logic
        print("connected")

    def disconnect(self):
        # Placeholder for disconnection logic
        print("disconnect")

    def read_leader_present_position(self):
        # Read current commanded positions based on control space
        while not self.commands_ready():
            time.sleep(0.1)
        if self.space == "joint":
            action = [self.joint_commands[key] for key in [
                "joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6",
                "joint_l7r", "joint_r1", "joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6",
                "joint_r7r", "twist_linear", "twist_angular", "joint_head_pan", "joint_head_tilt"
            ]]  # Full joint command list
        elif self.space == "cartesian":
            action = self.joint_commands["eef_l"] + self.joint_commands["eef_r"] + [self.joint_commands[key] for key in [
                "joint_l7r", "joint_r7r", "twist_linear", "twist_angular", "joint_head_pan", "joint_head_tilt"
            ]]  # Cartesian command list
        else:
            action = None
        return (action, 
                [self.joint_commands[key] for key in ["joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6"]],  # Left arm
                [self.joint_commands["joint_l7r"]],  # Left gripper
                [self.joint_commands[key] for key in ["joint_r1", "joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"]],  # Right arm
                [self.joint_commands["joint_r7r"]],  # Right gripper
                [self.joint_commands["twist_linear"], self.joint_commands["twist_angular"]],  # Base velocity
                self.joint_commands["eef_l"], self.joint_commands["eef_r"],  # End-effector poses
                [self.joint_commands["joint_head_pan"], self.joint_commands["joint_head_tilt"]])  # Head joints

    def read_present_position(self):
        # Read current state positions based on control space
        if self.space == "joint":
            observation = [self.joint_states[key] for key in [
                "joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6",
                "joint_l7r", "joint_r1", "joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6",
                "joint_r7r", "twist_linear", "twist_angular", "joint_head_pan", "joint_head_tilt"
            ]]  # Full joint state list
        elif self.space == "cartesian":
            observation = self.joint_states["eef_l"] + self.joint_states["eef_r"] + [self.joint_states[key] for key in [
                "joint_l7r", "joint_r7r", "twist_linear", "twist_angular", "joint_head_pan", "joint_head_tilt"
            ]]  # Cartesian state list
        else:
            observation = None
        return (observation,
                [self.joint_states[key] for key in ["joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6"]],  # Left arm
                [self.joint_states["joint_l7r"]],  # Left gripper
                [self.joint_states[key] for key in ["joint_r1", "joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"]],  # Right arm
                [self.joint_states["joint_r7r"]],  # Right gripper
                [self.joint_states["twist_linear"], self.joint_states["twist_angular"]],  # Base velocity
                self.joint_states["eef_l"], self.joint_states["eef_r"],  # End-effector poses
                self.joint_states["odom"],  # Robot pose
                [self.joint_states["joint_head_pan"], self.joint_states["joint_head_tilt"]])  # Head joints

    def write_goal_position(self, goal_pos: list[float]):
        # Send goal positions to the robot based on control space
        if self.space == "joint":
            joint_commands = dict(zip([
                "joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6",
                "joint_l7r", "joint_r1", "joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6",
                "joint_r7r", "twist_linear", "twist_angular", "joint_head_pan", "joint_head_tilt"
            ], goal_pos))  # Map goal positions to joint names

            # Publish commands to respective topics
            self.left_arm_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6"],
                position_cmd=[joint_commands[key] for key in ["joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6"]]
            ))
            self.left_lift_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_l1"],
                position_cmd=[joint_commands["joint_l1"]]
            ))
            self.left_arm_gripper_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_l7r"],
                position_cmd=[joint_commands["joint_l7r"]]
            ))
            self.right_arm_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"],
                position_cmd=[joint_commands[key] for key in ["joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"]]
            ))
            self.right_lift_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_r1"],
                position_cmd=[joint_commands["joint_r1"]]
            ))
            self.right_arm_gripper_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_r7r"],
                position_cmd=[joint_commands["joint_r7r"]]
            ))
            self.head_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
                name=["joint_head_pan", "joint_head_tilt"],
                position_cmd=[joint_commands["joint_head_pan"], joint_commands["joint_head_tilt"]]
            ))
            msg = geometry_msgs.msg.Twist()
            msg.linear.x = joint_commands["twist_linear"]  # Linear velocity command
            msg.angular.z = joint_commands["twist_angular"]  # Angular velocity command
            # self.cmd_vel_publisher.publish(msg)  # Uncomment to enable base movement
        elif self.space == "cartesian":
            raise NotImplementedError("Cartesian space is not supported for now")
        else:
            raise Exception("Give a space to the AstraController!")

    def read_cameras(self):
        # Return current camera images
        return self.images

    def quit(self):
        # Shutdown the controller
        if not self.is_quit.is_set():
            self.is_quit.set()
            self.node.destroy_node()  # Destroy ROS node
            rclpy.shutdown()  # Shutdown ROS

    def __del__(self):
        # Empty destructor (cleanup handled in quit)
        pass