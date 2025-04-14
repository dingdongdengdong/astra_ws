#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Visualize data of **all** frames of any episode of a dataset of type LeRobotDataset.

Note: The last frame of the episode doesn't always correspond to a final state.
That's because our datasets are composed of transition from state to state up to
the antepenultimate state associated to the ultimate action to arrive in the final state.
However, there might not be a transition from a final state to another state.

Note: This script aims to visualize the data used to train the neural networks.
~What you see is what you get~. When visualizing image modality, it is often expected to observe
lossy compression artifacts since these images have been decoded from compressed mp4 videos to
save disk space. The compression factor applied has been tuned to not affect success rate.

Examples:

- Visualize data stored on a local machine:
```
local$ python lerobot/scripts/visualize_dataset.py \
    --repo-id lerobot/pusht \
    --episode-index 0
```

- Visualize data stored on a distant machine with a local viewer:
```
distant$ python lerobot/scripts/visualize_dataset.py \
    --repo-id lerobot/pusht \
    --episode-index 0 \
    --save 1 \
    --output-dir path/to/directory

local$ scp distant:path/to/directory/lerobot_pusht_episode_0.rrd .
local$ rerun lerobot_pusht_episode_0.rrd
```

- Visualize data stored on a distant machine through streaming:
(You need to forward the websocket port to the distant machine, with
`ssh -L 9087:localhost:9087 username@remote-host`)
```
distant$ python lerobot/scripts/visualize_dataset.py \
    --repo-id lerobot/pusht \
    --episode-index 0 \
    --mode distant \
    --ws-port 9087

local$ rerun ws://localhost:9087
```

