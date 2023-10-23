import json
import subprocess
from collections import OrderedDict, defaultdict

from rich import print
from rich.console import Console
from rich.table import Table
from tqdm.auto import tqdm

# GPU details
GPU_DETAIL_DICT = {
    "NVIDIA-A100-SXM4-80GB": 32,
    "NVIDIA-A100-SXM4-40GB": 88,
    "NVIDIA-A100-SXM4-40GB-MIG-3g.20gb": 28,
    "NVIDIA-A100-SXM4-40GB-MIG-1g.5gb": 140,
}


# 🚀 Execute the shell command and get the output
def run_command(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def get_k8s_pods_gpu_info():
    # Run kubectl command to get all pods in JSON format
    result = subprocess.run(
        ["kubectl", "get", "pods", "-o", "json"], stdout=subprocess.PIPE
    )

    pod_json = json.loads(result.stdout)

    # Initialize the dictionary to store GPU info for each pod
    pod_gpu_info = {}

    # Loop through each pod
    for pod in pod_json["items"]:
        pod_name = pod["metadata"]["name"]
        containers = pod["spec"]["containers"]

        # Initialize GPU count to 0
        gpu_count = 0
        gpu_type = "Unknown"

        # Check if pod has nodeSelector for GPU type
        if "nodeSelector" in pod["spec"]:
            gpu_type = pod["spec"]["nodeSelector"].get(
                "nvidia.com/gpu.product", "Unknown"
            )

        # Loop through each container to sum up GPU requests
        for container in containers:
            resources = container["resources"]
            if (
                "limits" in resources
                and "nvidia.com/gpu" in resources["limits"]
            ):
                gpu_count += int(resources["limits"]["nvidia.com/gpu"])

        # Store GPU info for the pod
        pod_gpu_info[pod_name] = {
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "phase": pod["status"]["phase"],
        }

    return pod_gpu_info


# 📝 Extract GPU info from containers' resources
def extract_gpu_info(containers):
    gpu_model = None
    gpu_count = 0
    for container in containers:
        resources = container.get("resources", {})
        limits = resources.get("limits", {})
        if "nvidia.com/gpu" in limits:
            gpu_count += int(limits["nvidia.com/gpu"])
            annotations = container.get("annotations", {})
            gpu_model = annotations.get("nvidia.com/gpu.product")
    return gpu_model, gpu_count


def count_gpu_usage():
    pod_gpu_info = get_k8s_pods_gpu_info()
    gpu_usage = {"Available": OrderedDict()}

    for pod_name, info in pod_gpu_info.items():
        gpu_model = info["gpu_type"]
        gpu_count = info["gpu_count"]

        # Here you may also consider the 'status' of the pod to categorize GPU usage
        status = info["phase"]

        if gpu_model and gpu_count:
            if status not in gpu_usage:
                gpu_usage[status] = OrderedDict()
            if gpu_model in gpu_usage[status]:
                gpu_usage[status][gpu_model] += gpu_count
            else:
                gpu_usage[status][gpu_model] = gpu_count

    gpu_usage["Available"] = {
        k: v - gpu_usage.get("Running", {}).get(k, 0)
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

    # Populate the table
    for status, gpu_dict in gpu_usage.items():
        row = [status]
        for gpu_model in GPU_DETAIL_DICT.keys():
            row.append(
                str(gpu_dict.get(gpu_model, 0))
            )  # Use 0 if the GPU model is not found
        table.add_row(*row)

    console.print(table)
