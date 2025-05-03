import rclpy  # ROS 2 Python client library for node creation and communication
import rclpy.node  # Base class for creating ROS nodes
import rclpy.qos  # Quality of Service settings for reliable communication
import rclpy.action  # Support for ROS actions (not used here)

import sensor_msgs.msg  # Standard ROS messages for sensor data, e.g., JointState
import astra_controller_interfaces.msg  # Custom ROS messages for joint commands
#import astra_controller_interfaces.srv  # Custom ROS services (not used here)
import std_msgs.msg  # Standard ROS messages, e.g., String for errors

from .lift_controller import LiftController  # Import the LiftController class from the same package

def main(args=None):
    # Main function to set up and run the ROS node
    rclpy.init(args=args)  # Initialize the ROS 2 runtime

    node = rclpy.node.Node('lift_node')  # Create a ROS node named "lift_node"

    logger = node.get_logger()  # Get a logger instance for this node
    
    node.declare_parameter('device', '/dev/tty_puppet_lift_right')  # Declare parameter for the serial device
    node.declare_parameter('joint_names', ["joint_r1"])  # Declare parameter for the lift joint name

    device = node.get_parameter('device').value  # Retrieve the serial device name
    joint_names = node.get_parameter('joint_names').value  # Retrieve the joint name (should be just "joint_r1")
    
    assert len(joint_names) == 1  # Ensure there is exactly one joint (the lift)

    lift_controller = LiftController(device)  # Instantiate the LiftController with the serial device

    joint_state_publisher = node.create_publisher(sensor_msgs.msg.JointState, "joint_states", 10)  # Create a publisher for joint states

    def cb(position, velocity, effort, this_time):
        # Callback function to publish joint states from LiftController data
        msg = sensor_msgs.msg.JointState()  # Create a new JointState message
        msg.header.stamp = node.get_clock().now().to_msg()  # Set the current timestamp
        msg.name = joint_names  # Assign the lift joint name
        msg.position = [float(position)]  # Convert position to float list
        msg.velocity = [float(velocity)]  # Convert velocity to float list
        msg.effort = [float(effort)]  # Convert effort to float list
        joint_state_publisher.publish(msg)  # Publish the joint state message
    lift_controller.state_cb = cb  # Set this callback as the state callback for LiftController

    error_publisher = node.create_publisher(std_msgs.msg.String, 'error', 10)  # Create a publisher for error messages

    def cb(data):
        # Callback function for publishing error messages from LiftController
        error_publisher.publish(std_msgs.msg.String(data=data))  # Publish the error string
    lift_controller.error_cb = cb  # Set this callback as the error callback for LiftController
    
    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback function for handling incoming joint command messages
        assert msg.name == joint_names  # Verify the joint name matches "joint_r1"
        lift_controller.set_pos(msg.position_cmd[0])  # Set the lift position from the first command
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, 'joint_command', cb, rclpy.qos.qos_profile_sensor_data)  # Subscribe to joint commands

    rclpy.spin(node)  # Enter the ROS event loop to process messages

    node.destroy_node()  # Explicitly destroy the node (optional)
    rclpy.shutdown()  # Shut down the ROS 2 runtime

if __name__ == '__main__':
    main()  # Entry point of the script