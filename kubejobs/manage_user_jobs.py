import json
import subprocess
from datetime import datetime, timezone

import fire
import rich
from rich.console import Console
from rich.table import Table

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


# 🕵️‍♀️ List or delete Kubernetes jobs by user
def list_or_delete_jobs_by_user(
    namespace: str, username: str, term: str, delete: bool = False
) -> None:
    # Fetch all jobs from a specific Kubernetes namespace
    get_jobs_cmd = f"kubectl get jobs -n {namespace} -o json"
    jobs_output = run_command(get_jobs_cmd)
    jobs_json = json.loads(jobs_output)

    filtered_jobs = []  # Store jobs that match filters
    current_time = datetime.now(timezone.utc)

    # Initialize table for displaying job details
    table = Table(
        title="🔍 Kubernetes Jobs",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("📛 Name", width=50)
    table.add_column("✅ Completions", justify="right")
    table.add_column("⏳ Duration", justify="right")
    table.add_column("⌛ Age", justify="right")

    # Filter jobs and fill in the table
    for item in jobs_json["items"]:
        annotations = item["metadata"].get("annotations", {})
        if (
            annotations.get("user", "") == username
            and term in item["metadata"]["name"]
        ):
            filtered_jobs.append(item)
            add_row_to_table(item, current_time, table, term)

    # Display the table
    console.print(table)

    # Optionally delete filtered jobs
    if delete:
        delete_filtered_jobs(filtered_jobs, namespace, username, term)


# 📝 Add a row to the table with job details
def add_row_to_table(
    item: dict, current_time: datetime, table: Table, term: str
) -> None:
    job_name = item["metadata"]["name"]
    job_name = highlight_term(job_name, term)
    completions = (
        f"{item['status'].get('succeeded', 0)}/{item['spec']['completions']}"
    )
    completion_style = "bold green" if completions == "1/1" else "red"
    completion_text = (
        f"[{completion_style}]{completions}✔ Completed[/{completion_style}]"
        if completions == "1/1"
        else f"[{completion_style}]{completions}|❌ Incomplete[/{completion_style}]"
    )

    creation_time = parse_iso_time(item["metadata"]["creationTimestamp"])
    age = time_diff_to_human_readable(creation_time, current_time)
    duration = get_job_duration(item)
    table.add_row(
        job_name,
        completion_text,
        duration,
        age,
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
