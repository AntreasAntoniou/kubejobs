# Example usage:
import time

from kubejobs import KubernetesJob, create_jobs_for_experiments, create_pvc

# unique id generated using time

unique_id = time.strftime("%Y%m%d%H%M%S")


job = KubernetesJob(
    name=f"node-info-40gb-interactive-{unique_id}",
    image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
    command=["/bin/bash", "-c", "--"],
    args=["while true; do sleep 60; done;"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-80GB",
    shm_size="456G",  # "200G" is the maximum value for shm_size
    gpu_limit=2,
    backoff_limit=4,
    volume_mounts={
        "dataset-disk": {
            "pvc": "datasets-pvc-0",
            "mountPath": "/data",
        },
    },
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
