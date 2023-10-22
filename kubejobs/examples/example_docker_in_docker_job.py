import time

from rich import print

from kubejobs.jobs import KubernetesJob

# unique id generated using time
unique_id = time.strftime("%Y%m%d%H%M%S")


job = KubernetesJob(
    name=f"dind-{unique_id}",
    image="docker:dind",
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-40GB",
    gpu_limit=1,
    shm_size="100G",
    backoff_limit=4,
    cpu_request=24,
    ram_request="100G",
    privileged_security_context=True,
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()

from rich.console import Console

console = Console()

notes = """
# Notes

- Use `apk add micro` to install micro editor in the container
- Use `apk add nano` to install nano editor in the container
- Use `apk add git` to install git in the container
- Then you want to git clone your repo, cd into it, and run docker build -t myimage .
- Then follow https://github.com/AntreasAntoniou/useful-commands/blob/main/docker.md to push the image to ghcr.io
- Then you can use the image in a job
- Well done! :D
"""

console.print(notes, style="bold magenta")
