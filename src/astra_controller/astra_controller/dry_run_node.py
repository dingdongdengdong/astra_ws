import rclpy  # ROS 2 Python client library
import rclpy.node  # Node class for ROS nodes
import rclpy.qos  # QoS settings for ROS communication

import sensor_msgs.msg  # Sensor messages (e.g., JointState)
import astra_controller_interfaces.msg  # Custom messages for joint commands
import numpy as np  # NumPy for array operations (not heavily used here)
import threading  # Threading for periodic publishing
import time  # Time functions for delays

import logging  # Logging for debug/info messages

logger = logging.getLogger(__name__)  # Logger for this module

np.set_printoptions(precision=4, suppress=True)  # Configure NumPy printing (not used here)

def main(args=None):
    rclpy.init(args=args)  # Initialize ROS 2
    node = rclpy.node.Node("dry_run_node")  # Create ROS node named 'dry_run_node'

    joint_state_publisher = node.create_publisher(sensor_msgs.msg.JointState, "joint_states", 10)  # Publisher for joint states
    
    # Declare parameters with defaults
    node.declare_parameter('actively_send_joint_state', True)  # Whether to actively publish joint states
    node.declare_parameter('joint_names', ["joint_l1", "joint_l2", "joint_l3", "joint_l4", "joint_l5", "joint_l6", "joint_l7r", "joint_l7l"])  # List of joint names

    actively_send_joint_state = node.get_parameter('actively_send_joint_state').value  # Get parameter value
    joint_names = node.get_parameter('joint_names').value  # Get joint names
    
    assert len(joint_names) == 8  # Ensure exactly 8 joints (lift, 5 arm, 2 gripper)

    if actively_send_joint_state:
        # Initialize joint states dictionary with zeros
        joint_states = {joint_name: 0.0 for joint_name in joint_names}
        def publish_joint_states():
            # Thread function to periodically publish joint states
            while True:
                msg = sensor_msgs.msg.JointState()
                msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
                msg.name = list(joint_states.keys())  # Joint names
                msg.position = [float(x) for x in joint_states.values()]  # Joint positions

                joint_state_publisher.publish(msg)  # Publish joint states
                time.sleep(0.1)  # Publish at 10 Hz
        t = threading.Thread(target=publish_joint_states, daemon=True)
        t.start()  # Start publishing thread

    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback for arm joint commands (joints 2-6)
        assert msg.name == joint_names[1:6]  # Ensure correct joint names for arm
        
        send_msg = sensor_msgs.msg.JointState()
        send_msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
        send_msg.name = joint_names[1:6]  # Arm joint names
        send_msg.position = msg.position_cmd  # Set commanded positions
        joint_state_publisher.publish(send_msg)  # Publish joint states

        if actively_send_joint_state:
            joint_states.update(dict(zip(send_msg.name, send_msg.position)))  # Update local state
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, "arm/joint_command", cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to arm commands

    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback for gripper joint commands (joints 7-8)
        assert msg.name == joint_names[6:7]  # Ensure correct joint name for gripper command
        
        send_msg = sensor_msgs.msg.JointState()
        send_msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
        send_msg.name = joint_names[6:8]  # Gripper joint names (right and left)
        send_msg.position = [msg.position_cmd[0], -msg.position_cmd[0]]  # Mirror positions for gripper
        joint_state_publisher.publish(send_msg)  # Publish joint states

        if actively_send_joint_state:
            joint_states.update(dict(zip(send_msg.name, send_msg.position)))  # Update local state
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, "arm/gripper_joint_command", cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to gripper commands

    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback for lift joint command (joint 1)
        assert msg.name == joint_names[0:1]  # Ensure correct joint name for lift
        
        send_msg = sensor_msgs.msg.JointState()
        send_msg.header.stamp = node.get_clock().now().to_msg()  # Current timestamp
        send_msg.name = joint_names[0:1]  # Lift joint name
        send_msg.position = msg.position_cmd  # Set commanded position
        joint_state_publisher.publish(send_msg)  # Publish joint states

        if actively_send_joint_state:
            joint_states.update(dict(zip(send_msg.name, send_msg.position)))  # Update local state
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, "lift/joint_command", cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to lift commands

    rclpy.spin(node)  # Run ROS event loop

    node.destroy_node()  # Clean up node
    rclpy.shutdown()  # Shutdown ROS

if __name__ == '__main__':
    main()  # Entry point