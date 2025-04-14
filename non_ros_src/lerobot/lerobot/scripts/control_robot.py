"""
Utilities to control a robot.

Useful to record a dataset, replay a recorded episode, run the policy on your robot
and record an evaluation dataset, and to recalibrate your robot if needed.

Examples of usage:

- Recalibrate your robot:
```bash
python lerobot/scripts/control_robot.py \
    --robot.type=so100 \
    --control.type=calibrate
```

- Unlimited teleoperation at highest frequency (~200 Hz is expected), to exit with CTRL+C:
```bash
python lerobot/scripts/control_robot.py \
    --robot.type=so100 \
    --robot.cameras='{}' \
    --control.type=teleoperate

# Add the cameras from the robot definition to visualize them:
python lerobot/scripts/control_robot.py \
    --robot.type=so100 \
    --control.type=teleoperate
```

- Unlimited teleoperation at a limited frequency of 30 Hz, to simulate data recording frequency:
```bash
python lerobot/scripts/control_robot.py \
    --robot.type=so100 \
    --control.type=teleoperate \
    --control.fps=30
```

- Record one episode in order to test replay:
```bash
python lerobot/scripts/control_robot.py \
    --robot.type=so100 \
    --control.type=record \
    --control.fps=30 \
    --control.single_task="Grasp a lego block and put it in the bin." \
    --control.repo_id=$USER/koch_test \
    --control.num_episodes=1 \
    --control.push_to_hub=True
```

- Visualize dataset:
```bash
python lerobot/scripts/visualize_dataset.py \
    --repo-id $USER/koch_test \
    --episode-index 0
```

- Replay this test episode:
```bash
python lerobot/scripts/control_robot.py replay \
    --robot.type=so100 \
    --control.type=replay \
    --control.fps=30 \
    --control.repo_id=$USER/koch_test \
    --control.episode=0
```

- Record a full dataset in order to train a policy, with 2 seconds of warmup,
30 seconds of recording for each episode, and 10 seconds to reset the environment in between episodes:
```bash
python lerobot/scripts/control_robot.py record \
    --robot.type=so100 \
    --control.type=record \
    --control.fps 30 \
    --control.repo_id=$USER/koch_pick_place_lego \
    --control.num_episodes=50 \
    --control.warmup_time_s=2 \
    --control.episode_time_s=30 \
    --control.reset_time_s=10
```

**NOTE**: You can use your keyboard to control data recording flow.
- Tap right arrow key '->' to early exit while recording an episode and go to resseting the environment.
- Tap right arrow key '->' to early exit while resetting the environment and got to recording the next episode.
- Tap left arrow key '<-' to early exit and re-record the current episode.
- Tap escape key 'esc' to stop the data recording.
This might require a sudo permission to allow your terminal to monitor keyboard events.

**NOTE**: You can resume/continue data recording by running the same data recording command and adding `--control.resume=true`.
If the dataset you want to extend is not on the hub, you also need to add `--control.local_files_only=true`.

- Train on this dataset with the ACT policy:
```bash
python lerobot/scripts/train.py \
  --dataset.repo_id=${HF_USER}/koch_pick_place_lego \
  --policy.type=act \
  --output_dir=outputs/train/act_koch_pick_place_lego \
  --job_name=act_koch_pick_place_lego \
  --device=cuda \
  --wandb.enable=true
```

- Run the pretrained policy on the robot:
```bash
python lerobot/scripts/control_robot.py \
    --robot.type=so100 \
    --control.type=record \
    --control.fps=30 \
    --control.single_task="Grasp a lego block and put it in the bin." \
    --control.repo_id=$USER/eval_act_koch_pick_place_lego \
    --control.num_episodes=10 \
    --control.warmup_time_s=2 \
    --control.episode_time_s=30 \
    --control.reset_time_s=10 \
    --control.push_to_hub=true \
    --control.policy.path=outputs/train/act_koch_pick_place_lego/checkpoints/080000/pretrained_model
```
"""
# Docstring with usage examples:
# - Explains how to calibrate, teleoperate, record, and replay using command-line arguments.
# - Includes notes on keyboard controls and resuming recording.
"""
Utilities to control a robot.
[... see original docstring for examples ...]
"""

