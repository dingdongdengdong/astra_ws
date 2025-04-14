import rclpy  # ROS 2 Python client library
import rclpy.node  # Node class for creating ROS nodes
import rclpy.qos  # Quality of Service settings for ROS communication
import rclpy.action  # Action client/server support (not used here)

import nav_msgs.msg  # Navigation messages (e.g., Odometry)
import geometry_msgs.msg  # Geometry messages (e.g., Twist, TransformStamped)
import std_msgs.msg  # Standard messages (e.g., Float32)
import tf2_ros  # TF2 library for broadcasting transforms
import math  # Math functions (e.g., cos, sin)

from .base_controller import BaseController  # Custom class for motor control

from pytransform3d import rotations as pr  # Library for quaternion calculations

def main(args=None):
    rclpy.init(args=args)  # Initialize ROS 2 with command-line args

    node = rclpy.node.Node('base_node')  # Create a ROS node named 'base_node'

    logger = node.get_logger()  # Logger for debugging/info messages

    node.declare_parameter('device', 'can0')  # Declare CAN device parameter with default 'can0'
    device = node.get_parameter('device').value  # Get the CAN device name from parameters

    base_controller = BaseController(device)  # Initialize BaseController with CAN device

    # Initialize robot position and orientation (x, y, yaw)
    pos_x = 0.0  # X position in meters
    pos_y = 0.0  # Y position in meters
    pos_theta = 0.0  # Yaw angle in radians

    odom_publisher = node.create_publisher(nav_msgs.msg.Odometry, "odom", 10)  # Publisher for odometry data
    tf_broadcaster = tf2_ros.TransformBroadcaster(node)  # Broadcaster for TF transforms

    def cb(linear_vel, angular_vel, dt):
        # Callback to compute and publish odometry based on velocity and time step
        nonlocal pos_x, pos_y, pos_theta  # Use nonlocal variables for position updates

        # Calculate position increments using unicycle kinematics
        d_x = linear_vel * math.cos(pos_theta) * dt  # X displacement
        d_y = linear_vel * math.sin(pos_theta) * dt  # Y displacement
        d_theta = angular_vel * dt  # Angular displacement

        # Update position and orientation
        pos_x += d_x
        pos_y += d_y
        pos_theta += d_theta
        quat = pr.quaternion_from_angle(2, pos_theta)  # Convert yaw to quaternion (axis 2 = z-axis)

        # Create and populate Odometry message
        odom_msg = nav_msgs.msg.Odometry()
        odom_msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
        odom_msg.header.frame_id = "odom"  # Fixed frame (world frame)
        odom_msg.child_frame_id = "base_link"  # Moving frame (robot base)

        # Set position in odometry message
        odom_msg.pose.pose.position.x = pos_x
        odom_msg.pose.pose.position.y = pos_y
        odom_msg.pose.pose.position.z = 0.0  # Assume 2D motion (z = 0)
        odom_msg.pose.pose.orientation.w = quat[0]  # Quaternion components
        odom_msg.pose.pose.orientation.x = quat[1]
        odom_msg.pose.pose.orientation.y = quat[2]
        odom_msg.pose.pose.orientation.z = quat[3]

        # Set velocity in odometry message
        odom_msg.twist.twist.linear.x = linear_vel  # Linear velocity in x-direction
        odom_msg.twist.twist.linear.y = 0.0  # No lateral motion (y = 0)
        odom_msg.twist.twist.angular.z = angular_vel  # Angular velocity around z-axis

        odom_publisher.publish(odom_msg)  # Publish odometry message

        # Create and populate TF transform message
        tf_msg = geometry_msgs.msg.TransformStamped()
        tf_msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
        tf_msg.header.frame_id = "odom"  # Parent frame
        tf_msg.child_frame_id = "base_link"  # Child frame

        # Set translation and rotation for TF
        tf_msg.transform.translation.x = odom_msg.pose.pose.position.x
        tf_msg.transform.translation.y = odom_msg.pose.pose.position.y
        tf_msg.transform.translation.z = odom_msg.pose.pose.position.z
        tf_msg.transform.rotation = odom_msg.pose.pose.orientation  # Copy orientation

        tf_broadcaster.sendTransform(tf_msg)  # Broadcast TF transform
    base_controller.state_cb = cb  # Assign callback to BaseController for state updates

    def cb(msg: geometry_msgs.msg.Twist):
        # Callback for velocity commands from 'cmd_vel' topic
        base_controller.set_vel(msg.linear.x, msg.angular.z)  # Set linear and angular velocities
    node.create_subscription(geometry_msgs.msg.Twist, 'cmd_vel', cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to velocity commands

    # Dictionary of publishers for debug topics
    debug_publishers = {}
    debug_publishers["curpos_left"] = node.create_publisher(std_msgs.msg.Float32, "base/debug/curpos_left", 10)  # Left wheel position
    debug_publishers["curpos_right"] = node.create_publisher(std_msgs.msg.Float32, "base/debug/curpos_right", 10)  # Right wheel position
    debug_publishers["setpos_left"] = node.create_publisher(std_msgs.msg.Float32, "base/debug/setpos_left", 10)  # Left wheel setpoint
    debug_publishers["setpos_right"] = node.create_publisher(std_msgs.msg.Float32, "base/debug/setpos_right", 10)  # Right wheel setpoint

    def debug_cb(name, value):
        # Callback to publish debug data
        assert name in debug_publishers  # Ensure topic name is valid
        msg = std_msgs.msg.Float32()
        msg.data = value  # Set debug value
        debug_publishers[name].publish(msg)  # Publish to appropriate topic
    base_controller.debug_cb = debug_cb  # Assign debug callback to BaseController

    try:
        rclpy.spin(node)  # Run ROS event loop
    except KeyboardInterrupt as err:
        base_controller.stop()  # Stop motors on interrupt
        raise err  # Re-raise interrupt

    node.destroy_node()  # Clean up node
    rclpy.shutdown()  # Shutdown ROS

if __name__ == '__main__':
    main()  # Entry point