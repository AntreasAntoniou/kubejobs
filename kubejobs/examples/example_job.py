# Example usage:
import time

from kubejobs.jobs import (
    KubernetesJob,
    create_jobs_for_experiments,
    create_pvc,
)

# unique id generated using time

unique_id = time.strftime("%Y%m%d%H%M%S")

create_pvc(
    pvc_name="datasets-pvc", storage="1Gi", access_modes="ReadWriteOnce"
)

job = KubernetesJob(
    name=f"node-info-80gb-full-{unique_id}",
    image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
    command=["/bin/bash"],
    args=["-c", "df -h"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-80GB",
    gpu_limit=2,
    backoff_limit=4,
    volume_mounts={
        "node-info-80gb-full": {"mountPath": "/node-info"},
        "dataset-disk": {
            "pvc": "datasets-pvc-0",
            "mountPath": "/data",
        },
    },
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
