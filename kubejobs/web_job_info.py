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


def run_command(cmd: str) -> str:
    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def fetch_and_render_job_info(namespace="informatics"):
    # Initialize Rich Console and Progress Bar
    console = Console()
    progress = Progress(console=console)

    # Run kubectl command to get job information in json format
    get_jobs_cmd = f"kubectl get jobs -n {namespace} -o json"
    jobs_output = run_command(get_jobs_cmd)
    jobs_data = json.loads(jobs_output)

    # Initialize data for Streamlit and Rich Table
    st_data = []
    table = Table(
        show_header=True, header_style="bold magenta", box=rich.box.SQUARE
    )
    table.add_column("Name")
    table.add_column("Namespace")
    table.add_column("UID")
    table.add_column("Creation Time")
    table.add_column("Age")
    table.add_column("Completions")
    table.add_column("Failed")
    table.add_column("Succeeded")
    table.add_column("CPU Request")
    table.add_column("Memory Request")
    table.add_column("GPU Type")
    table.add_column("GPU Limit")
    table.add_column("Username", "No Info")

    current_time = datetime.now(timezone.utc)

    # Populate data
    with progress:
        task = progress.add_task(
            "[cyan]Fetching and Rendering Jobs...",
            total=len(jobs_data["items"]),
        )
        for job in jobs_data["items"]:
            metadata = job["metadata"]
            status = job["status"]
            spec = job.get("spec", {})
            template_spec = spec.get("template", {}).get("spec", {})
            containers = template_spec.get("containers", [{}])[0]
            resources = containers.get("resources", {})
            node_selector = template_spec.get("nodeSelector", {})

            name = metadata.get("name", "N/A")
            namespace = metadata.get("namespace", "N/A")
            username = metadata.get("annotations", {}).get("username", "N/A")

            uid = metadata.get("uid", "N/A")
            creation_time = parse_iso_time(
                metadata.get("creationTimestamp", "")
            )
            age = time_diff_to_human_readable(creation_time, current_time)
            completions = spec.get("completions", "N/A")
            failed = status.get("failed", "N/A")
            succeeded = status.get("succeeded", "N/A")
            cpu_request = resources.get("requests", {}).get("cpu", "N/A")
            memory_request = resources.get("requests", {}).get("memory", "N/A")
            gpu_type = node_selector.get("nvidia.com/gpu.product", "N/A")
            gpu_limit = resources.get("limits", {}).get(
                "nvidia.com/gpu", "N/A"
            )

            st_data.append(
                [
                    name,
                    namespace,
                    username,
                    uid,
                    str(creation_time),
                    age,
                    str(completions),
                    str(failed),
                    str(succeeded),
                    cpu_request,
                    memory_request,
                    gpu_type,
                    gpu_limit,
                ]
            )
            table.add_row(
                name,
                namespace,
                username,
                uid,
                str(creation_time),
                age,
                str(completions),
                str(failed),
                str(succeeded),
                cpu_request,
                memory_request,
                gpu_type,
                str(gpu_limit),
            )

            progress.update(task, advance=1)

    console.print(table)

    # Streamlit data rendering
    st.title("Kubernetes Jobs Information")
    df = pd.DataFrame(
        st_data,
        columns=[
            "Name",
            "Namespace",
            "Username",
            "UID",
            "Creation Time",
            "Age",
            "Completions",
            "Failed",
            "Succeeded",
            "CPU Request",
            "Memory Request",
            "GPU Type",
            "GPU Limit",
        ],
    )
    st.dataframe(df)


if __name__ == "__main__":
    fire.Fire(fetch_and_render_job_info)