"""

import argparse
import gc
import logging
import time
from pathlib import Path
from typing import Iterator

import numpy as np
import rerun as rr
import torch
import torch.utils.data
import tqdm

from lerobot.common.datasets.lerobot_dataset import LeRobotDataset


class EpisodeSampler(torch.utils.data.Sampler):
    def __init__(self, dataset: LeRobotDataset, episode_index: int):
        from_idx = dataset.episode_data_index["from"][episode_index].item()
        to_idx = dataset.episode_data_index["to"][episode_index].item()
        self.frame_ids = range(from_idx, to_idx)

    def __iter__(self) -> Iterator:
        return iter(self.frame_ids)

    def __len__(self) -> int:
        return len(self.frame_ids)


def to_hwc_uint8_numpy(chw_float32_torch: torch.Tensor) -> np.ndarray:
    assert chw_float32_torch.dtype == torch.float32
    assert chw_float32_torch.ndim == 3
    c, h, w = chw_float32_torch.shape
    assert c < h and c < w, f"expect channel first images, but instead {chw_float32_torch.shape}"
    hwc_uint8_numpy = (chw_float32_torch * 255).type(torch.uint8).permute(1, 2, 0).numpy()
    return hwc_uint8_numpy


def visualize_dataset(
    dataset: LeRobotDataset,
    episode_index: int,
    batch_size: int = 32,
    num_workers: int = 0,
    mode: str = "local",
    web_port: int = 9090,
    ws_port: int = 9087,
    save: bool = False,
    output_dir: Path | None = None,
) -> Path | None:
    if save:
        assert (
            output_dir is not None
        ), "Set an output directory where to write .rrd files with `--output-dir path/to/directory`."

    repo_id = dataset.repo_id

    logging.info("Loading dataloader")
    episode_sampler = EpisodeSampler(dataset, episode_index)
    dataloader = torch.utils.data.DataLoader(
        dataset,
        num_workers=num_workers,
        batch_size=batch_size,
        sampler=episode_sampler,
    )

    logging.info("Starting Rerun")

    if mode not in ["local", "distant"]:
        raise ValueError(mode)

    spawn_local_viewer = mode == "local" and not save
    rr.init(f"{repo_id}/episode_{episode_index}", spawn=spawn_local_viewer)

    # Manually call python garbage collector after `rr.init` to avoid hanging in a blocking flush
    # when iterating on a dataloader with `num_workers` > 0
    # TODO(rcadene): remove `gc.collect` when rerun version 0.16 is out, which includes a fix
    gc.collect()

    if mode == "distant":
        rr.serve(open_browser=False, web_port=web_port, ws_port=ws_port)

    logging.info("Logging to Rerun")

    for batch in tqdm.tqdm(dataloader, total=len(dataloader)):
        # iterate over the batch
        for i in range(len(batch["index"])):
            rr.set_time_sequence("frame_index", batch["frame_index"][i].item())
            rr.set_time_seconds("timestamp", batch["timestamp"][i].item())

            # display each camera image
            for key in dataset.meta.camera_keys:
                # TODO(rcadene): add `.compress()`? is it lossless?
                rr.log(key, rr.Image(to_hwc_uint8_numpy(batch[key][i])))

            # display each dimension of action space (e.g. actuators command)
            if "action" in batch:
                for dim_idx, val in enumerate(batch["action"][i]):
                    rr.log(f"action/{dim_idx}", rr.Scalar(val.item()))

            # display each dimension of observed state space (e.g. agent position in joint space)
            if "observation.state" in batch:
                for dim_idx, val in enumerate(batch["observation.state"][i]):
                    rr.log(f"observation.state/{dim_idx}", rr.Scalar(val.item()))
            
            for key in batch:
                if "observation.state." in key or "action." in key:
                    if batch[key][i].ndim == 1:
                        for dim_idx, val in enumerate(batch[key][i]):
                            rr.log(f"{key}/{dim_idx}", rr.Scalar(val.item()))
                    else:
                        rr.log(key, rr.Scalar(batch[key][i].item()))

            if "next.done" in batch:
                rr.log("next.done", rr.Scalar(batch["next.done"][i].item()))

            if "next.reward" in batch:
                rr.log("next.reward", rr.Scalar(batch["next.reward"][i].item()))

            if "next.success" in batch:
                rr.log("next.success", rr.Scalar(batch["next.success"][i].item()))

    if mode == "local" and save:
        # save .rrd locally
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        repo_id_str = repo_id.replace("/", "_")
        rrd_path = output_dir / f"{repo_id_str}_episode_{episode_index}.rrd"
        rr.save(rrd_path)
        return rrd_path

    elif mode == "distant":
        # stop the process from exiting since it is serving the websocket connection
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Ctrl-C received. Exiting.")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo-id",
        type=str,
        required=True,
        help="Name of hugging face repository containing a LeRobotDataset dataset (e.g. `lerobot/pusht`).",
    )
    parser.add_argument(
        "--episode-index",
        type=int,
        required=True,
        help="Episode to visualize.",
    )
    parser.add_argument(
        "--local-files-only",
        type=int,
        default=0,
        help="Use local files only. By default, this script will try to fetch the dataset from the hub if it exists.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root directory for the dataset stored locally (e.g. `--root data`). By default, the dataset will be loaded from hugging face cache folder, or downloaded from the hub if available.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory path to write a .rrd file when `--save 1` is set.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size loaded by DataLoader.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=4,
        help="Number of processes of Dataloader for loading the data.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="local",
        help=(
            "Mode of viewing between 'local' or 'distant'. "
            "'local' requires data to be on a local machine. It spawns a viewer to visualize the data locally. "
            "'distant' creates a server on the distant machine where the data is stored. "
            "Visualize the data by connecting to the server with `rerun ws://localhost:PORT` on the local machine."
        ),
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=9090,
        help="Web port for rerun.io when `--mode distant` is set.",
    )
    parser.add_argument(
        "--ws-port",
        type=int,
        default=9087,
        help="Web socket port for rerun.io when `--mode distant` is set.",
    )
    parser.add_argument(
        "--save",
        type=int,
        default=0,
        help=(
            "Save a .rrd file in the directory provided by `--output-dir`. "
            "It also deactivates the spawning of a viewer. "
            "Visualize the data by running `rerun path/to/file.rrd` on your local machine."
        ),
    )

    args = parser.parse_args()
    kwargs = vars(args)
    repo_id = kwargs.pop("repo_id")
    root = kwargs.pop("root")
    local_files_only = kwargs.pop("local_files_only")

    logging.info("Loading dataset")
    dataset = LeRobotDataset(repo_id, root=root, local_files_only=local_files_only)

    visualize_dataset(dataset, **vars(args))


if __name__ == "__main__":
    main()




"""
#!/usr/bin/env python
# Shebang line to run the script as a Python executable.

# Copyright notice and Apache License 2.0 details:
# - Indicates the script is copyrighted by HuggingFace (2024).
# - Licensed under Apache 2.0, allowing use with specific conditions (see license for details).
# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Docstring explaining the script's purpose:
# - Visualizes all frames of an episode from a LeRobotDataset.
# - Notes that the last frame may not represent a final state due to dataset structure (transitions up to antepenultimate state).
# - Highlights that images may show compression artifacts due to mp4 encoding for disk efficiency.
# - Provides example commands for local visualization, saving to a file, and distant streaming.
"""
Visualize data of **all** frames of any episode of a dataset of type LeRobotDataset.
[... see original docstring for details and examples ...]
"""

