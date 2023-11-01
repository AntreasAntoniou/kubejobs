import json
import os
import subprocess
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone

import fire
import numpy as np
import pandas as pd
import rich
from tqdm.auto import tqdm


def run_command(command: str) -> (str, str):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )
    return result.stdout, result.stderr


def ssh_into_pod_and_run_command(
    pod_name: str, namespace: str, command: str
) -> str:
    ssh_command = f"kubectl exec -n {namespace} {pod_name} -- {command}"
    stdout, stderr = run_command(ssh_command)
    if stderr:
        print(f"Error executing command in pod {pod_name}: {stderr}")
    return stdout


def create_and_copy_wandb_script(pod_name, namespace, metadata):
    # Convert the metadata dictionary to a JSON string
    metadata_json = json.dumps(metadata)
    metadata_filename = f"/tmp/wandb_metadata_{pod_name}.json"

    # Create the metadata JSON file locally
    with open(metadata_filename, "w") as f:
        json.dump(metadata, f)

    # Copy the metadata JSON file to the pod
    copy_metadata_command = [
        "kubectl",
        "cp",
        metadata_filename,
        f"{namespace}/{pod_name}:{metadata_filename}",
    ]
    subprocess.run(copy_metadata_command, check=True)

    # Copy the script to the pod
    copy_script_command = [
        "kubectl",
        "cp",
        "kubejobs/wandb_monitor.py",
        f"{namespace}/{pod_name}:/tmp/wandb_monitor.py",
    ]
    subprocess.run(copy_script_command, check=True)

    # Define the command to install wandb and start the monitoring script
    exec_command = (
        f"pip install wandb && "
        f"export WANDB_API_KEY='{os.getenv('WANDB_API_KEY')}' && "
        f"export WANDB_ENTITY='{os.getenv('WANDB_ENTITY')}' && "
        f"export WANDB_PROJECT='{os.getenv('WANDB_PROJECT')}' && "
        f"export POD_NAME='{pod_name}' && "
        f"export WANDB_METADATA_PATH='{metadata_filename}' && "
        f"python /tmp/wandb_monitor.py"
    )

    # Execute the command inside the pod
    exec_command_full = [
        "kubectl",
        "exec",
        "-n",
        namespace,
        pod_name,
        "--",
        "/bin/bash",
        "-c",
        exec_command,
    ]
    subprocess.Popen(
        exec_command_full,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def fetch_and_render_pod_info(
    namespace="informatics",
    refresh_interval=10,
    infinite_loop=True,
):
    name_set = set()
    while True:
        get_pods_cmd = f"kubectl get pods -n {namespace} -o json"
        pods_output, pods_error = run_command(get_pods_cmd)
        pod_data = json.loads(pods_output)

        current_time = datetime.now(timezone.utc)

        for pod in tqdm(pod_data["items"]):
            metadata = pod["metadata"]
            spec = pod.get("spec", {})
            status = pod["status"]

            name = metadata["name"]
            namespace = metadata["namespace"]
            if name in name_set:
                continue
            name_set.add(name)

            try:
                create_and_copy_wandb_script(name, namespace, pod)
            except Exception as e:
                print(f"Error on {pod}, {e}")
        time.sleep(refresh_interval)


if __name__ == "__main__":
    fire.Fire(fetch_and_render_pod_info)
