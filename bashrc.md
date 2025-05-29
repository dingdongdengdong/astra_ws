alias sb="source ./install/setup.bash && echo \"install/setup.bash loaded!\""
alias ib="source ./install/local_setup.bash && echo \"install/local_setup.bash loaded!\""
alias rb="source ~/.bashrc; echo \"bashrc is reloaded!\""
alias ros_domain_id="export ROS_DOMAIN_ID=8 && echo \"ROS_DOMAIN_ID=8\""
alias humble="source /opt/ros/humble/setup.bash; ros_domain_id; echo \"ROS2 Humble is activated!\""

source ~/ros2_ws/.venv/bin/activate


source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export PYTHONPATH="/home/jammy/ros2_ws/.venv/lib/python3.10/site-packages:$PYTHONPATH"
