from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

repo_id = "lookas/astra_grab_floor_toys"

root = None
local_files_only = True

dataset = LeRobotDataset(
    repo_id,
    root=root,
    local_files_only=local_files_only,
)

push_to_hub = True
tags = ["astra"]
private = False

if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)