# Example usage:
import time

from rich import print

from kubejobs.jobs import KubernetesJob, create_pvc

env_vars = {
    "DATASET_DIR": "/data/",
    "MODEL_DIR": "/data/model/",
}

# unique id generated using time

unique_id = time.strftime("%Y%m%d%H%M%S")

# create some persistent storage to keep around model weights, and perhaps data if you need it
create_pvc(
    pvc_name="my-data-pvc-0", storage="100Gi", access_modes="ReadWriteOnce"
)

job = KubernetesJob(
    name=f"gate-node-{unique_id}",
    image="ghcr.io/antreasantoniou/gate:latest",
    command=["/bin/bash", "-c", "--"],
    args=["while true; do sleep 60; done;"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-40GB",
    gpu_limit=1,
    shm_size="100G",  # "200G" is the maximum value for shm_size
    backoff_limit=4,
    cpu_request=192 // 8,
    ram_request=f"{890 // 8}G",
    env_vars=env_vars,
    # volume_mounts={
    #     "dataset-disk": {
    #         "pvc": "my-data-pvc-0",
    #         "mountPath": "/data",
    #     },
    # },
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
