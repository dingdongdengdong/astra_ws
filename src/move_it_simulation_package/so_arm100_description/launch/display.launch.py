from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # Launch argument to select hardware type (mock or real)
        DeclareLaunchArgument(
            name='ros2_control_hardware_type',
            default_value='mock_components',
            description='Type of ros2_control hardware interface plugin'
        ),

        # robot_state_publisher node
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': Command([
                    PathJoinSubstitution([
                        FindExecutable(name='xacro')
                    ]),
                    ' ',
                    PathJoinSubstitution([
                        FindPackageShare('so_arm100_description'),
                        'urdf',
                        'so_arm100.urdf.xacro'
                    ]),
                    ' ',
                    'ros2_control_hardware_type:=',
                    LaunchConfiguration('ros2_control_hardware_type')
                ])
            }]
        ),

        # joint_state_publisher_gui node (for manual control of joints)
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen'
        ),

        # RViz2 node
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', PathJoinSubstitution([
                FindPackageShare('so_arm100_description'),
                'rviz',
                'model.rviz'
            ])]
        )
    ])
