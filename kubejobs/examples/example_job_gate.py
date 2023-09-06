# Example usage:
import time

from kubejobs.jobs import KubernetesJob


env_vars = {}

# unique id generated using time


unique_id = time.strftime("%Y%m%d%H%M%S")


job = KubernetesJob(
    name="gate-node-dev",
    image="ghcr.io/antreasantoniou/gate:latest",
    command=["/bin/bash", "-c", "--"],
    args=["while true; do sleep 60; done;"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-40GB",
    shm_size="100G",  # "200G" is the maximum value for shm_size
    gpu_limit=1,
    backoff_limit=3,
    volume_mounts={
        "gate-disk": {
            "pvc": "gate-pvc-1",
            "mountPath": "/data/",
        },
    },
    env_vars=env_vars,
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
