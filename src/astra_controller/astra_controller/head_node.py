import rclpy  # ROS 2 Python client library for node creation and communication
import rclpy.node  # Base class for creating ROS nodes
import rclpy.qos  # Quality of Service settings for reliable communication

import astra_controller_interfaces.msg  # Custom ROS messages for joint commands
import sensor_msgs.msg  # Standard ROS messages for sensor data, e.g., JointState
import std_msgs.msg  # Standard ROS messages, e.g., UInt8 for torque

from astra_controller.head_controller import HeadController  # Import the HeadController class

import numpy as np  # Library for numerical operations

def main(args=None):
    # Main function to set up and run the ROS node
    rclpy.init(args=args)  # Initialize the ROS 2 runtime

    node = rclpy.node.Node("head_node")  # Create a ROS node named "head_node"

    logger = node.get_logger()  # Get a logger instance for this node
    
    node.declare_parameter('device', '/dev/tty_head')  # Declare a parameter for the serial device with a default value

    device = node.get_parameter('device').value  # Retrieve the serial device name from the parameter
    joint_names = ["joint_head_pan", "joint_head_tilt"]  # Define the names of the head joints (pan and tilt)

    head_controller = HeadController(device)  # Instantiate the HeadController with the serial device

    joint_state_publisher = node.create_publisher(sensor_msgs.msg.JointState, "joint_states", 10)  # Create a publisher for joint states

    def cb(position, velocity, effort, this_time):
        # Callback function to publish joint states from HeadController data
        msg = sensor_msgs.msg.JointState()  # Create a new JointState message
        msg.header.stamp = node.get_clock().now().to_msg()  # Set the current timestamp
        assert len(position) == len(velocity) == len(effort) == len(joint_names)  # Ensure data matches number of joints
        msg.name = joint_names  # Assign joint names to the message
        msg.position = [float(p) for p in position]  # Convert positions to float list
        msg.velocity = [float(v) for v in velocity]  # Convert velocities to float list
        msg.effort = [float(e) for e in effort]  # Convert efforts to float list
        joint_state_publisher.publish(msg)  # Publish the joint state message
    head_controller.state_cb = cb  # Set this callback as the state callback for HeadController

    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback function for handling incoming joint command messages
        assert msg.name == joint_names  # Verify the joint names match expected ones
        assert len(msg.position_cmd) == len(joint_names)  # Verify the number of position commands matches joints
        position_cmd = msg.position_cmd  # Extract the position commands
        head_controller.set_pos(np.array(position_cmd, dtype=np.float32))  # Set the positions on the head controller
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, 'joint_command', cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to joint commands

    def cb(msg: std_msgs.msg.UInt8):
        # Callback function for handling torque enable/disable messages
        logger.info(f'torque_enable: {msg.data}')  # Log the torque state (0 or 1)
        head_controller.set_torque(msg.data)  # Enable or disable torque based on message
    node.create_subscription(std_msgs.msg.UInt8, 'torque_enable', cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to torque commands

    try:
        rclpy.spin(node)  # Enter the ROS event loop to process messages
    except KeyboardInterrupt as err:
        head_controller.stop()  # Stop the head controller on interrupt (e.g., Ctrl+C)
        raise err  # Re-raise the interrupt to exit cleanly

    node.destroy_node()  # Explicitly destroy the node (optional, done by garbage collector otherwise)
    rclpy.shutdown()  # Shut down the ROS 2 runtime

if __name__ == '__main__':
    main()  # Entry point of the script