import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone

import fire
import numpy as np
import pandas as pd
import rich
import wandb
from tqdm.auto import tqdm


def convert_to_gigabytes(value: str) -> float:
    """
    Convert the given storage/memory value to base Gigabytes (GB).

    Args:
        value (str): Input storage/memory value with units. E.g., '20G', '20Gi', '2000M', '2000Mi'

    Returns:
        float: The value converted to Gigabytes (GB).
    """
    # Define conversion factors
    factor_gb = {
        "G": 1,
        "Gi": 1 / 1.073741824,
        "M": 1 / 1024,
        "Mi": 1 / (1024 * 1.073741824),
    }

    # Find the numeric and unit parts of the input
    numeric_part = "".join(filter(str.isdigit, value))
    unit_part = "".join(filter(str.isalpha, value))

    # Convert to Gigabytes (GB)
    if unit_part in factor_gb.keys():
        return float(numeric_part) * factor_gb[unit_part]
    elif value == "N/A":
        return -1
    else:
        raise ValueError(
            f"Unknown unit {unit_part}. Supported units are {list(factor_gb.keys())}."
        )


def parse_iso_time(time_str: str) -> datetime:
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def time_diff_to_human_readable(start: datetime, end: datetime) -> str:
    diff = end - start
    minutes, seconds = divmod(diff.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{diff.days}d {hours}h {minutes}m {seconds}s"


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


def fetch_and_render_pod_info(
    namespace="informatics",
    refresh_interval=10,
    wandb_project="gpu_monitoring",
):
    wandb.login()

    runs = {}  # Store the wandb runs

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
            uid = metadata["uid"]

            username = metadata.get("annotations", {}).get("username", "N/A")

            pod_status = status["phase"]
            node = spec.get("nodeName", "N/A")

            container = spec.get("containers", [{}])[0]
            image = container.get("image", "N/A")

            resources = container.get("resources", {})
            cpu_request = resources.get("requests", {}).get("cpu", "0")
            memory_request = resources.get("requests", {}).get("memory", "N/A")
            gpu_type = spec.get("nodeSelector", {}).get(
                "nvidia.com/gpu.product", "N/A"
            )
            gpu_limit = resources.get("limits", {}).get("nvidia.com/gpu", "0")

            creation_time = parse_iso_time(metadata["creationTimestamp"])
            age = time_diff_to_human_readable(creation_time, current_time)

            # SSH into the pod and get GPU utilization details
            gpu_usage_output = ssh_into_pod_and_run_command(
                name,
                namespace,
                "nvidia-smi --query-gpu=memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits",
            )

            # Process the GPU data and log it to wandb
            lines = gpu_usage_output.splitlines()
            for line in lines:
                gpu_memory_total, gpu_memory_used, gpu_utilization = map(
                    float, line.split(", ")
                )

                # Initialize a new wandb run if we haven't seen this pod before
                if name not in runs:
                    runs[name] = wandb.init(
                        project=wandb_project, name=name, reinit=True
                    )

                # Log the GPU data to wandb
                runs[name].log(
                    {
                        "GPU Memory Total (GB)": gpu_memory_total,
                        "GPU Memory Used (GB)": gpu_memory_used,
                        "GPU Utilization (%)": gpu_utilization,
                    }
                )

        time.sleep(refresh_interval)

    # Finish all wandb runs when exiting the loop
    for run in runs.values():
        run.finish()


if __name__ == "__main__":
    fire.Fire(fetch_and_render_pod_info)
