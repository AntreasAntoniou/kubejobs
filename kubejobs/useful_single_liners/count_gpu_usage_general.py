import re
import subprocess
from collections import defaultdict
from typing import OrderedDict

import yaml
from rich import print
from rich.console import Console
from rich.table import Table
from tqdm.auto import tqdm

# NVIDIA-A100-SXM4-80GB – a full non-MIG 80GB GPU
# NVIDIA-A100-SXM4-40GB – a full non-MIG 40GB GPU
# NVIDIA-A100-SXM4-40GB-MIG-3g.20gb – just under half-GPU
# NVIDIA-A100-SXM4-40GB-MIG-1g.5gb – a seventh of a GPU

# 32 Nvidia A100 80 GB GPUs
# 70 Nvidia A100 40 GB GPUs
# 28 Nvidia A100 3G.20GB GPUs
# 140 A100 1G.5GB GPUs

GPU_DETAIL_DICT = {
    "NVIDIA-A100-SXM4-80GB": 32,
    "NVIDIA-A100-SXM4-40GB": 88,
    "NVIDIA-A100-SXM4-40GB-MIG-3g.20gb": 28,
    "NVIDIA-A100-SXM4-40GB-MIG-1g.5gb": 140,
}


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
    gpu_usage = {"Available": OrderedDict()}
    for pod, status in tqdm(pods):
        pod_description = "\n".join(describe_pod(pod))
        gpu_model, gpu_count = extract_gpu_info(pod_description)
        if gpu_model and gpu_count:
            if status not in gpu_usage:
                gpu_usage[status] = OrderedDict()
            if gpu_model in gpu_usage[status]:
                gpu_usage[status][gpu_model] += gpu_count
            else:
                gpu_usage[status][gpu_model] = gpu_count

    gpu_usage["Available"] = {
        k: v - gpu_usage["Running"][k] if k in gpu_usage["Running"] else v
        for k, v in GPU_DETAIL_DICT.items()
    }

    return gpu_usage


if __name__ == "__main__":
    gpu_usage = count_gpu_usage()

    # Create a table with dynamic columns based on the GPU models
    table = Table(title="GPU Usage")
    table.add_column("Status", justify="left", style="cyan")

    # Dynamically add columns for each GPU model
    for gpu_model in GPU_DETAIL_DICT.keys():
        table.add_column(gpu_model, justify="right", style="magenta")

    console = Console()

    # Create a defaultdict to ensure that if a GPU model is not present, it defaults to 0
    full_gpu_usage = defaultdict(lambda: defaultdict(int))

    for status, gpu_dict in gpu_usage.items():
        for gpu_model, count in gpu_dict.items():
            full_gpu_usage[status][gpu_model] = count

    # Populate the table
    for status, gpu_dict in full_gpu_usage.items():
        row = [status]
        for gpu_model in GPU_DETAIL_DICT.keys():
            row.append(
                str(gpu_dict.get(gpu_model, 0))
            )  # Use 0 if the GPU model is not found
        table.add_row(*row)

    console.print(table)