# Import required libraries:
# - argparse: For parsing command-line arguments.
# - gc: For manual garbage collection to manage memory.
# - logging: For logging script progress and errors.
# - time: For handling timing in distant mode.
# - pathlib.Path: For cross-platform file path handling.
# - typing.Iterator: For type hinting iterator objects.
# - numpy: For array operations (image conversion).
# - rerun: Visualization library for displaying dataset data interactively.
# - torch: For tensor operations and data loading.
# - torch.utils.data: For DataLoader and Sampler utilities.
# - tqdm: For progress bars during iteration.
# - LeRobotDataset: Custom class for loading LeRobot datasets.
import argparse
import gc
import logging
import time
from pathlib import Path
from typing import Iterator
import numpy as np
import rerun as rr
import torch
import torch.utils.data
import tqdm
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

# Define a custom Sampler for selecting frames from a specific episode:
# - Ensures only frames from the chosen episode_index are loaded.
class EpisodeSampler(torch.utils.data.Sampler):
    def __init__(self, dataset: LeRobotDataset, episode_index: int):
        # Get the start and end indices for the episode:
        # - dataset.episode_data_index["from"] and ["to"] map episode indices to frame ranges.
        from_idx = dataset.episode_data_index["from"][episode_index].item()
        to_idx = dataset.episode_data_index["to"][episode_index].item()
        # Store the range of frame indices for this episode.
        self.frame_ids = range(from_idx, to_idx)

    def __iter__(self) -> Iterator:
        # Return an iterator over the frame indices.
        return iter(self.frame_ids)

    def __len__(self) -> int:
        # Return the number of frames in the episode.
        return len(self.frame_ids)

# Utility function to convert images from PyTorch to NumPy format:
# - Converts channel-first (C,H,W), float32 tensors to height-width-channel (H,W,C), uint8 NumPy arrays for visualization.
def to_hwc_uint8_numpy(chw_float32_torch: torch.Tensor) -> np.ndarray:
    # Ensure input is float32 and 3D (C,H,W).
    assert chw_float32_torch.dtype == torch.float32
    assert chw_float32_torch.ndim == 3
    c, h, w = chw_float32_torch.shape
    # Verify channel-first format (C < H, C < W).
    assert c < h and c < w, f"expect channel first images, but instead {chw_float32_torch.shape}"
    # Scale from [0,1] float to [0,255] uint8, permute to H,W,C, and convert to NumPy.
    hwc_uint8_numpy = (chw_float32_torch * 255).type(torch.uint8).permute(1, 2, 0).numpy()
    return hwc_uint8_numpy

