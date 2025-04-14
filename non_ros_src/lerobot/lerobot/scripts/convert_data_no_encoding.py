# Import required libraries:
# - torch: For tensor operations (e.g., concatenation, stacking).
# - LeRobotDataset: Custom class from LeRobot for managing robotic datasets.
# - tqdm: Adds progress bars for iteration visibility.
# - os: For file system operations (e.g., removing cache, copying videos).
# - write_json, INFO_PATH: Utilities to save dataset metadata as JSON.
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import tqdm
import os
from lerobot.common.datasets.utils import write_json, INFO_PATH

# Define dataset identifiers:
# - raw_repo_id: Source dataset ID from which data is loaded.
# - repo_id: New dataset ID, appending "_with_joint_space" to indicate joint space data inclusion.
raw_repo_id = "lookas/astra_grab_floor_toys"
repo_id = raw_repo_id + "_with_joint_space"

# Dataset configuration:
# - root: Set to None, using the default cache directory (~/.cache/huggingface/lerobot).
# - local_files_only: True ensures data is loaded locally, avoiding online downloads.
root = None
local_files_only = True

# Load the raw dataset:
# - Uses LeRobotDataset to access the source dataset with specified repo_id and settings.
# - Contains metadata (e.g., fps), features (e.g., state shapes), and data (e.g., actions, observations).
raw_dataset = LeRobotDataset(
    raw_repo_id,
    root=root,
    local_files_only=local_files_only,
)

# Temporarily remove video features for efficiency:
# - Store video features (head, wrist_left, wrist_right cameras) in a dictionary.
# - Remove them from raw_dataset.meta.info["features"] to speed up data processing.
# - Assert no video keys remain in meta.video_keys to confirm removal.
raw_video_features = {
    "observation.images.head": raw_dataset.meta.info["features"].pop("observation.images.head"),
    "observation.images.wrist_left": raw_dataset.meta.info["features"].pop("observation.images.wrist_left"),
    "observation.images.wrist_right": raw_dataset.meta.info["features"].pop("observation.images.wrist_right"),
}
assert len(raw_dataset.meta.video_keys) == 0

# Calculate dimensions for actions and observations:
# - action_dim: Size of the action vector, summing shapes of arm, gripper, base, and head components for both left and right.
# - obs_dim: Size of the observation state vector, calculated similarly.
# - Dynamically computed from feature shapes in the raw dataset.
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
# - 'action': A float32 tensor of shape (action_dim,), with names as indices (0 to action_dim-1).
# - 'observation.state': A float32 tensor of shape (obs_dim,), with similar naming.
# - Include all other features from raw_dataset to preserve additional data (e.g., images).
features = {
    'action': {'dtype': 'float32', "shape": (action_dim,), 'names': list(range(action_dim))}, 
    'observation.state': {'dtype': 'float32', "shape": (obs_dim,), 'names': list(range(obs_dim))}, 
    **raw_dataset.features
}

# Clear cache for the new dataset:
# - Removes the cache directory for repo_id to ensure a fresh dataset creation.
os.system(f"rm -rf ~/.cache/huggingface/lerobot/{repo_id}")

# Create a new LeRobotDataset:
# - repo_id: Unique ID for the new dataset.
# - fps: Inherited from raw_dataset for consistency in frame timing.
# - root: Default cache directory.
# - robot_type: "astra_joint" specifies the Astra robot with joint space data.
# - features: Custom features defined above.
# - use_videos: True to include video data (though not encoded yet).
dataset = LeRobotDataset.create(
    repo_id,
    raw_dataset.meta.fps,
    root=root,
    robot_type="astra_joint",
    features=features,
    use_videos=True,
)

# Define a generator for episodes:
# - Groups rows into episodes based on frame_index == 0 (new episode start).
# - Uses tqdm for a progress bar during iteration.
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
# - Iterates through episodes using the generator.
for rows in get_episode():
    task = rows[0]["task"]  # Extract task description from the first row.

    # Process each row in the episode:
    for row in rows:
        # Remove unnecessary metadata keys to simplify the frame structure:
        row.pop("episode_index")
        row.pop("task")
        row.pop("frame_index")
        row.pop("timestamp")
        row.pop("index")
        row.pop("task_index")
        row.pop("action")  # Remove original action to replace with concatenated version.
        row.pop("observation.state")  # Remove original state for the same reason.

        # Create a new frame with concatenated action and observation tensors:
        frame = {
            "action": torch.concatenate([
                row["action.arm_l"],               # Left arm actions.
                row["action.gripper_l"].unsqueeze(-1),  # Left gripper (add dimension for concatenation).
                row["action.arm_r"],               # Right arm actions.
                row["action.gripper_r"].unsqueeze(-1),  # Right gripper.
                row["action.base"],                # Base actions.
                row["action.head"],                # Head actions.
            ]),
            "observation.state": torch.concatenate([
                row["observation.state.arm_l"],    # Left arm state.
                row["observation.state.gripper_l"].unsqueeze(-1),  # Left gripper state.
                row["observation.state.arm_r"],    # Right arm state.
                row["observation.state.gripper_r"].unsqueeze(-1),  # Right gripper state.
                row["observation.state.base"],     # Base state.
                row["observation.state.head"],     # Head state.
            ]),
            **row  # Include remaining row data (e.g., images).
        }
        
        # Add the processed frame to the new dataset.
        dataset.add_frame(frame)

    # Save the episode with the task name, without encoding videos yet.
    dataset.save_episode(task)

# Restore video features to metadata:
# - Re-adds the previously removed video features.
# - Updates total_videos count from the raw dataset.
# - Writes the updated metadata to a JSON file at INFO_PATH.
dataset.meta.info["features"].update(raw_video_features)
dataset.meta.info["total_videos"] = raw_dataset.meta.info["total_videos"]
write_json(dataset.meta.info, dataset.meta.root / INFO_PATH)

# Copy video files from the raw dataset to the new dataset’s directory.
os.system(f"cp -r {raw_dataset.root}/videos/ {dataset.root}/videos/")

# Finalize the dataset:
# - run_compute_stats: If True, computes statistics (e.g., means, stds) for the dataset.
# - push_to_hub: If True, uploads the dataset to a hub (likely Hugging Face).
# - tags: Labels the dataset with "astra".
# - private: False makes the dataset publicly accessible.
run_compute_stats = True
push_to_hub = True
tags = ["astra"]
private = False

if run_compute_stats:
    print("Computing dataset statistics")
dataset.consolidate(run_compute_stats)  # Consolidates data and computes stats if enabled.

if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)  # Uploads to the hub with specified settings.

"""
Purpose: Converts a raw dataset into a new format with joint space data, delaying video encoding for efficiency.
No Video Encoding: Uses encode_videos=False implicitly (default behavior here) to save episodes without encoding videos immediately, deferring it to consolidate.
Joint Space: The "_with_joint_space" suffix suggests a focus on joint space representation, though no explicit transformation beyond concatenation is applied.
"""