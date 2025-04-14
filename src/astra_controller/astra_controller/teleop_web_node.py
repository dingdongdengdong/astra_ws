import rclpy  # ROS 2 Python client library for node creation and communication
import rclpy.node  # Base class for creating ROS nodes
import rclpy.qos  # Quality of Service settings for reliable communication

import std_msgs.msg  # Standard ROS messages (e.g., Bool, String)
import geometry_msgs.msg  # ROS messages for geometry (e.g., PoseStamped)
import sensor_msgs.msg  # ROS messages for sensor data (e.g., Image)
import astra_controller_interfaces.msg  # Custom ROS messages for joint commands

from astra_teleop_web.teleoprator import Teleopoperator  # Custom class for web-based teleoperation
from tf2_ros.transform_listener import TransformListener  # Listener for TF transforms
from tf2_ros.buffer import Buffer  # Buffer to store TF transforms

import numpy as np  # Numerical operations library
from pytransform3d import transformations as pt  # 3D transformation library
import modern_robotics as mr  # Robot kinematics library
from mr_urdf_loader import loadURDF  # Utility to load URDF robot models
from pathlib import Path  # File path handling
from ament_index_python import get_package_share_directory  # Locate ROS package directories
from astra_controller.astra_controller import pq_from_ros_transform  # Convert ROS transform to position-quaternion

np.set_printoptions(precision=4, suppress=True)  # Configure NumPy printing: 4 decimals, suppress small values

# Define a reliable QoS profile for sensor data (e.g., camera images)
qos_profile_sensor_data_reliable = rclpy.qos.QoSProfile(**rclpy.impl.implementation_singleton.rclpy_implementation.rmw_qos_profile_t.predefined('qos_profile_sensor_data').to_dict())
qos_profile_sensor_data_reliable.reliability = 1  # Set to reliable communication

