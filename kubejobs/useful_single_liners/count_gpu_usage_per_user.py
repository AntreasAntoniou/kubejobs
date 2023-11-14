import json
import subprocess

import yaml
from rich.console import Console
from rich.table import Table


def get_gpu_usage():
    json_output = subprocess.check_output(
        ["kubectl", "get", "pods", "-o", "json"]
    )

    pods_info = json.loads(json_output)

    gpu_usage = {}
    user_gpu_usage = {}
    for item in pods_info["items"]:
        pod_name = item["metadata"]["name"]
        user_name = pod_name

        for container in item["spec"]["containers"]:
            gpu_request = (
                container["resources"]
                .get("requests", {})
                .get("nvidia.com/gpu")
            )
            gpu_model = (
                item["spec"]
                .get("nodeSelector", {})
                .get("nvidia.com/gpu.product")
            )

            if gpu_model and gpu_request:
                gpu_usage[gpu_model] = gpu_usage.get(gpu_model, 0) + int(
                    gpu_request
                )
                user_gpu_usage[user_name] = user_gpu_usage.get(user_name, {})
                user_gpu_usage[user_name][gpu_model] = user_gpu_usage[
                    user_name
                ].get(gpu_model, 0) + int(gpu_request)

    return gpu_usage, user_gpu_usage


def print_table(title, data, gpu_model_keys):
    console = Console()

    table = Table(show_header=True, header_style="bold magenta")

    table.add_column("Pod Name")
    for gpu_model in gpu_model_keys:
        table.add_column(gpu_model)

    for key, value in data.items():
        row = [key]
        for gpu_model in gpu_model_keys:
            row.append(str(value.get(gpu_model, 0)))
        table.add_row(*row)

    console.print(title)
    console.print(table)


gpu_usage, user_gpu_usage = get_gpu_usage()
gpu_models = list(gpu_usage.keys())

print_table("Pod Specific GPU Usage:", user_gpu_usage, gpu_models)
