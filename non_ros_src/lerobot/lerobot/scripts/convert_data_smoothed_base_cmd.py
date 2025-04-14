# Import required libraries:
# - torch: For tensor operations.
# - LeRobotDataset: Custom class for handling robotic datasets.
# - tqdm: For progress bars during iteration.
# - os: For file system operations.
# - scipy.signal: For signal processing (smoothing).
# - matplotlib.pyplot: For plotting (commented out, likely for debugging).
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import tqdm
import os
from lerobot.common.datasets.utils import write_json, INFO_PATH
import scipy.signal
import matplotlib.pyplot as plt

# Define dataset identifiers:
# - raw_repo_id: Source dataset ID.
# - repo_id: New dataset ID with "_smoothed_base_cmd" appended to indicate smoothed base commands.
raw_repo_id = "lookas/astra_grab_floor_toys_extended"
repo_id = raw_repo_id + "_smoothed_base_cmd"

# Dataset configuration:
# - root: None means default cache directory is used (likely ~/.cache/huggingface/lerobot).
# - local_files_only: Ensures data is loaded from local cache, avoiding downloads.
root = None
local_files_only = True

# Load the raw dataset using LeRobotDataset:
# - Initializes with raw_repo_id, root, and local_files_only.
# - Contains metadata, features, and data for robot states, actions, and images.
raw_dataset = LeRobotDataset(
    raw_repo_id,
    root=root,
    local_files_only=local_files_only,
)

# Temporarily remove video-related features to speed up data processing:
# - Store video features (head, wrist_left, wrist_right cameras) in raw_video_features.
# - Pop them from raw_dataset.meta.info["features"] to exclude from immediate processing.
# - Assert that no video keys remain in meta.video_keys for efficiency.
raw_video_features = {
    "observation.images.head": raw_dataset.meta.info["features"].pop("observation.images.head"),
    "observation.images.wrist_left": raw_dataset.meta.info["features"].pop("observation.images.wrist_left"),
    "observation.images.wrist_right": raw_dataset.meta.info["features"].pop("observation.images.wrist_right"),
}
assert len(raw_dataset.meta.video_keys) == 0

# Calculate dimensions for actions and observations:
# - action_dim: Total size of action vector (concatenation of arm, gripper, base, head for left and right).
# - obs_dim: Total size of observation state vector (same components as action).
# - Uses feature shapes from raw_dataset to compute dimensions dynamically.
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

# Define features for the new dataset:
# - action: Float32 tensor of shape (action_dim,), with numbered names (0 to action_dim-1).
# - observation.state: Float32 tensor of shape (obs_dim,), with numbered names.
# - Include all features from raw_dataset to preserve other data (e.g., images).
features = {
    'action': {'dtype': 'float32', "shape": (action_dim,), 'names': list(range(action_dim))}, 
    'observation.state': {'dtype': 'float32', "shape": (obs_dim,), 'names': list(range(obs_dim))}, 
    **raw_dataset.features
}

# Clear cache for the new dataset to ensure a fresh start:
# - Deletes the cache directory for repo_id to avoid conflicts with prior runs.
os.system(f"rm -rf ~/.cache/huggingface/lerobot/{repo_id}")

# Create a new LeRobotDataset:
# - repo_id: Unique identifier for the new dataset.
# - fps: Copied from raw_dataset for consistency.
# - root: Uses default cache directory.
# - robot_type: Set to "astra_joint" (specific to the Astra robot).
# - features: Defined above, including action and observation dimensions.
# - use_videos: True to include video data in the dataset.
dataset = LeRobotDataset.create(
    repo_id,
    raw_dataset.meta.fps,
    root=root,
    robot_type="astra_joint",
    features=features,
    use_videos=True,
)

# Define a generator to yield episodes:
# - Iterates through raw_dataset with a progress bar (tqdm).
# - Groups rows into episodes based on frame_index == 0 (start of a new episode).
# - Yields each episode as a list of rows.
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
# - Iterates through episodes using get_episode().
for rows in get_episode():
    # Extract task name from the first row of the episode.
    task = rows[0]["task"]
    
    # Stack base actions and timestamps for all rows in the episode:
    # - action.base: Likely a 2D tensor (e.g., [x, y] for base movement).
    # - timestamps: Time data for each frame.
    action_base = torch.stack([row["action.base"] for row in rows])
    timestamps = torch.stack([row["timestamp"] for row in rows])

    # Smooth base actions:
    # - Compute cumulative sum of action_base to transform velocities to positions.
    # - Apply Savitzky-Golay filter (window=100, polyorder=0) to smooth each dimension (x, y).
    # - Convert smoothed cumulative sum back to velocities by computing differences.
    action_base_cumsum = torch.cumsum(action_base, dim=0)
    action_base_cumsum_smoothed = torch.tensor([
        scipy.signal.savgol_filter(action_base_cumsum[:, 0].numpy(), 100, 0),
        scipy.signal.savgol_filter(action_base_cumsum[:, 1].numpy(), 100, 0)
    ]).permute(1, 0)
    action_base_smoothed = torch.diff(action_base_cumsum_smoothed, dim=0, prepend=torch.zeros(1, 2))

    # Update each row with smoothed base actions.
    for i in range(len(rows)):
        rows[i]["action.base"] = action_base_smoothed[i]

    # Commented-out plotting code (for debugging):
    # - Would visualize raw vs. smoothed base actions and their cumulative sums.
    # - Saves plots to PDF files (e.g., "smoothed_action_base_0.pdf").
    # fig, ax = plt.subplots()
    # ax.plot(action_base[:, 0])
    # ax.plot(action_base[:, 1])
    # ...

    # Process each row in the episode:
    for row in rows:
        # Remove unnecessary fields to streamline data.
        row.pop("episode_index")
        row.pop("task")
        row.pop("frame_index")
        row.pop("timestamp")
        row.pop("index")
        row.pop("task_index")
        row.pop("action")
        row.pop("observation.state")
        
        # Create a new frame dictionary:
        # - action: Concatenated tensor of arm, gripper, base, and head actions.
        # - observation.state: Concatenated tensor of corresponding states.
        # - Include remaining row data (e.g., images).
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
        
        # Add the frame to the new dataset.
        dataset.add_frame(frame)

    # Save the episode with the associated task name.
    dataset.save_episode(task)

# Restore video features to the dataset’s metadata:
# - Re-adds the video features removed earlier.
# - Updates total_videos count from raw_dataset.
# - Writes updated metadata to a JSON file.
dataset.meta.info["features"].update(raw_video_features)
dataset.meta.info["total_videos"] = raw_dataset.meta.info["total_videos"]
write_json(dataset.meta.info, dataset.meta.root / INFO_PATH)

# Copy video files from raw_dataset to the new dataset’s directory.
os.system(f"cp -r {raw_dataset.root}/videos/ {dataset.root}/videos/")

# Finalize the dataset:
# - run_compute_stats: If True, computes dataset statistics (e.g., means, stds).
# - push_to_hub: If True, uploads the dataset to the hub (likely Hugging Face).
# - tags: Labels the dataset with "astra".
# - private: False means the dataset is publicly accessible.
run_compute_stats = True
push_to_hub = True
tags = ["astra"]
private = False

if run_compute_stats:
    print("Computing dataset statistics")
dataset.consolidate(run_compute_stats)

if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)