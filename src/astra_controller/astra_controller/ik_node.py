import math  # Library for mathematical functions like pi and fmod
from pathlib import Path  # Library for handling file paths in a platform-independent way
import rclpy  # ROS 2 Python client library for node creation and communication
import rclpy.node  # Base class for creating ROS nodes
import rclpy.qos  # Quality of Service settings for reliable communication

import geometry_msgs.msg  # ROS messages for geometry data, e.g., PoseStamped
import astra_controller_interfaces.msg  # Custom ROS messages for joint commands
import std_msgs.msg  # Standard ROS messages, e.g., String for errors

from ament_index_python import get_package_share_directory  # Function to locate package share directories

from typing import Any, List, Tuple, Union  # Type hints for better code readability

import modern_robotics as mr  # Library for robot kinematics calculations
import numpy as np  # Library for numerical operations, especially with arrays
from mr_urdf_loader import loadURDF  # Utility to load URDF files for robot models
from pytransform3d import transformations as pt  # Library for 3D transformation operations

import logging  # Library for logging debug/info/error messages

logger = logging.getLogger(__name__)  # Create a logger specific to this module

np.set_printoptions(precision=4, suppress=True)  # Configure NumPy to print with 4 decimal places and suppress small values

def pq_from_ros_pose(msg: geometry_msgs.msg.Pose):
    # Convert a ROS Pose message to a position-quaternion list [x, y, z, w, qx, qy, qz]
    return [
        msg.position.x,  # X position
        msg.position.y,  # Y position
        msg.position.z,  # Z position
        msg.orientation.w,  # Quaternion w component
        msg.orientation.x,  # Quaternion x component
        msg.orientation.y,  # Quaternion y component
        msg.orientation.z  # Quaternion z component
    ]

