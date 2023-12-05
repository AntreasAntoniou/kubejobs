import json
import subprocess

import fire
from rich import print
from rich.table import Table
from tqdm.auto import tqdm


def check_jobs():
    # Get all jobs
    get_jobs_command = ["kubectl", "get", "jobs", "-o", "json"]
    jobs_output = subprocess.check_output(get_jobs_command)
    jobs_json = json.loads(jobs_output)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Job Name", style="green", width=50)
    table.add_column("Pods", style="yellow", width=50)

    for job in tqdm(jobs_json["items"]):
        job_name = job["metadata"]["name"]

        # Get job details
        get_job_command = ["kubectl", "get", "job", job_name, "-o", "json"]
        job_output = subprocess.check_output(get_job_command)
        job_json = json.loads(job_output)

        # Check if the job has failed pods
        failed_pods = job_json["status"].get("failed", 0)

        # Check if the job has completed pods
        completed_pods = job_json["status"].get("succeeded", 0)

        if failed_pods > 0 and completed_pods == 0:
            # Get all pods for this job
            get_pods_command = [
                "kubectl",
                "get",
                "pods",
                "--selector",
                f"job-name={job_name}",
                "-o",
                "json",
            ]
            pods_output = subprocess.check_output(get_pods_command)
            pods_json = json.loads(pods_output)

            pods = [pod["metadata"]["name"] for pod in pods_json["items"]]
            table.add_row(job_name, "\n".join(pods))

    print(table)


if __name__ == "__main__":
    fire.Fire(check_jobs)
