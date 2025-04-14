# Import required libraries (same as above).
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import tqdm
import os
from lerobot.common.datasets.utils import write_json, INFO_PATH

# Define dataset identifiers:
# - raw_repo_id: Source dataset with extended data.
# - repo_id: New dataset ID with "_base_cmd_pos" indicating base commands are now positions.
raw_repo_id = "lookas/astra_grab_floor_toys_extended"
repo_id = raw_repo_id + "_base_cmd_pos"

# Dataset configuration (same as above).
root = None
local_files_only = True

# Load the raw dataset (same as above).
raw_dataset = LeRobotDataset(
    raw_repo_id,
    root=root,
    local_files_only=local_files_only,
)

# Temporarily remove video features (same as above).
raw_video_features = {
    "observation.images.head": raw_dataset.meta.info["features"].pop("observation.images.head"),
    "observation.images.wrist_left": raw_dataset.meta.info["features"].pop("observation.images.wrist_left"),
    "observation.images.wrist_right": raw_dataset.meta.info["features"].pop("observation.images.wrist_right"),
}
assert len(raw_dataset.meta.video_keys) == 0

# Calculate action and observation dimensions (same as above).
action_dim = (raw_dataset.features["observation.state.arm_l"]["shape"][0]
    + raw_dataset.features["observation.state.gripper_l"]["shape"][0]
    + raw_dataset.features["observation.state.arm_r"]["shape"][0]
    + raw_dataset.features["observation.state.gripper_r"]["shape"][0]
    + raw_dataset.features["observation.state.base"]["shape"][0]
    + raw_dataset.features["observation.state.head"]["shape"][0])

obs_dim = (raw_dataset.features["observation.state.arm_l"]["shape"][0]
    + raw_dataset.features["observation.state.gripper_l"]["shape"][0]
    + raw_dataset.features["observation.state.arm_r"]["shape"][0]
    + raw_dataset.features["observation.state.gripper_r"]["shape"][0]
    + raw_dataset.features["observation.state.base"]["shape"][0]
    + raw_dataset.features["observation.state.head"]["shape"][0])

# Define features for the new dataset (same as above).
features = {
    'action': {'dtype': 'float32', "shape": (action_dim,), 'names': list(range(action_dim))}, 
    'observation.state': {'dtype': 'float32', "shape": (obs_dim,), 'names': list(range(obs_dim))}, 
    **raw_dataset.features
}

# Clear cache for the new dataset (same as above).
os.system(f"rm -rf ~/.cache/huggingface/lerobot/{repo_id}")

# Create a new LeRobotDataset (same as above).
dataset = LeRobotDataset.create(
    repo_id,
    raw_dataset.meta.fps,
    root=root,
    robot_type="astra_joint",
    features=features,
    use_videos=True,
)

# Define episode generator (same as above).
def get_episode():
    first = True
    rows = []
    for row in tqdm.tqdm(raw_dataset):
        if row["frame_index"] == 0 and not first:
            yield rows
            rows = []
        first = False
        rows.append(row)
    yield rows

# Process each episode:
for rows in get_episode():
    task = rows[0]["task"]  # Extract task from the first row.

    # Stack base actions and timestamps for the episode:
    # - action_base: Tensor of base actions for all frames.
    # - timestamps: Tensor of timestamps (not used further here but collected).
    action_base = torch.stack([row["action.base"] for row in rows])
    timestamps = torch.stack([row["timestamp"] for row in rows])

    # Convert base commands from velocities to positions:
    # - Computes cumulative sum along the time dimension (dim=0) to integrate velocities into positions.
    action_base_cumsum = torch.cumsum(action_base, dim=0)

    # Update each row with the cumulative base positions:
    for i in range(len(rows)):
        rows[i]["action.base"] = action_base_cumsum[i]

    # Process each row in the episode (similar to above):
    for row in rows:
        # Remove metadata keys:
        row.pop("episode_index")
        row.pop("task")
        row.pop("frame_index")
        row.pop("timestamp")
        row.pop("index")
        row.pop("task_index")
        row.pop("action")
        row.pop("observation.state")

        # Create a new frame with concatenated tensors:
        frame = {
            "action": torch.concatenate([
                row["action.arm_l"],
                row["action.gripper_l"].unsqueeze(-1),
                row["action.arm_r"],
                row["action.gripper_r"].unsqueeze(-1),
                row["action.base"],  # Now contains position data.
                row["action.head"],
            ]),
            "observation.state": torch.concatenate([
                row["observation.state.arm_l"],
                row["observation.state.gripper_l"].unsqueeze(-1),
                row["observation.state.arm_r"],
                row["observation.state.gripper_r"].unsqueeze(-1),
                row["observation.state.base"],
                row["observation.state.head"],
            ]),
            **row
        }
        
        # Add the frame to the dataset.
        dataset.add_frame(frame)

    # Save the episode with the task name.
    dataset.save_episode(task)

# Restore video features and copy videos (same as above).
dataset.meta.info["features"].update(raw_video_features)
dataset.meta.info["total_videos"] = raw_dataset.meta.info["total_videos"]
write_json(dataset.meta.info, dataset.meta.root / INFO_PATH)
os.system(f"cp -r {raw_dataset.root}/videos/ {dataset.root}/videos/")

# Finalize the dataset (same as above).
run_compute_stats = True
push_to_hub = True
tags = ["astra"]
private = False

if run_compute_stats:
    print("Computing dataset statistics")
dataset.consolidate(run_compute_stats)

if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)
    
"""
Key Features and Purpose
Purpose: Transforms base commands from velocities to positions, creating a new dataset suitable for position-based control policies.
Base Command Conversion: Uses torch.cumsum to integrate velocities into positions, a key modification for the Astra robot’s base actions.
No Smoothing: Focuses solely on conversion without additional data smoothing.
"""