# Import libraries:
# - Standard Python modules (logging, time, etc.) for general utilities.
# - LeRobot-specific modules for dataset management, policy creation, and robot control.
import logging
import time
from dataclasses import asdict
from pprint import pformat
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.policies.factory import make_policy
from lerobot.common.robot_devices.control_configs import (
    CalibrateControlConfig,
    ControlPipelineConfig,
    RecordControlConfig,
    ReplayControlConfig,
    TeleoperateControlConfig,
)
from lerobot.common.robot_devices.control_utils import (
    control_loop,
    init_keyboard_listener,
    log_control_info,
    record_episode,
    reset_environment,
    sanity_check_dataset_name,
    sanity_check_dataset_robot_compatibility,
    stop_recording,
    warmup_record,
)
from lerobot.common.robot_devices.robots.utils import Robot, make_robot_from_config
from lerobot.common.robot_devices.utils import busy_wait, safe_disconnect
from lerobot.common.utils.utils import has_method, init_logging, log_say
from lerobot.configs import parser

# Calibration function:
# - Recalibrates the robot by removing existing calibration files and reconnecting.
@safe_disconnect
def calibrate(robot: Robot, cfg: CalibrateControlConfig):
    # Special case for "stretch" robots:
    if robot.robot_type.startswith("stretch"):
        if not robot.is_connected:
            robot.connect()
        if not robot.is_homed():
            robot.home()
        return

    # Determine arms to calibrate:
    arms = robot.available_arms if cfg.arms is None else cfg.arms
    unknown_arms = [arm_id for arm_id in arms if arm_id not in robot.available_arms]
    available_arms_str = " ".join(robot.available_arms)
    unknown_arms_str = " ".join(unknown_arms)

    # Validate arms input:
    if arms is None or len(arms) == 0:
        raise ValueError(f"No arm provided. Use `--arms {available_arms_str}`")
    if len(unknown_arms) > 0:
        raise ValueError(f"Unknown arms: '{unknown_arms_str}'. Available: `{available_arms_str}`")

    # Remove existing calibration files:
    for arm_id in arms:
        arm_calib_path = robot.calibration_dir / f"{arm_id}.json"
        if arm_calib_path.exists():
            print(f"Removing '{arm_calib_path}'")
            arm_calib_path.unlink()
        else:
            print(f"Calibration file not found '{arm_calib_path}'")

    # Disconnect and reconnect to trigger calibration:
    if robot.is_connected:
        robot.disconnect()
    robot.connect()
    robot.disconnect()
    print("Calibration is done! You can now teleoperate and record datasets!")

# Teleoperation function:
# - Allows manual control of the robot with optional camera display.
@safe_disconnect
def teleoperate(robot: Robot, cfg: TeleoperateControlConfig):
    control_loop(
        robot,
        control_time_s=cfg.teleop_time_s,  # Duration of teleoperation.
        fps=cfg.fps,                       # Control frequency.
        teleoperate=True,                  # Enable teleoperation mode.
        display_cameras=cfg.display_cameras,  # Show camera feeds if enabled.
    )

