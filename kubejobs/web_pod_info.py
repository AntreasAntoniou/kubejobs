import json
import subprocess
import time
from datetime import datetime, timezone

import fire
import numpy as np
import pandas as pd
import rich
import streamlit as st
from tqdm import tqdm


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


def run_command(command: str) -> str:
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
    loop=True,
    refresh_interval=60,
    samples_per_gpu=3,
):
    """
    Fetches information about Kubernetes pods and renders it in a Streamlit table.

    Args:
    - namespace (str): The Kubernetes namespace to fetch pod information from. Default is "informatics".
    - loop (bool): Whether to continuously refresh the pod information and update the table. Default is True.
    - refresh_interval (int): The number of seconds to wait between each refresh of the pod information. Default is 60.
    - samples_per_gpu (int): The number of samples to take when measuring GPU utilization. Default is 3.
    """
    # Outside of your loop, before you start refreshing data
    st_table = st.empty()

    while True:
        get_pods_cmd = f"kubectl get pods -n {namespace} -o json"
        pods_output, _ = run_command(get_pods_cmd)
        pod_data = json.loads(pods_output)

        columns = [
            "Name",
            "Namespace",
            "Username",
            "UID",
            "Status",
            "Node",
            "Image",
            "CPU Request",
            "Memory Request",
            "GPU Type",
            "GPU Limit",
            "GPU Memory Used",
            "GPU Memory Total",
            "GPU Utilization",
            "Creation Time",
            "Age",
        ]
        data = []

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
            gpu_memory_total_list = []
            gpu_memory_used_list = []
            gpu_utilization_list = []

            for _ in range(samples_per_gpu):
                gpu_usage_output = ssh_into_pod_and_run_command(
                    name,
                    namespace,
                    "nvidia-smi --query-gpu=memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits",
                )

                for line in gpu_usage_output.splitlines():
                    (
                        gpu_memory_total,
                        gpu_memory_used,
                        gpu_utilization,
                    ) = line.split(",")
                    gpu_memory_total_list.append(float(gpu_memory_total))
                    gpu_memory_used_list.append(float(gpu_memory_used))
                    gpu_utilization_list.append(float(gpu_utilization))

            gpu_memory_total = (
                np.mean(gpu_memory_total_list)
                if len(gpu_memory_total_list) > 0
                else -1
            )
            gpu_memory_used = (
                np.mean(gpu_memory_used_list)
                if len(gpu_memory_used_list) > 0
                else -1
            )
            gpu_utilization = (
                np.mean(gpu_utilization_list)
                if len(gpu_utilization_list) > 0
                else -1
            )

            data.append(
                [
                    str(name),
                    str(namespace),
                    str(username),
                    str(uid),
                    pod_status,
                    node,
                    image,
                    int(cpu_request),
                    convert_to_gigabytes(memory_request),
                    gpu_type,
                    int(gpu_limit),
                    gpu_memory_used,
                    gpu_memory_total,
                    gpu_utilization,
                    str(creation_time),
                    age,
                ]
            )

        df = pd.DataFrame(data, columns=columns)
        # Inside your loop, when you update the DataFrame
        st_table.dataframe(
            df
        )  # This will update the existing table instead of creating a new one

        if not loop:
            break
        time.sleep(
            refresh_interval
        )  # Refresh every specified number of seconds


if __name__ == "__main__":
    fire.Fire(fetch_and_render_pod_info)
