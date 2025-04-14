# %%
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import tqdm
import os

raw_repo_id = "lookas/astra_grab_floor_toys_without_observations_actions"
repo_id = "lookas/astra_grab_floor_toys"

root = None
local_files_only = True

raw_dataset = LeRobotDataset(
    raw_repo_id,
    root=root,
    local_files_only=local_files_only,
)

# %%
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

features = {
    'action': {'dtype': 'float32', "shape": (action_dim,), 'names': list(range(action_dim))}, 
    'observation.state': {'dtype': 'float32', "shape": (obs_dim,), 'names': list(range(obs_dim))}, 
    **raw_dataset.features
}

# %%
os.system(f"rm -rf ~/.cache/huggingface/lerobot/{repo_id}")

# Create empty dataset or load existing saved episodes
dataset = LeRobotDataset.create(
    repo_id,
    raw_dataset.meta.fps,
    root=root,
    robot_type="astra_joint",
    features=features,
    use_videos=True,
    image_writer_threads=4 * 3,
)

# %%
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

# %%
for rows in get_episode():
    task = rows[0]["task"]

    rows = rows[5:] # remove empty state

    for row in rows:
        row.pop("episode_index")
        row.pop("task")
        row.pop("frame_index")
        row.pop("timestamp")
        row.pop("index")
        row.pop("task_index")
        row.pop("action")
        row.pop("observation.state")
        
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
        
        dataset.add_frame(frame)
    
    del rows

    dataset.save_episode(task)

# %%
run_compute_stats = True
push_to_hub = True
tags = ["astra"]
private = False

if run_compute_stats:
    print("Computing dataset statistics")

dataset.consolidate(run_compute_stats)

if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)