# Main visualization function:
# - Loads and visualizes a specific episode using Rerun.
# - Supports local viewing, saving to a file, or distant streaming.
def visualize_dataset(
    dataset: LeRobotDataset,
    episode_index: int,
    batch_size: int = 32,
    num_workers: int = 0,
    mode: str = "local",
    web_port: int = 9090,
    ws_port: int = 9087,
    save: bool = False,
    output_dir: Path | None = None,
) -> Path | None:
    # Validate output_dir if saving is enabled:
    if save:
        assert output_dir is not None, "Set an output directory with `--output-dir path/to/directory`."

    # Store the dataset’s repo_id for naming outputs.
    repo_id = dataset.repo_id

    # Log progress for user feedback.
    logging.info("Loading dataloader")
    # Create a sampler to load only the specified episode’s frames.
    episode_sampler = EpisodeSampler(dataset, episode_index)
    # Set up a DataLoader for efficient batch loading:
    # - Uses the custom sampler, specified batch size, and number of workers for parallel loading.
    dataloader = torch.utils.data.DataLoader(
        dataset,
        num_workers=num_workers,
        batch_size=batch_size,
        sampler=episode_sampler,
    )

    # Initialize Rerun visualization:
    logging.info("Starting Rerun")
    # Validate visualization mode.
    if mode not in ["local", "distant"]:
        raise ValueError(mode)
    # Determine if a local viewer should be spawned (only for local mode, not saving).
    spawn_local_viewer = mode == "local" and not save
    # Initialize Rerun with a name based on repo_id and episode_index.
    rr.init(f"{repo_id}/episode_{episode_index}", spawn=spawn_local_viewer)

    # Manually collect garbage to prevent memory issues:
    # - Needed due to a known issue with Rerun and DataLoader workers (fixed in Rerun 0.16).
    gc.collect()

    # Set up distant mode if selected:
    # - Starts a server for streaming visualization data over WebSocket.
    if mode == "distant":
        rr.serve(open_browser=False, web_port=web_port, ws_port=ws_port)

    # Begin logging data to Rerun.
    logging.info("Logging to Rerun")

    # Iterate through batches with a progress bar:
    for batch in tqdm.tqdm(dataloader, total=len(dataloader)):
        # Process each frame in the batch:
        for i in range(len(batch["index"])):
            # Set the timeline for visualization:
            # - frame_index: The frame number within the episode.
            # - timestamp: The recorded time of the frame.
            rr.set_time_sequence("frame_index", batch["frame_index"][i].item())
            rr.set_time_seconds("timestamp", batch["timestamp"][i].item())

            # Log camera images:
            # - Iterates through all camera keys (e.g., observation.images.head).
            # - Converts images to HWC uint8 format and logs them as Rerun Image objects.
            for key in dataset.meta.camera_keys:
                rr.log(key, rr.Image(to_hwc_uint8_numpy(batch[key][i])))

            # Log action dimensions:
            # - If actions are present, logs each dimension as a scalar plot.
            if "action" in batch:
                for dim_idx, val in enumerate(batch["action"][i]):
                    rr.log(f"action/{dim_idx}", rr.Scalar(val.item()))

            # Log observation state dimensions:
            # - If states are present, logs each dimension as a scalar plot.
            if "observation.state" in batch:
                for dim_idx, val in enumerate(batch["observation.state"][i]):
                    rr.log(f"observation.state/{dim_idx}", rr.Scalar(val.item()))

            # Log additional state/action subfields:
            # - Handles keys like observation.state.arm_l or action.base.
            # - Logs vector fields as individual scalars or single scalar values.
            for key in batch:
                if "observation.state." in key or "action." in key:
                    if batch[key][i].ndim == 1:  # Vector field (e.g., arm_l with multiple dimensions).
                        for dim_idx, val in enumerate(batch[key][i]):
                            rr.log(f"{key}/{dim_idx}", rr.Scalar(val.item()))
                    else:  # Scalar field (e.g., gripper_l as a single value).
                        rr.log(key, rr.Scalar(batch[key][i].item()))

            # Log additional metadata if present:
            # - next.done: Indicates if the episode is complete.
            if "next.done" in batch:
                rr.log("next.done", rr.Scalar(batch["next.done"][i].item()))
            # - next.reward: Reward value for the transition.
            if "next.reward" in batch:
                rr.log("next.reward", rr.Scalar(batch["next.reward"][i].item()))
            # - next.success: Success indicator for the task.
            if "next.success" in batch:
                rr.log("next.success", rr.Scalar(batch["next.success"][i].item()))

    # Handle saving or distant mode:
    if mode == "local" and save:
        # Save the visualization as an .rrd file:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        # Create a filename based on repo_id and episode_index.
        repo_id_str = repo_id.replace("/", "_")
        rrd_path = output_dir / f"{repo_id_str}_episode_{episode_index}.rrd"
        rr.save(rrd_path)
        return rrd_path
    elif mode == "distant":
        # Keep the process running to maintain the WebSocket server:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Ctrl-C received. Exiting.")

