from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import FindPackageShare
import os

def generate_launch_description():
    pkg_share = FindPackageShare("so_arm100_moveit_config").find("so_arm100_moveit_config")
    rviz_config_path = os.path.join(pkg_share, "config", "moveit.rviz")

    return LaunchDescription([
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="log",
            arguments=["-d", rviz_config_path],
            parameters=[
                {"use_sim_time": False}
            ]
        )
    ])