def main(args=None):
    # Main function to initialize and run the ROS node
    rclpy.init(args=args)  # Initialize ROS 2 runtime

    node = rclpy.node.Node("teleop_web_node")  # Create a ROS node named "teleop_web_node"

    logger = node.get_logger()  # Get logger for debugging/info messages
    
    teleopoperator = Teleopoperator()  # Create teleoperation object for web interface
    
    tf_buffer = Buffer()  # Buffer to store TF transforms
    tf_listener = TransformListener(tf_buffer, node)  # Listen for TF transforms
    
    def get_current_eef_pose_cb(side):
        # Callback to get the current end-effector pose for the specified side (left/right)
        Tsgoal_msg = tf_buffer.lookup_transform('base_link', 'link_ree_teleop' if side == "right" else 'link_lee_teleop', rclpy.time.Time())  # Get transform from base_link to end-effector
        Tsgoal = pt.transform_from_pq(np.array(pq_from_ros_transform(Tsgoal_msg.transform)))  # Convert to 4x4 transformation matrix
        return Tsgoal  # Return the transformation
    teleopoperator.on_get_current_eef_pose = get_current_eef_pose_cb  # Assign callback to teleopoperator

    M = {}  # Home configurations for left and right sides
    Slist = {}  # Screw axes for left and right sides
    
    for side in ["left", "right"]:
        # Load URDF model for the robot
        urdf_name = str(Path(get_package_share_directory("astra_description")) / "urdf" / "astra_description_rel.urdf")
        M[side], Slist[side], _, _, _, _ = loadURDF(
            urdf_name, 
            eef_link_name='link_ree_teleop' if side == "right" else 'link_lee_teleop',  # End-effector link
            actuated_joint_names=["joint_r1", "joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"] if side == "right" else ["joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6"]  # Joints
        )

    def get_initial_eef_pose_cb(side, initial_joint_states):
        # Callback to compute initial end-effector pose using forward kinematics
        return mr.FKinSpace(M[side], Slist[side], initial_joint_states)  # Return transformation matrix
    teleopoperator.on_get_initial_eef_pose = get_initial_eef_pose_cb  # Assign callback
    
    def pub_T(pub, T, frame_id='base_link'):
        # Helper function to publish a transformation as a PoseStamped message
        msg = geometry_msgs.msg.PoseStamped()
        msg.header.frame_id = frame_id  # Set frame ID
        msg.header.stamp = node.get_clock().now().to_msg()  # Set timestamp
        pq = pt.pq_from_transform(T)  # Convert to position-quaternion
        msg.pose.position.x = pq[0]  # Position x
        msg.pose.position.y = pq[1]  # Position y
        msg.pose.position.z = pq[2]  # Position z
        msg.pose.orientation.w = pq[3]  # Quaternion w
        msg.pose.orientation.x = pq[4]  # Quaternion x
        msg.pose.orientation.y = pq[5]  # Quaternion y
        msg.pose.orientation.z = pq[6]  # Quaternion z
        pub.publish(msg)  # Publish the message
    
    # Dictionaries for publishers for each side (left/right)
    goal_pose_publisher = {}
    goal_pose_inactive_publisher = {}
    cam_pose_publisher = {}
    arm_gripper_joint_command_publisher = {}
    arm_joint_command_publisher = {}
    lift_joint_command_publisher = {}
    
    for side in ["left", "right"]:
        # Create publishers for goal poses, camera poses, and joint commands
        goal_pose_publisher[side] = node.create_publisher(geometry_msgs.msg.PoseStamped, f"{side}/goal_pose", 10)
        goal_pose_inactive_publisher[side] = node.create_publisher(geometry_msgs.msg.PoseStamped, f"{side}/goal_pose_inactive", 10)
        cam_pose_publisher[side] = node.create_publisher(geometry_msgs.msg.PoseStamped, f"{side}/cam_pose", 10)
        arm_gripper_joint_command_publisher[side] = node.create_publisher(astra_controller_interfaces.msg.JointCommand, f"{side}/arm/gripper_joint_command", 10)
        arm_joint_command_publisher[side] = node.create_publisher(astra_controller_interfaces.msg.JointCommand, f"{side}/arm/joint_command", 10)
        lift_joint_command_publisher[side] = node.create_publisher(astra_controller_interfaces.msg.JointCommand, f"{side}/lift/joint_command", 10)

    def pub_goal_cb(side, Tsgoal, Tscam=None, Tsgoal_inactive=None):
        # Callback to publish goal and camera poses
        if Tsgoal is not None:
            pub_T(goal_pose_publisher[side], Tsgoal)  # Publish goal pose
        if Tsgoal_inactive is not None:
            pub_T(goal_pose_inactive_publisher[side], Tsgoal_inactive)  # Publish inactive goal pose
        if Tscam is not None:
            pub_T(cam_pose_publisher[side], Tscam)  # Publish camera pose
    teleopoperator.on_pub_goal = pub_goal_cb  # Assign callback
    
    def pub_gripper_cb(side, gripper_open):
        # Callback to publish gripper joint commands
        arm_gripper_joint_command_publisher[side].publish(astra_controller_interfaces.msg.JointCommand(
            name=["joint_r7r" if side == "right" else "joint_l7r"],  # Gripper joint name
            position_cmd=[gripper_open]  # Gripper position
        ))
    teleopoperator.on_pub_gripper = pub_gripper_cb  # Assign callback

    head_joint_command_publisher = node.create_publisher(astra_controller_interfaces.msg.JointCommand, "head/joint_command", 10)

    def pub_head_cb(head_pan, head_tilt):
        # Callback to publish head joint commands
        head_joint_command_publisher.publish(astra_controller_interfaces.msg.JointCommand(
            name=["joint_head_pan", "joint_head_tilt"],  # Head joint names
            position_cmd=[head_pan, head_tilt]  # Head joint positions
        ))
    teleopoperator.on_pub_head = pub_head_cb  # Assign callback

    cmd_vel_publisher = node.create_publisher(geometry_msgs.msg.Twist, 'cmd_vel', 10)
    def cmd_vel_cb(linear_vel, angular_vel):
        # Callback to publish velocity commands
        msg = geometry_msgs.msg.Twist()
        msg.linear.x = linear_vel  # Linear velocity
        msg.angular.z = angular_vel  # Angular velocity
        cmd_vel_publisher.publish(msg)  # Publish velocity command
    teleopoperator.on_cmd_vel = cmd_vel_cb  # Assign callback
    
    reset_publisher = node.create_publisher(std_msgs.msg.Bool, 'reset', 10)
    done_publisher = node.create_publisher(std_msgs.msg.Bool, 'done', 10)

    def reset_cb():
        # Callback to publish reset signal
        reset_publisher.publish(std_msgs.msg.Bool(data=True))  # Publish True to reset
    teleopoperator.on_reset = reset_cb  # Assign callback

    def done_cb():
        # Callback to publish done signal
        done_publisher.publish(std_msgs.msg.Bool(data=True))  # Publish True to indicate done
    teleopoperator.on_done = done_cb  # Assign callback

    def get_cb(name):
        # Factory function to create callbacks for camera image subscriptions
        def cb(msg: sensor_msgs.msg.Image):
            assert msg.encoding == "rgb8"  # Check image encoding
            assert msg.height == 360 and msg.width == 640  # Check image dimensions
            image = np.asarray(msg.data).reshape(msg.height, msg.width, 3)  # Reshape to [H, W, C]
            teleopoperator.webserver.track_feed(name, (image, msg.header.stamp.sec, msg.header.stamp.nanosec))  # Send to webserver
        return cb
    # Subscribe to camera feeds with reliable QoS
    node.create_subscription(sensor_msgs.msg.Image, 'cam_head/image_raw', get_cb("head"), qos_profile_sensor_data_reliable)
    node.create_subscription(sensor_msgs.msg.Image, 'left/cam_wrist/image_raw', get_cb("wrist_left"), qos_profile_sensor_data_reliable)
    node.create_subscription(sensor_msgs.msg.Image, 'right/cam_wrist/image_raw', get_cb("wrist_right"), qos_profile_sensor_data_reliable)

    # Subscribe to error messages for IK and hardware
    def cb(msg):
        teleopoperator.error_cb(f"[IK Left]\n{msg.data}")  # Report left IK errors
    node.create_subscription(std_msgs.msg.String, 'left/ik_error', cb, rclpy.qos.qos_profile_sensor_data)
    
    def cb(msg):
        teleopoperator.error_cb(f"[IK Right]\n{msg.data}")  # Report right IK errors
    node.create_subscription(std_msgs.msg.String, 'right/ik_error', cb, rclpy.qos.qos_profile_sensor_data)
    
    def cb(msg):
        teleopoperator.error_cb(f"[Arm Left]\n{msg.data}")  # Report left arm errors
    node.create_subscription(std_msgs.msg.String, 'left/arm/error', cb, rclpy.qos.qos_profile_sensor_data)
    
    def cb(msg):
        teleopoperator.error_cb(f"[Arm Right]\n{msg.data}")  # Report right arm errors
    node.create_subscription(std_msgs.msg.String, 'right/arm/error', cb, rclpy.qos.qos_profile_sensor_data)
    
    def cb(msg):
        teleopoperator.error_cb(f"[Lift Left]\n{msg.data}")  # Report left lift errors
    node.create_subscription(std_msgs.msg.String, 'left/lift/error', cb, rclpy.qos.qos_profile_sensor_data)
    
    def cb(msg):
        teleopoperator.error_cb(f"[Lift Right]\n{msg.data}")  # Report right lift errors
    node.create_subscription(std_msgs.msg.String, 'right/lift/error', cb, rclpy.qos.qos_profile_sensor_data)

    try:
        rclpy.spin(node)  # Start the ROS event loop
    except KeyboardInterrupt as err:
        teleopoperator.webserver.loop.stop()  # Stop webserver on interrupt
        raise err  # Re-raise to exit cleanly

    node.destroy_node()  # Clean up the node (optional)
    rclpy.shutdown()  # Shut down ROS 2 runtime

if __name__ == '__main__':
    main()  # Run the main function