# Main entry point:
def main():
    # Set up argument parser for command-line options:
    parser = argparse.ArgumentParser()
    # Required: Dataset repository ID (e.g., lerobot/pusht).
    parser.add_argument("--repo-id", type=str, required=True, help="Name of hugging face repository...")
    # Required: Episode index to visualize.
    parser.add_argument("--episode-index", type=int, required=True, help="Episode to visualize.")
    # Optional: Use local files only (default: 0, i.e., False).
    parser.add_argument("--local-files-only", type=int, default=0, help="Use local files only...")
    # Optional: Root directory for dataset (default: None, uses cache).
    parser.add_argument("--root", type=Path, default=None, help="Root directory for the dataset...")
    # Optional: Output directory for saving .rrd files.
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory path to write a .rrd file...")
    # Optional: Batch size for DataLoader (default: 32).
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size loaded by DataLoader.")
    # Optional: Number of DataLoader workers (default: 4).
    parser.add_argument("--num-workers", type=int, default=4, help="Number of processes of Dataloader...")
    # Optional: Visualization mode (local or distant, default: local).
    parser.add_argument("--mode", type=str, default="local", help="Mode of viewing between 'local' or 'distant'...")
    # Optional: Web port for distant mode (default: 9090).
    parser.add_argument("--web-port", type=int, default=9090, help="Web port for rerun.io when `--mode distant`...")
    # Optional: WebSocket port for distant mode (default: 9087).
    parser.add_argument("--ws-port", type=int, default=9087, help="Web socket port for rerun.io...")
    # Optional: Save .rrd file (default: 0, i.e., False).
    parser.add_argument("--save", type=int, default=0, help="Save a .rrd file in the directory...")

    # Parse arguments.
    args = parser.parse_args()
    kwargs = vars(args)
    # Extract key arguments for dataset loading.
    repo_id = kwargs.pop("repo_id")
    root = kwargs.pop("root")
    local_files_only = kwargs.pop("local_files_only")

    # Load the dataset:
    logging.info("Loading dataset")
    dataset = LeRobotDataset(repo_id, root=root, local_files_only=local_files_only)

    # Call the visualization function with parsed arguments.
    visualize_dataset(dataset, **vars(args))

# Standard Python entry point:
if __name__ == "__main__":
    main()
"""


"""
Detailed Explanation
Purpose
The script visualizes episodes from a LeRobotDataset, allowing users to inspect the data used for training robotic policies. It supports:

Local Visualization: Displays data interactively using a Rerun viewer on the same machine.
Saving to File: Saves visualization data as an .rrd file for later viewing.
Distant Streaming: Streams data to a remote viewer via WebSocket, useful for datasets on a remote server.
Data Types: Visualizes camera images, action dimensions, state dimensions, and metadata like done flags, rewards, or success indicators.
Key Features
Rerun Integration:
Uses Rerun (a visualization tool) to display time-series data, including images and scalar plots.
Supports timelines based on frame indices and timestamps for synchronized viewing.
Efficient Data Loading:
Uses a custom EpisodeSampler to load only the frames of the specified episode.
Employs PyTorch’s DataLoader for batched, parallel data loading.
Flexible Visualization Modes:
Local: Immediate visualization with an optional save to .rrd.
Distant: Streams data to a remote client, requiring port forwarding (e.g., via SSH).
Comprehensive Data Display:
Images: Converted to HWC uint8 format for display.
Actions/States: Plotted as scalar time-series for each dimension.
Metadata: Includes done, reward, and success signals if available.
Error Handling:
Validates inputs (e.g., mode, output_dir).
Manages memory with garbage collection to avoid issues with Rerun and DataLoader.
Workflow
Argument Parsing:
Collects user inputs like repo_id, episode_index, mode, and others.
Supports flexible configuration for different use cases.
Dataset Loading:
Loads the dataset using LeRobotDataset, respecting root and local_files_only.
DataLoader Setup:
Uses EpisodeSampler to restrict loading to the chosen episode.
Configures batch size and workers for efficient processing.
Visualization:
Initializes Rerun with the appropriate mode (local or distant).
Iterates through batches, logging images, actions, states, and metadata to Rerun.
Output Handling:
Saves .rrd files if requested or keeps the server running for distant mode.
Relation to Astra Robot
While the script is generic to LeRobotDataset, it’s applicable to Astra robot datasets (e.g., lookas/astra_grab_floor_toys). For such datasets, it would visualize:

Camera feeds (observation.images.head, wrist_left, wrist_right).
Actions (action.arm_l, action.base, etc.) as scalar plots.
States (observation.state.arm_l, etc.) similarly.
Metadata like task completion (next.done) or success (next.success).
Notable Details
Compression Artifacts: The docstring warns about potential image artifacts due to mp4 compression, tuned to not impact training performance.
Garbage Collection: Includes a workaround (gc.collect) for a Rerun issue with DataLoader workers, noted to be fixed in Rerun 0.16.
Distant Mode: Requires manual port forwarding for streaming, making it suitable for remote servers but needing network setup.
Summary
The visualize_dataset.py script is a powerful tool for inspecting LeRobotDataset episodes, offering flexible visualization options (local, saved, distant) and comprehensive data display (images, actions, states, metadata). It’s designed for debugging and understanding datasets, crucial for robotic tasks like those involving the Astra robot. The use of Rerun ensures interactive, time-synchronized visualization, while the script’s modularity supports various deployment scenarios.
"""