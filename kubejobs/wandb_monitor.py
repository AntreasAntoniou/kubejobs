import json
import os
import time

import wandb

# Path to the metadata JSON file
metadata_path = os.getenv("WANDB_METADATA_PATH")

# Load metadata from the specified JSON file
metadata = {}
if metadata_path:
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {metadata_path}: {e}")
        metadata = {}

# Initialize the W&B run with metadata
wandb.init(
    project=os.getenv("WANDB_PROJECT"),
    entity=os.getenv("WANDB_ENTITY"),
    name=os.getenv("POD_NAME"),
    config=metadata,
)

# Run an infinite loop that logs a heartbeat every 10 seconds
while True:
    wandb.log({"heartbeat": 1})
    time.sleep(10)
