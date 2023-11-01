import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone

import fire
import numpy as np
import pandas as pd
import rich
import streamlit as st
from tqdm import tqdm


def exponential_moving_average_efficient(data, N):
    """
    Compute the Exponential Moving Average (EMA) for a list of values.

    Args:
        data (list): The list of data points.
        span (int): The span N for the EMA calculation.

    Returns:
        float: The EMA of the data.
    """
    # Convert list to numpy array for vectorized operations
    data_array = np.array(data)

    # Calculate the smoothing factor alpha
    alpha = 2 / (N + 1)

    # Initialize the EMA array
    ema = np.zeros_like(data_array)
    ema[0] = data_array[0]

    # Calculate the EMA
    for i in range(1, len(data_array)):
        ema[i] = (alpha * data_array[i]) + ((1 - alpha) * ema[i - 1])

    return ema[-1]


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
        return -1


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
    refresh_interval=0,
    samples_per_gpu=1,
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
        "GPU Count Actual",
        "Creation Time",
        "Age",
    ]

    per_user_total_gpu_memory = defaultdict(list)
    per_user_total_gpu_utilization = defaultdict(list)
    per_user_total_gpu_memory_used = defaultdict(list)

    while True:
        get_pods_cmd = f"kubectl get pods -n {namespace} -o json"
        pods_output, _ = run_command(get_pods_cmd)
        pod_data = json.loads(pods_output)

        current_time = datetime.now(timezone.utc)
        data = []

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
            gpu_count_actual = 0
            for _ in range(samples_per_gpu):
                gpu_usage_output = ssh_into_pod_and_run_command(
                    name,
                    namespace,
                    "nvidia-smi --query-gpu=memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits",
                )
                lines = gpu_usage_output.splitlines()
                gpu_count_actual = len(lines)
                for line in lines:
                    (
                        gpu_memory_total,
                        gpu_memory_used,
                        gpu_utilization,
                    ) = line.split(",")

                    per_user_total_gpu_memory[username].append(
                        float(gpu_memory_total)
                    )
                    per_user_total_gpu_memory_used[username].append(
                        float(gpu_memory_used)
                    )
                    per_user_total_gpu_utilization[username].append(
                        float(gpu_utilization)
                    )

            gpu_memory_total = (
                exponential_moving_average_efficient(
                    data=per_user_total_gpu_memory[username],
                    N=min(25, len(per_user_total_gpu_memory[username])),
                )
                if len(per_user_total_gpu_memory[username]) > 0
                else -1
            )
            gpu_memory_used = (
                exponential_moving_average_efficient(
                    data=per_user_total_gpu_memory_used[username],
                    N=min(25, len(per_user_total_gpu_memory_used[username])),
                )
                if len(per_user_total_gpu_memory_used[username]) > 0
                else -1
            )
            gpu_utilization = (
                exponential_moving_average_efficient(
                    data=per_user_total_gpu_utilization[username],
                    N=min(25, len(per_user_total_gpu_utilization[username])),
                )
                if len(per_user_total_gpu_utilization[username]) > 0
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
                    gpu_count_actual,
                    str(creation_time),
                    age,
                ]
            )

        df = pd.DataFrame(data, columns=columns)
        # Inside your loop, when you update the DataFrame

        st.dataframe(
            df
        )  # This will update the existing table instead of creating a new one

        if not loop:
            break
        time.sleep(
            refresh_interval
        )  # Refresh every specified number of seconds


if __name__ == "__main__":
    fire.Fire(fetch_and_render_pod_info)
