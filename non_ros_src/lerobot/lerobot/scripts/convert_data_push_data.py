# Import LeRobotDataset class.
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

# Define dataset identifier.
repo_id = "lookas/astra_grab_floor_toys"

# Dataset configuration.
root = None
local_files_only = True

# Load the dataset.
dataset = LeRobotDataset(
    repo_id,
    root=root,
    local_files_only=local_files_only,
)

# Configuration for pushing to hub.
push_to_hub = True
tags = ["astra"]
private = False

# Push dataset to hub with specified tags and visibility.
if push_to_hub:
    dataset.push_to_hub(tags=tags, private=private)