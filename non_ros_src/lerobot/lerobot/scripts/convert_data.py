# Import required libraries (same as above, minus smoothing and plotting tools).
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import tqdm
import os

# Define dataset identifiers:
# - raw_repo_id: Source dataset without observations/actions.
# - repo_id: New processed dataset ID.
raw_repo_id = "lookas/astra_grab_floor_toys_without_observations_actions"
repo_id = "lookas/astra_grab_floor_toys"

# Dataset configuration (same as above).
root = None
local_files_only = True

# Load the raw dataset.
raw_dataset = LeRobotDataset(
    raw_repo_id,
    root=root,
    local_files_only=local_files_only,
)

# Calculate action and observation dimensions (identical to convert_data_smoothed_base_cmd.py).
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

# Clear cache for the new dataset.
os.system(f"rm -rf ~/.cache/huggingface/lerobot/{repo_id}")

# Create a new LeRobotDataset:
# - Adds image_writer_threads=4*3 to optimize video writing (not present in first script).
dataset = LeRobotDataset.create(
    repo_id,
    raw_dataset.meta.fps,
    root=root,
    robot_type="astra_joint",
    features=features,
    use_videos=True,
    image_writer_threads=4 * 3,
)

# Define episode generator (identical to first script).
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
    # Extract task name.
    task = rows[0]["task"]

    # Skip first 5 rows (likely empty or invalid states).
    rows = rows[5:]

    # Process each row:
    for row in rows:
        # Remove unnecessary fields (same as first script).
        row.pop("episode_index")
        row.pop("task")
        row.pop("frame_index")
        row.pop("timestamp")
        row.pop("index")
        row.pop("task_index")
        row.pop("action")
        row.pop("observation.state")
        
        # Create a frame with concatenated action and observation tensors (same as first script).
        frame = {
            "action": torch.concatenate([
                row["action.arm_l"],
                row["action.gripper_l"].unsqueeze(-1),
                row["action.arm_r"],
                row["action.gripper_r"].unsqueeze(-1),
                row["action.base"],
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
        
        # Add frame to dataset.
        dataset.add_frame(frame)
    
    # Delete rows to free memory.
    del rows

    # Save episode with task name.
    dataset.save_episode(task)

# Finalize dataset (same as first script).
run_compute_stats = True
push_to_hub = True
tags = ["astra"]
private = False

if run_compute_stats:
    print("Computing dataset statistics")
dataset.consolidate(run_compute_stats)

if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)