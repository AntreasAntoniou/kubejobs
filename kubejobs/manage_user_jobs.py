import json
import subprocess
from datetime import datetime, timezone
from typing import Dict, Optional

import fire
import rich
from rich import print
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

console = Console()


# 🚀 Run shell command and return the output
def run_command(cmd: str) -> str:
    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


# 📅 Parse ISO formatted time to Python datetime object
def parse_iso_time(time_str: str) -> datetime:
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


# ⏳ Convert time difference to human-readable format
def time_diff_to_human_readable(start: datetime, end: datetime) -> str:
    diff = end - start
    minutes, seconds = divmod(diff.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{diff.days}d {hours}h {minutes}m {seconds}s"


def highlight_term(text: str, term: str, style: str = "[bold cyan]") -> str:
    return text.replace(term, f"{style}{term}[/]")


def get_job_status(job_name: str, namespace: str, job_dict: Dict) -> str:
    # "status": {
    #     "completionTime": "2023-10-23T17:45:25Z",
    #     "conditions": [
    #         {
    #             "lastProbeTime": "2023-10-23T17:45:25Z",
    #             "lastTransitionTime": "2023-10-23T17:45:25Z",
    #             "status": "True",
    #             "type": "Complete"
    #         }
    #     ],
    #     "failed": 1,
    #     "ready": 0,
    #     "startTime": "2023-10-23T16:38:56Z",
    #     "succeeded": 1,
    #     "uncountedTerminatedPods": {}
    # }

    # "status": {
    #     "conditions": [
    #         {
    #             "lastProbeTime": "2023-10-23T18:01:12Z",
    #             "lastTransitionTime": "2023-10-23T18:01:12Z",
    #             "message": "Job has reached the specified backoff limit",
    #             "reason": "BackoffLimitExceeded",
    #             "status": "True",
    #             "type": "Failed"
    #         }
    #     ],
    #     "failed": 5,
    #     "ready": 0,
    #     "startTime": "2023-10-23T17:28:00Z",
    #     "uncountedTerminatedPods": {}
    # }

    status_dict = job_dict["status"]
    failed_count = status_dict.get("failed", 0)
    succeeded_count = status_dict.get("succeeded", 0)
    conditions = status_dict.get("conditions", [])
    ready = status_dict.get("ready", 0)
    try:
        output_dict = {
            "failed": failed_count,
            "succeeded": succeeded_count,
            "condition": conditions[-1]["type"] if conditions else "--",
            "reason": conditions[-1]["reason"]
            if (conditions and hasattr(conditions[-1], "reason"))
            else "--",
            "ready": ready,
        }
    except Exception as e:
        print(e)
        print(conditions)

        raise e

    output_dict = {k: str(v) for k, v in output_dict.items()}

    return output_dict


# 🕵️‍♀️ List or delete Kubernetes jobs by user
def list_or_delete_jobs_by_user(
    namespace: str,
    username: str,
    term: str,
    delete: bool = False,
    show_job_status: bool = False,
) -> None:
    # Fetch all jobs from a specific Kubernetes namespace
    get_jobs_cmd = f"kubectl get jobs -n {namespace} -o json"
    jobs_output = run_command(get_jobs_cmd)
    jobs_json = json.loads(jobs_output)

    filtered_jobs = []  # Store jobs that match filters
    current_time = datetime.now(timezone.utc)

    # Initialize table for displaying job details
    # BOXES = [
    #     "ASCII",
    #     "ASCII2",
    #     "ASCII_DOUBLE_HEAD",
    #     "SQUARE",
    #     "SQUARE_DOUBLE_HEAD",
    #     "MINIMAL",
    #     "MINIMAL_HEAVY_HEAD",
    #     "MINIMAL_DOUBLE_HEAD",
    #     "SIMPLE",
    #     "SIMPLE_HEAD",
    #     "SIMPLE_HEAVY",
    #     "HORIZONTALS",
    #     "ROUNDED",
    #     "HEAVY",
    #     "HEAVY_EDGE",
    #     "HEAVY_HEAD",
    #     "DOUBLE",
    #     "DOUBLE_EDGE",
    #     "MARKDOWN",
    # ]
    table = Table(
        title="🔍 Kubernetes Jobs",
        show_header=True,
        header_style="bold magenta",
        box=rich.box.SQUARE,
    )
    table.add_column("📛 Name", width=75)
    table.add_column("⏳ Duration", justify="right")
    table.add_column("⌛ Age", justify="right")
    table.add_column("✅ Completions", justify="right")
    if show_job_status:
        table.add_column("💥 Failed", justify="right")
        table.add_column("🏆 Succeeded", justify="right")
        table.add_column("👀 Condition", justify="right")
        table.add_column("🧐 Reason", justify="right")
        table.add_column("🔖 Ready", justify="right")

    # Filter jobs and fill in the table
    for item in tqdm(jobs_json["items"]):
        annotations = item["metadata"].get("annotations", {})
        if (
            annotations.get("username", "") == username
            and term in item["metadata"]["name"]
        ):
            filtered_jobs.append(item)

            if show_job_status:
                job_status = get_job_status(
                    item["metadata"]["name"], namespace, item
                )
                add_row_to_table(item, current_time, table, term, job_status)

            else:
                add_row_to_table(item, current_time, table, term)

    # Display the table
    console.print(table)

    # Optionally delete filtered jobs
    if delete:
        delete_filtered_jobs(filtered_jobs, namespace, username, term)


# 📝 Add a row to the table with job details
def add_row_to_table(
    item: dict,
    current_time: datetime,
    table: Table,
    term: str,
    job_status: Optional[Dict] = None,
) -> None:
    job_name = item["metadata"]["name"]
    job_name = highlight_term(job_name, term)
    completions = (
        f"{item['status'].get('succeeded', 0)}/{item['spec']['completions']}"
    )

    if job_status:
        if job_status["condition"] == "Failed":
            row_style = "red"
        elif completions == "1/1":
            row_style = "bold green"
        else:
            row_style = "yellow"
    else:
        row_style = "yellow" if completions != "1/1" else "bold green"

    # Determine completion text based on the job_status
    if job_status:
        completion_text = (
            f"{completions}✔ Completed"
            if completions == "1/1"
            else f"{completions}|❌ Failed"
            if job_status["condition"] == "Failed"
            else f"{completions}|⏳ Running"
        )
    else:
        completion_text = (
            f"{completions}|⏳ Running"
            if completions != "1/1"
            else f"{completions}|✔ Completed"
        )

    # Get other job details
    creation_time = parse_iso_time(item["metadata"]["creationTimestamp"])
    age = time_diff_to_human_readable(creation_time, current_time)
    duration = get_job_duration(item)

    # Add row with determined style
    if job_status:
        table.add_row(
            job_name,
            duration,
            age,
            completion_text,
            *list(job_status.values()),
            style=row_style,
        )
    else:
        table.add_row(
            job_name,
            duration,
            age,
            completion_text,
            style=row_style,
        )


# ⏱ Calculate job duration if available
def get_job_duration(item: dict) -> str:
    start_time_str = item["status"].get("startTime")
    completion_time_str = item["status"].get("completionTime")
    if start_time_str and completion_time_str:
        start_time = parse_iso_time(start_time_str)
        completion_time = parse_iso_time(completion_time_str)
        return time_diff_to_human_readable(start_time, completion_time)
    return "N/A"


# 🗑 Delete filtered jobs
def delete_filtered_jobs(
    filtered_jobs: list, namespace: str, username: str, term: str
) -> None:
    for item in filtered_jobs:
        job_name = item["metadata"]["name"]
        del_cmd = f"kubectl delete job {job_name} -n {namespace}"
        run_command(del_cmd)
    console.print(
        f"[red]✅ Deleted jobs initiated by '{username}' in namespace '{namespace}' matching term '{term}'[/red]"
    )


if __name__ == "__main__":
    fire.Fire(list_or_delete_jobs_by_user)
