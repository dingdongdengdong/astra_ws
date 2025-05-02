from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindPackageShare
import os

def generate_launch_description():
    moveit_config_pkg = FindPackageShare("so_arm100_moveit_config").find("so_arm100_moveit_config")

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(moveit_config_pkg, "launch", "move_group.launch.py")
            )
        )
    ])
