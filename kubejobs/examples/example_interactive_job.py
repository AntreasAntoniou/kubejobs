# Example usage:
import time

from kubejobs.jobs import KubernetesJob, create_pvc

env_vars = {
    "DATASET_DIR": "/data/",
    "MODEL_DIR": "/data/model/",
}

# unique id generated using time

unique_id = time.strftime("%Y%m%d%H%M%S")

# create some persistent storage to keep around model weights, and perhaps data if you need it
create_pvc(pvc_name="my-data-pvc-0", storage="100Gi", access_modes="ReadWriteOnce")

job = KubernetesJob(
    name="gate-node-0",
    image="ghcr.io/antreasantoniou/gate:dev-latest",
    command=["/bin/bash", "-c", "--"],
    args=["while true; do sleep 60; done;"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-80GB",
    shm_size="100G",  # "200G" is the maximum value for shm_size
    gpu_limit=1,
    backoff_limit=4,
    volume_mounts={
        "my-data-disk-0": {
            "pvc": "my-data-pvc-0",
            "mountPath": "/data/",
        },
    },
    env_vars=env_vars,
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
