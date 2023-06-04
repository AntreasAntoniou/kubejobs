import subprocess
import re
import yaml

from rich import print
from rich.console import Console
from rich.table import Table
import re

from tqdm.auto import tqdm

import subprocess


def run_subprocess(command):
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.split("\n")


def get_pods():
    pods = run_subprocess(
        [
            "kubectl",
            "get",
            "pods",
            "-o",
            "jsonpath={range .items[*]}{.metadata.name}{','}{.status.phase}{','}{end}",
        ]
    )

    # Split the string into a list of pods
    pods = pods[0].split(",")[
        :-1
    ]  # The last item is an empty string due to the trailing comma

    # Group the pods into pairs of (name, status)
    pods = list(zip(pods[::2], pods[1::2]))

    return pods


def describe_pod(pod):
    result = run_subprocess(["kubectl", "describe", "pod", pod])
    return result


def extract_gpu_info(pod_description):
    model_pattern = re.compile(r"nvidia\.com/gpu\.product=(\S+)")
    count_pattern = re.compile(r"nvidia\.com/gpu:\s+(\d+)")

    model_match = model_pattern.search(pod_description)
    count_match = count_pattern.search(pod_description)

    gpu_model = model_match.group(1) if model_match else None
    gpu_count = int(count_match.group(1)) if count_match else None

    return gpu_model, gpu_count


def count_gpu_usage():
    pods = get_pods()
    gpu_usage = {"active": {}, "inactive": {}}
    for pod, status in tqdm(pods):
        pod_description = "\n".join(describe_pod(pod))
        gpu_model, gpu_count = extract_gpu_info(pod_description)
        if gpu_model and gpu_count:
            status = "active" if "Running" in status else "inactive"
            if gpu_model in gpu_usage[status]:
                gpu_usage[status][gpu_model] += gpu_count
            else:
                gpu_usage[status][gpu_model] = gpu_count
    return gpu_usage


if __name__ == "__main__":
    gpu_usage = count_gpu_usage()
    print(gpu_usage)
