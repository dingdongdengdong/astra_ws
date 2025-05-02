cmake_minimum_required(VERSION 3.22)
project(so_arm100_moveit_config)

find_package(ament_cmake REQUIRED)

# Install all launch files
install(
  DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install all configuration files
install(
  DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

# Install MoveIt Setup Assistant metadata
install(
  FILES .setup_assistant
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
