# %%
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import tqdm
import os
from lerobot.common.datasets.utils import write_json, INFO_PATH

raw_repo_id = "lookas/astra_grab_floor_toys"
repo_id = raw_repo_id + "_with_joint_space"

root = None
local_files_only = True

raw_dataset = LeRobotDataset(
    raw_repo_id,
    root=root,
    local_files_only=local_files_only,
)

# temporary remove video_keys for faster reading and writing
raw_video_features = {
    "observation.images.head": raw_dataset.meta.info["features"].pop("observation.images.head"),
    "observation.images.wrist_left": raw_dataset.meta.info["features"].pop("observation.images.wrist_left"),
    "observation.images.wrist_right": raw_dataset.meta.info["features"].pop("observation.images.wrist_right"),
}
assert len(raw_dataset.meta.video_keys) == 0

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

    dataset.save_episode(task)

# %%
dataset.meta.info["features"].update(raw_video_features)

dataset.meta.info["total_videos"] = raw_dataset.meta.info["total_videos"]
write_json(dataset.meta.info, dataset.meta.root / INFO_PATH)

os.system(f"cp -r {raw_dataset.root}/videos/ {dataset.root}/videos/")

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
