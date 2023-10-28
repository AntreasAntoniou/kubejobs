import json
import subprocess
from datetime import datetime, timezone

import fire
import pandas as pd
import rich
import streamlit as st
from rich.console import Console
from rich.progress import Progress
from rich.table import Table


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
    return result.stdout


def fetch_and_render_pod_info(namespace="informatics"):
    get_pods_cmd = f"kubectl get pods -n {namespace} -o json"
    pods_output = run_command(get_pods_cmd)
    pod_data = json.loads(pods_output)

    console = Console()

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
        "Creation Time",
        "Age",
    ]
    data = []

    table = Table(
        show_header=True, header_style="bold magenta", box=rich.box.SQUARE
    )
    for col in columns:
        table.add_column(col)

    current_time = datetime.now(timezone.utc)

    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Processing Pods...", total=len(pod_data["items"])
        )

        for pod in pod_data["items"]:
            progress.update(task, advance=1)

            metadata = pod["metadata"]
            spec = pod.get("spec", {})
            status = pod["status"]

            name = metadata["name"]
            namespace = metadata["namespace"]
            uid = metadata["uid"]

            # "spec": {
            #     "template": {
            #         "metadata": {
            #             "annotations": self.metadata  # Add metadata to Pod template as well
            #         },
            username = (
                spec.get("template", {})
                .get("metadata", "N/A")
                .get("annotations")
                .get("username", "N/A")
            )

            pod_status = status["phase"]
            node = spec.get("nodeName", "N/A")

            container = spec.get("containers", [{}])[0]
            image = container.get("image", "N/A")

            resources = container.get("resources", {})
            cpu_request = resources.get("requests", {}).get("cpu", "N/A")
            memory_request = resources.get("requests", {}).get("memory", "N/A")
            gpu_type = spec.get("nodeSelector", {}).get(
                "nvidia.com/gpu.product", "N/A"
            )
            gpu_limit = resources.get("limits", {}).get(
                "nvidia.com/gpu", "N/A"
            )

            creation_time = parse_iso_time(metadata["creationTimestamp"])
            age = time_diff_to_human_readable(creation_time, current_time)

            row = [
                name,
                namespace,
                username,
                uid,
                pod_status,
                node,
                image,
                cpu_request,
                memory_request,
                gpu_type,
                str(gpu_limit),
                str(creation_time),
                age,
            ]
            data.append(row)
            table.add_row(*row)

    console.print(table)

    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df)


if __name__ == "__main__":
    fire.Fire(fetch_and_render_pod_info)
