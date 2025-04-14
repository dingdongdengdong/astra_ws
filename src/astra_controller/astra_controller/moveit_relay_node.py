import rclpy  # ROS 2 Python client library for node creation and communication
import rclpy.node  # Base class for creating ROS nodes
import rclpy.qos  # Quality of Service settings for reliable communication
import rclpy.action  # Support for ROS actions, used here for action servers

import astra_controller_interfaces.msg  # Custom ROS messages for joint commands
import control_msgs.action  # Standard ROS action messages for joint trajectory control
import astra_controller_interfaces.srv  # Custom ROS service messages (not used here)

def main(args=None):
    # Main function to initialize and run the ROS node
    rclpy.init(args=args)  # Initialize the ROS 2 runtime environment

    node = rclpy.node.Node('moveit_relay_node')  # Create a ROS node named "moveit_relay_node"

    # Publishers to send joint commands to the robot's arm, gripper, and lift
    arm_joint_command_publisher = node.create_publisher(astra_controller_interfaces.msg.JointCommand, "arm/joint_command", 10)  # Arm joint command topic
    gripper_joint_command_publisher = node.create_publisher(astra_controller_interfaces.msg.JointCommand, "arm/gripper_joint_command", 10)  # Gripper joint command topic
    lift_joint_command_publisher = node.create_publisher(astra_controller_interfaces.msg.JointCommand, "lift/joint_command", 10)  # Lift joint command topic
    
    # Dictionary to store current joint positions, initialized to zero
    joint_pos = {
        "joint_r1": 0.0,  # Lift joint
        "joint_r2": 0.0,  # Arm joint 2
        "joint_r3": 0.0,  # Arm joint 3
        "joint_r4": 0.0,  # Arm joint 4
        "joint_r5": 0.0,  # Arm joint 5
        "joint_r6": 0.0,  # Arm joint 6
        "joint_r7l": 0.0,  # Left gripper joint (not used in this script)
        "joint_r7r": 0.0   # Right gripper joint
    }

    def execute_callback(goal_handle: rclpy.action.server.ServerGoalHandle):
        # Callback for arm action server to process joint trajectory goals from MoveIt
        node.get_logger().info('Executing goal...')  # Log the goal execution
        # Iterate over joint names and their target positions from the trajectory
        for joint_name, position in zip(
            goal_handle.request.trajectory.joint_names,  # Joint names from the goal
            goal_handle.request.trajectory.points[-1].positions  # Final positions in the trajectory
        ):
            joint_pos[joint_name] = position  # Update the joint position dictionary

        # Create and publish a JointCommand message for arm joints (joints 2-6)
        msg = astra_controller_interfaces.msg.JointCommand(
            name=["joint_r2", "joint_r3", "joint_r4", "joint_r5", "joint_r6"],  # Arm joint names
            position_cmd=[joint_pos["joint_r2"], joint_pos["joint_r3"], joint_pos["joint_r4"], joint_pos["joint_r5"], joint_pos["joint_r6"]]  # Target positions
        )
        arm_joint_command_publisher.publish(msg)  # Send arm joint commands

        # Create and publish a JointCommand message for the lift joint (joint_r1)
        msg = astra_controller_interfaces.msg.JointCommand(
            name=["joint_r1"],  # Lift joint name
            position_cmd=[joint_pos["joint_r1"]]  # Target position
        )
        lift_joint_command_publisher.publish(msg)  # Send lift joint command
        
        goal_handle.succeed()  # Mark the goal as successfully completed

        # Return the result of the action
        result = control_msgs.action.FollowJointTrajectory.Result()
        result.error_code = control_msgs.action.FollowJointTrajectory.Result.SUCCESSFUL  # Success code
        result.error_string = "SUCC"  # Success message
        return result
    
    # Create an action server for the arm trajectory controller
    rclpy.action.ActionServer(
        node,
        control_msgs.action.FollowJointTrajectory,  # Action type for joint trajectories
        '/astra_right_arm_controller/follow_joint_trajectory',  # Action server topic for arm
        execute_callback  # Callback to handle arm goals
    )

    def execute_callback(goal_handle: rclpy.action.server.ServerGoalHandle):
        # Callback for gripper action server to process joint trajectory goals from MoveIt
        node.get_logger().info('Executing goal...')  # Log the goal execution
        # Iterate over joint names and their target positions from the trajectory
        for joint_name, position in zip(
            goal_handle.request.trajectory.joint_names,  # Joint names from the goal
            goal_handle.request.trajectory.points[-1].positions  # Final positions in the trajectory
        ):
            joint_pos[joint_name] = position  # Update the joint position dictionary

        # Create and publish a JointCommand message for the gripper joint (joint_r7r)
        msg = astra_controller_interfaces.msg.JointCommand(
            name=["joint_r7r"],  # Right gripper joint name
            position_cmd=[joint_pos["joint_r7r"]]  # Target position
        )
        gripper_joint_command_publisher.publish(msg)  # Send gripper joint command
        
        goal_handle.succeed()  # Mark the goal as successfully completed

        # Return the result of the action
        result = control_msgs.action.FollowJointTrajectory.Result()
        result.error_code = control_msgs.action.FollowJointTrajectory.Result.SUCCESSFUL  # Success code
        result.error_string = "SUCC"  # Success message
        return result
    
    # Create an action server for the gripper trajectory controller
    rclpy.action.ActionServer(
        node,
        control_msgs.action.FollowJointTrajectory,  # Action type for joint trajectories
        '/astra_right_hand_controller/follow_joint_trajectory',  # Action server topic for gripper
        execute_callback  # Callback to handle gripper goals
    )

    rclpy.spin(node)  # Start the ROS event loop to process incoming goals

    node.destroy_node()  # Clean up the node when done (optional)
    rclpy.shutdown()  # Shut down the ROS 2 runtime

if __name__ == '__main__':
    main()  # Run the main function