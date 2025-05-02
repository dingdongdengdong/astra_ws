from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import FindPackageShare, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            name="use_sim_time",
            default_value="false",
            description="Use simulation (Gazebo) clock if true",
        ),
        DeclareLaunchArgument(
            name="robot_description_file",
            default_value="so_arm100.urdf.xacro",
            description="URDF/XACRO file to load",
        ),
    ]

    pkg_description = FindPackageShare("so_arm100_description")

    urdf_file_path = PathJoinSubstitution([
        pkg_description,
        "urdf",
        LaunchConfiguration("robot_description_file"),
    ])

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": Command(["xacro ", urdf_file_path]),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }]
    )

    return LaunchDescription(declared_arguments + [robot_state_publisher_node])