def main(args=None):
    # Main function to set up and run the ROS node
    rclpy.init(args=args)  # Initialize the ROS 2 runtime

    node = rclpy.node.Node("ik_node")  # Create a ROS node named "ik_node"
    
    node.declare_parameter('eef_link_name', 'link_ree_teleop')  # Declare parameter for end-effector link name
    node.declare_parameter('joint_names', ['joint_r1', 'joint_r2', 'joint_r3', 'joint_r4', 'joint_r5', 'joint_r6'])  # Declare parameter for joint names

    eef_link_name = node.get_parameter('eef_link_name').value  # Get the end-effector link name
    joint_names = node.get_parameter('joint_names').value  # Get the list of joint names
    
    assert len(joint_names) == 6  # Ensure there are exactly 6 joints (1 lift + 5 arm)

    # Construct the path to the URDF file for the robot model
    urdf_name = str(Path(get_package_share_directory("astra_description")) / "urdf" / "astra_description_rel.urdf")
    M, Slist, Blist, Mlist, Glist, robot = loadURDF(  # Load the URDF model
        urdf_name,  # Path to the URDF file
        eef_link_name=eef_link_name,  # Name of the end-effector link
        actuated_joint_names=joint_names  # Names of the actuated joints
    )
    
    # Extract joint limits from the URDF model
    joint_limit_lower = [robot.joint_map[joint_name].limit.lower for joint_name in joint_names]  # Lower limits for each joint
    joint_limit_upper = [robot.joint_map[joint_name].limit.upper for joint_name in joint_names]  # Upper limits for each joint

    # Create publishers for sending joint commands
    arm_joint_command_publisher = node.create_publisher(astra_controller_interfaces.msg.JointCommand, "arm/joint_command", 10)  # Publisher for arm joints
    lift_joint_command_publisher = node.create_publisher(astra_controller_interfaces.msg.JointCommand, "lift/joint_command", 10)  # Publisher for lift joint
    
    error_publisher = node.create_publisher(std_msgs.msg.String, "ik_error", 10)  # Publisher for IK error messages
        
    def pub_theta(theta_list):
        # Publish joint commands for arm and lift separately
        msg = astra_controller_interfaces.msg.JointCommand(  # Create message for arm joints
            name=joint_names[1:],  # Arm joints (excluding lift, joint_r1)
            position_cmd=list(theta_list[1:])  # Position commands for arm joints
        )
        arm_joint_command_publisher.publish(msg)  # Publish arm joint commands

        msg = astra_controller_interfaces.msg.JointCommand(  # Create message for lift joint
            name=joint_names[:1],  # Lift joint (joint_r1)
            position_cmd=list(theta_list[:1])  # Position command for lift joint
        )
        lift_joint_command_publisher.publish(msg)  # Publish lift joint command
        
    last_theta_list = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # Initial guess for joint angles (all zero)

    def set_ee_pose_matrix(T_sd: np.ndarray) -> Tuple[Union[np.ndarray, Any, List[float]], bool]:
        # Compute joint angles to achieve a desired end-effector pose using inverse kinematics
        logger.debug(f'Setting ee_pose to matrix=\n{T_sd}')  # Log the desired transformation matrix
        
        nonlocal last_theta_list  # Use the last successful joint angles as an initial guess
        
        for initial_guess in [last_theta_list, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]:  # Try two initial guesses
            theta_list, success = mr.IKinSpace(  # Perform inverse kinematics
                Slist=Slist,  # Screw axes in the space frame
                M=M,  # Home configuration of the end-effector
                T=T_sd,  # Desired transformation matrix
                thetalist0=initial_guess,  # Initial guess for joint angles
                eomg=0.001,  # Orientation error tolerance
                ev=0.001  # Position error tolerance
            )
            
            if not success:  # If IK failed with this guess
                logger.warn('Failed guess. Maybe EEF is out of range.')  # Log a warning
                continue  # Try the next initial guess
            
            # Normalize joint angles to [-pi, pi] for arm joints (skip lift joint)
            for i in [1, 2, 3, 4, 5]:  # Indices for arm joints (joint_r2 to joint_r6)
                theta_list[i] = math.fmod(math.fmod(theta_list[i] + math.pi, 2*math.pi) + 2*math.pi, 2*math.pi) - math.pi

            # Check if the solution respects joint limits
            ok = True  # Flag to track if all joints are within limits
            for i, (p, mn, mx) in enumerate(zip(theta_list, joint_limit_lower, joint_limit_upper)):  # Iterate over joints
                if not (mn <= p <= mx):  # If a joint exceeds its limits
                    logger.error(f"Joint #{i+1} reach limit, min: {mn}, max: {mx}, current pos: {p}")  # Log the violation
                    ok = False  # Mark solution as invalid
            if not ok:  # If any joint limit was violated
                continue  # Try the next initial guess
            
            pub_theta(theta_list)  # Publish the valid joint angles

            last_theta_list = theta_list  # Update the last successful solution
            return theta_list, True  # Return the solution and success flag
        
        error_publisher.publish(std_msgs.msg.String(data="IK failed"))  # Publish an error message if no solution found
        logger.warn('No valid pose could be found. Will not execute')  # Log a warning
        return theta_list, False  # Return the last attempted solution and failure flag

    def cb(msg: geometry_msgs.msg.PoseStamped):
        # Callback function for handling incoming goal pose messages
        T_sd = pt.transform_from_pq(np.array(pq_from_ros_pose(msg.pose)))  # Convert ROS pose to transformation matrix
        set_ee_pose_matrix(T_sd)  # Compute and set joint positions to achieve the pose
    node.create_subscription(geometry_msgs.msg.PoseStamped, "goal_pose", cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to goal poses

    rclpy.spin(node)  # Enter the ROS event loop to process messages

    node.destroy_node()  # Explicitly destroy the node (optional)
    rclpy.shutdown()  # Shut down the ROS 2 runtime

if __name__ == '__main__':
    main()  # Entry point of the script