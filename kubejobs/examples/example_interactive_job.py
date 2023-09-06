# Example usage:
import time

from kubejobs.jobs import KubernetesJob


env_vars = {}

# unique id generated using time


unique_id = time.strftime("%Y%m%d%H%M%S")


job = KubernetesJob(
    name="tali-data-copy",
    image="ghcr.io/antreasantoniou/gate:latest",
    command=["/bin/bash", "-c", "--"],
    args=["while true; do sleep 60; done;"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-40GB",
    shm_size="100G",  # "200G" is the maximum value for shm_size
    gpu_limit=1,
    backoff_limit=3,
    volume_mounts={
        "tali-disk-0": {
            "pvc": "tali-pvc-0",
            "mountPath": "/data/",
        },
        "tali-disk-3": {
            "pvc": "tali-pvc-3",
            "mountPath": "/data2/",
        },
        "tali-disk-4": {
            "pvc": "tali-pvc-4",
            "mountPath": "/data3/",
        },
        "tali-disk-5": {
            "pvc": "tali-pvc-5",
            "mountPath": "/data4/",
        },
        "tali-disk-6": {
            "pvc": "tali-pvc-6",
            "mountPath": "/data5/",
        },
        "tali-disk-7": {
            "pvc": "tali-pvc-7",
            "mountPath": "/data6/",
        },
        "tali-disk-8": {
            "pvc": "tali-pvc-8",
            "mountPath": "/data7/",
        },
    },
    env_vars=env_vars,
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
