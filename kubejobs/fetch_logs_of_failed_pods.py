import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

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
        shell=True,
    )
    # Add decoding and error handling
    stdout = result.stdout.decode("utf-8", errors="ignore")
    stderr = result.stderr.decode("utf-8", errors="ignore")
    return stdout, stderr


def ssh_into_pod_and_run_command(
    pod_name: str, namespace: str, command: str
) -> str:
    ssh_command = f"kubectl exec -n {namespace} {pod_name} -- {command}"
    stdout, stderr = run_command(ssh_command)
    if stderr:
        print(f"Error executing command in pod {pod_name}: {stderr}")
    return stdout


def fetch_logs_of_failed_jobs(
    namespace: str, matching_string: str, log_dir: str | Path = "logs"
):
    """
    Fetches logs of failed jobs in a specified namespace and deletes the job afterwards.

    Args:
        namespace (str): The namespace to check for failed jobs.
        matching_string (str): A string to filter pods by. Only pods containing this string in their name would be considered.
    """
    get_pods_cmd = f"kubectl get pods -n {namespace} -o json"
    pods_output, _ = run_command(get_pods_cmd)
    pod_data = json.loads(pods_output.strip())

    if isinstance(log_dir, str):
        log_dir = Path(log_dir)

    for pod in pod_data["items"]:
        pod_name = pod["metadata"]["name"]

        # If the pod's name doesn't contain the matching_string, skip this iteration
        if matching_string not in pod_name:
            continue

        status = pod["status"]["phase"]
        labels = pod["metadata"].get("labels", {})

        if "job-name" in labels and status.lower() == "failed":
            try:
                log_command = f"kubectl logs {pod_name} -n {namespace}"
                log_output, _ = run_command(log_command)
                log_path = log_dir / f"{pod_name}.log"

                with open(log_path, "w") as file:
                    file.write(log_output)

                print(f"Log saved for failed pod {pod_name}")

                delete_pod_command = (
                    f"kubectl delete pod {pod_name} -n {namespace}"
                )
                _, _ = run_command(delete_pod_command)
                print(f"{pod_name} deleted.")
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")
                print(f"Stdout output: {e.stdout}")
                print(f"Stderr output: {e.stderr}")


if __name__ == "__main__":
    fire.Fire(fetch_logs_of_failed_jobs)
