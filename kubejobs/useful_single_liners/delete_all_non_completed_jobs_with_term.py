import json
import subprocess

import fire


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


# 🗑 Delete incomplete jobs
def delete_incomplete_jobs(namespace: str, term: str) -> None:
    # Fetch all jobs from a specific Kubernetes namespace
    get_jobs_cmd = f"kubectl get jobs -n {namespace} -o json"
    jobs_output = run_command(get_jobs_cmd)
    jobs_json = json.loads(jobs_output)

    # Filter jobs and delete if not completed and matching the term
    for item in jobs_json["items"]:
        job_name = item["metadata"]["name"]
        completions = item["status"].get("succeeded", 0)

        if completions != item["spec"]["completions"] and term in job_name:
            print(f"Deleting incomplete job: {job_name}")
            del_cmd = f"kubectl delete job {job_name} -n {namespace}"
            run_command(del_cmd)
            print(f"Deleted job: {job_name}")


if __name__ == "__main__":
    fire.Fire(delete_incomplete_jobs)
