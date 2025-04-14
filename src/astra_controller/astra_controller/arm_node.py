import rclpy
import rclpy.node
import rclpy.qos
import rclpy.action
import sensor_msgs.msg
import std_msgs.msg
import astra_controller_interfaces.msg
import struct
from .arm_controller import ArmController

def main(args=None):
    # Initialize ROS
    rclpy.init(args=args)
    node = rclpy.node.Node('arm_node')  # Create a ROS node named 'arm_node'
    logger = node.get_logger()  # Get logger for this node

    # Declare parameters with defaults
    node.declare_parameter('device', '/dev/tty_puppet_right')  # Serial device path
    node.declare_parameter('joint_names', ["joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"])  # Arm joint names
    node.declare_parameter('gripper_joint_names', ["joint_r7l", "joint_r7r"])  # Gripper joint names (left, right)

    # Retrieve parameter values
    device = node.get_parameter('device').value
    joint_names = node.get_parameter('joint_names').value
    gripper_joint_names = node.get_parameter('gripper_joint_names').value

    assert len(joint_names) == 5  # Ensure 5 arm joints
    assert len(gripper_joint_names) == 2  # Ensure 2 gripper joints

    arm_controller = ArmController(device)  # Initialize ArmController with device

    # Create publishers for joint states
    joint_state_publisher = node.create_publisher(sensor_msgs.msg.JointState, "joint_states", 10)  # Arm joint states
    gripper_joint_state_publisher = node.create_publisher(sensor_msgs.msg.JointState, "gripper_joint_states", 10)  # Gripper joint states

    def cb(position, velocity, effort, this_time):
        # Callback to publish joint states from ArmController
        msg = sensor_msgs.msg.JointState()
        msg.header.stamp = node.get_clock().now().to_msg()  # Set timestamp
        msg.name = joint_names  # Arm joint names
        msg.position = [float(p) for p in position[:5]]  # Positions for joints 0-4
        msg.velocity = [float(v) for v in velocity[:5]]  # Velocities for joints 0-4
        msg.effort = [float(e) for e in effort[:5]]  # Efforts for joints 0-4
        joint_state_publisher.publish(msg)  # Publish arm joint states

        msg = sensor_msgs.msg.JointState()
        msg.header.stamp = node.get_clock().now().to_msg()  # Set timestamp
        msg.name = gripper_joint_names  # Gripper joint names
        msg.position = [-float(position[5]), float(position[5])]  # Mirror gripper position (left negative, right positive)
        msg.velocity = [-float(velocity[5]), float(velocity[5])]  # Mirror gripper velocity
        msg.effort = [-float(effort[5]), float(effort[5])]  # Mirror gripper effort
        gripper_joint_state_publisher.publish(msg)  # Publish gripper joint states
    arm_controller.state_cb = cb  # Assign callback to ArmController

    # Publisher for debug data
    debug_publisher = node.create_publisher(std_msgs.msg.Float32MultiArray, 'debug', 10)
    def cb(data):
        # Callback to publish debug data
        msg = std_msgs.msg.Float32MultiArray()
        msg.data = data  # Float array of debug values
        debug_publisher.publish(msg)
    arm_controller.debug_cb = cb  # Assign debug callback

    # Publisher for pong responses
    pong_publisher = node.create_publisher(std_msgs.msg.UInt16MultiArray, 'pong', 10)
    def cb(data):
        # Callback to publish pong responses
        logger.info(f'pong: {data}')
        pong_publisher.publish(std_msgs.msg.UInt16MultiArray(data=data))  # Publish 6 uint16 values
    arm_controller.pong_cb = cb  # Assign pong callback

    # Publisher for error messages
    error_publisher = node.create_publisher(std_msgs.msg.String, 'error', 10)
    def cb(data):
        # Callback to publish error messages
        error_publisher.publish(std_msgs.msg.String(data=data))
    arm_controller.error_cb = cb  # Assign error callback

    last_position_cmd = arm_controller.get_pos()[0]  # Get initial position command
    logger.info(f"using initial state {last_position_cmd}")

    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback for arm joint commands
        nonlocal last_position_cmd
        assert msg.name == joint_names  # Verify joint names match
        position_cmd = [*msg.position_cmd[:5], last_position_cmd[5]]  # Update arm joints, keep gripper
        arm_controller.set_pos(position_cmd)  # Send position command
        last_position_cmd = position_cmd  # Update last command
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, 'joint_command', cb, rclpy.qos.qos_profile_sensor_data)

    def cb(msg: astra_controller_interfaces.msg.JointCommand):
        # Callback for gripper commands
        nonlocal last_position_cmd
        assert msg.name == gripper_joint_names[1:2]  # Verify right gripper joint name
        position_cmd = [*last_position_cmd[:5], msg.position_cmd[0]]  # Update gripper, keep arm joints
        arm_controller.set_pos(position_cmd)  # Send position command
        last_position_cmd = position_cmd  # Update last command
    node.create_subscription(astra_controller_interfaces.msg.JointCommand, 'gripper_joint_command', cb, rclpy.qos.qos_profile_sensor_data)

    def cb(msg: std_msgs.msg.UInt8):
        # Callback for torque enable/disable
        logger.info(f'torque_enable: {msg.data}')
        arm_controller.set_torque(msg.data)  # Set torque state
    node.create_subscription(std_msgs.msg.UInt8, 'torque_enable', cb, rclpy.qos.qos_profile_sensor_data)

    def cb(msg: std_msgs.msg.UInt16MultiArray):
        # Callback for ping commands
        logger.info(f'ping: {msg.data}')
        arm_controller.write(struct.pack('>BBHHHHHHHH', arm_controller.COMM_HEAD, arm_controller.COMM_TYPE_PING, *msg.data))  # Send ping packet
    node.create_subscription(std_msgs.msg.UInt16MultiArray, 'ping', cb, rclpy.qos.qos_profile_sensor_data)

    def cb(msg: std_msgs.msg.Float32MultiArray):
        # Callback to set PID parameters
        logger.info(f'set_pid: {msg.data}')
        arm_controller.set_pid(*msg.data)  # Update PID settings
    node.create_subscription(std_msgs.msg.Float32MultiArray, 'set_pid', cb, rclpy.qos.qos_profile_sensor_data)

    try:
        rclpy.spin(node)  # Start ROS event loop
    except KeyboardInterrupt as err:
        arm_controller.stop()  # Stop controller on interrupt
        raise err

    node.destroy_node()  # Clean up node
    rclpy.shutdown()  # Shutdown ROS

if __name__ == '__main__':
    main()