# Recording function:
# - Records datasets by controlling the robot manually or with a policy.
@safe_disconnect
def record(robot: Robot, cfg: RecordControlConfig) -> LeRobotDataset:
    # Resume existing dataset or create a new one:
    if cfg.resume:
        dataset = LeRobotDataset(cfg.repo_id, root=cfg.root, local_files_only=cfg.local_files_only)
        if len(robot.camera_features) > 0:
            dataset.start_image_writer(
                num_processes=cfg.num_image_writer_processes,
                num_threads=cfg.num_image_writer_threads_per_camera * len(robot.camera_features),
            )
        sanity_check_dataset_robot_compatibility(dataset, robot, cfg.fps, cfg.video)
    else:
        sanity_check_dataset_name(cfg.repo_id, cfg.policy)
        dataset = LeRobotDataset.create(
            cfg.repo_id,
            cfg.fps,
            root=cfg.root,
            robot=robot,
            use_videos=cfg.video,
            image_writer_processes=cfg.num_image_writer_processes,
            image_writer_threads=cfg.num_image_writer_threads_per_camera * len(robot.camera_features),
        )

    # Load policy if provided:
    policy = None if cfg.policy is None else make_policy(cfg.policy, cfg.device, ds_meta=dataset.meta)

    # Connect to the robot:
    if not robot.is_connected:
        robot.connect()

    # Initialize keyboard listener for control:
    listener, events = init_keyboard_listener()

    # Warmup phase:
    # - Allows initial positioning and synchronization.
    enable_teleoperation = policy is None
    log_say("Warmup record", cfg.play_sounds)
    warmup_record(robot, events, enable_teleoperation, cfg.warmup_time_s, cfg.display_cameras, cfg.fps)

    # Safety stop if supported:
    if has_method(robot, "teleop_safety_stop"):
        robot.teleop_safety_stop()

    # Record episodes:
    recorded_episodes = 0
    while True:
        if recorded_episodes >= cfg.num_episodes:
            break

        # Reset environment between episodes:
        if not events["stop_recording"] and (
            (recorded_episodes < cfg.num_episodes) or events["rerecord_episode"]
        ):
            log_say("Reset the environment", cfg.play_sounds)
            reset_environment(robot, events, cfg.reset_time_s)

        # Record an episode:
        log_say(f"Recording episode {dataset.num_episodes}", cfg.play_sounds)
        record_episode(
            dataset=dataset,
            robot=robot,
            events=events,
            episode_time_s=cfg.episode_time_s,
            display_cameras=cfg.display_cameras,
            policy=policy,
            device=cfg.device,
            use_amp=cfg.use_amp,
            fps=cfg.fps,
        )

        # Handle re-recording:
        if events["rerecord_episode"]:
            log_say("Re-record episode", cfg.play_sounds)
            events["rerecord_episode"] = False
            events["exit_early"] = False
            dataset.clear_episode_buffer()
            continue

        # Save episode without encoding videos:
        dataset.save_episode(cfg.single_task, encode_videos=False)
        recorded_episodes += 1

        if events["stop_recording"]:
            break

    # Finalize recording:
    log_say("Stop recording", cfg.play_sounds, blocking=True)
    stop_recording(robot, listener, cfg.display_cameras)

    # Compute stats and push to hub if enabled:
    if cfg.run_compute_stats:
        logging.info("Computing dataset statistics")
    dataset.consolidate(cfg.run_compute_stats)
    if cfg.push_to_hub:
        dataset.push_to_hub(tags=cfg.tags, private=cfg.private)

    log_say("Exiting", cfg.play_sounds)
    return dataset

# Replay function:
# - Replays a recorded episode by sending actions to the robot.
@safe_disconnect
def replay(robot: Robot, cfg: ReplayControlConfig):
    # Load the dataset for the specified episode:
    dataset = LeRobotDataset(
        cfg.repo_id, root=cfg.root, episodes=[cfg.episode], local_files_only=cfg.local_files_only
    )
    actions = dataset.hf_dataset.select_columns("action")

    # Connect to the robot:
    if not robot.is_connected:
        robot.connect()

    # Replay the episode:
    log_say("Replaying episode", cfg.play_sounds, blocking=True)
    for idx in range(dataset.num_frames):
        start_episode_t = time.perf_counter()
        action = actions[idx]["action"]
        robot.send_action(action)  # Send action to the robot.

        # Maintain timing:
        dt_s = time.perf_counter() - start_episode_t
        busy_wait(1 / cfg.fps - dt_s)  # Wait to match the specified fps.
        dt_s = time.perf_counter() - start_episode_t
        log_control_info(robot, dt_s, fps=cfg.fps)  # Log timing info.

# Main control function:
# - Parses config and executes the appropriate control mode.
@parser.wrap()
def control_robot(cfg: ControlPipelineConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))  # Log configuration.

    # Create robot instance from config:
    robot = make_robot_from_config(cfg.robot)

    # Execute control mode based on config:
    if isinstance(cfg.control, CalibrateControlConfig):
        calibrate(robot, cfg.control)
    elif isinstance(cfg.control, TeleoperateControlConfig):
        teleoperate(robot, cfg.control)
    elif isinstance(cfg.control, RecordControlConfig):
        record(robot, cfg.control)
    elif isinstance(cfg.control, ReplayControlConfig):
        replay(robot, cfg.control)

    # Ensure clean disconnection:
    if robot.is_connected:
        robot.disconnect()

# Entry point:
if __name__ == "__main__":
    control_robot()

"""
Key Features and Purpose
Purpose: Provides a comprehensive interface for robot control and data collection.
Control Modes:
Calibrate: Recalibrates arms by managing calibration files.
Teleoperate: Manual control with customizable frequency and camera display.
Record: Captures datasets with warmup, reset, and policy support; delays video encoding.
Replay: Replays episodes at a specified frequency.
Keyboard Controls: Allows dynamic recording adjustments (e.g., stop, re-record).
Policy Integration: Supports automated control with pretrained policies.
"""