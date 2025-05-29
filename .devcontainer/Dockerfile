FROM ros:humble-ros-base

ARG USERNAME=rosdev
ARG UID=1000
ARG GID=$UID

# Install some dependencies packages
RUN apt update -q \
    && apt upgrade -q -y \
    && apt install -y --no-install-recommends \
    software-properties-common \
    python3-pip \
    python-is-python3 \
    xauth \
    ros-humble-desktop \
    ros-dev-tools \
    ros-humble-camera-info-manager \
    ros-humble-srdfdom \
    ###for simulation
    ros-humble-moveit-configs-utils \
    ros-humble-moveit \

    libopus-dev \
    libvpx-dev \
    v4l-utils \
    # Added FFMPEG dev libraries for PyAV
    libavformat-dev libavcodec-dev libswscale-dev libavfilter-dev libavdevice-dev libswresample-dev \
    
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python build tools and pytoml (system-wide for availability)
RUN pip install --no-cache-dir pytoml poetry

# Create and switch to user
RUN groupadd -g $GID $USERNAME \
    && useradd -lm -u $UID -g $USERNAME -s /bin/bash $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER $USERNAME

# Create workspace so that user own this directory
# $HOME은 이 시점에서 /home/$USERNAME으로 설정됩니다.
RUN mkdir -p $HOME/ros2_ws/src

# Copy non_ros_src into the image, owned by the user
COPY --chown=$USERNAME:$USERNAME non_ros_src $HOME/ros2_ws/non_ros_src

# Set WORKDIR for subsequent Python package installations
WORKDIR $HOME/ros2_ws

# Install Python dependencies from requirements.txt files (as user)
RUN pip install --no-cache-dir --user \
    -r $HOME/ros2_ws/non_ros_src/aiortc/requirements/lint.txt \
    -r $HOME/ros2_ws/non_ros_src/aiortc/requirements/doc.txt \
    -r $HOME/ros2_ws/non_ros_src/odrive-can/docker/requirements.txt \
    -r $HOME/ros2_ws/non_ros_src/pyribbit/requirements.txt \
    -r $HOME/ros2_ws/non_ros_src/urchin/requirements.txt

# Install lerobot using poetry (as user)
WORKDIR $HOME/ros2_ws/non_ros_src/lerobot
RUN poetry config virtualenvs.create false && \
    poetry install --no-cache --no-dev --no-interaction --no-ansi

# Install other Python packages from source (as user)
WORKDIR $HOME/ros2_ws # Reset WORKDIR to ensure correct relative paths if any were used, or use absolute paths
RUN pip install --no-cache-dir --user \
    $HOME/ros2_ws/non_ros_src/aiortc \
    $HOME/ros2_ws/non_ros_src/astra_teleop \
    $HOME/ros2_ws/non_ros_src/astra_teleop_web \
    $HOME/ros2_ws/non_ros_src/mr_urdf_loader \
    $HOME/ros2_ws/non_ros_src/PyAV \
    $HOME/ros2_ws/non_ros_src/odrive-can \
    $HOME/ros2_ws/non_ros_src/pyribbit \
    $HOME/ros2_ws/non_ros_src/urchin \
    $HOME/ros2_ws/non_ros_src/ModernRobotics/packages/Python

# Original WORKDIR setting for the rest of the setup
WORKDIR $HOME/ros2_ws

# Copy configuration files
# $HOME/.bashrc를 대상으로 하고, 내용에도 $HOME을 사용합니다.
RUN echo 'source /opt/ros/'$ROS_DISTRO'/setup.bash' >> $HOME/.bashrc \
    && echo 'source $HOME/ros2_ws/install/setup.bash' >> $HOME/.bashrc \
    && echo 'export PATH="$HOME/.local/bin:$PATH"' >> $HOME/.bashrc

# Setup entrypoint
COPY ./ros_entrypoint.sh /
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]