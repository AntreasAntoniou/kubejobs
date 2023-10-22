# Example usage:
import time

from kubejobs.jobs import KubernetesJob

<<<<<<< HEAD
env_vars = {
    "NEPTUNE_API_TOKEN": "eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiJkOTFjMTY5Zi03ZGUwLTQ4ODYtYWI0Zi1kZDEzNjlkMGI5ZjQifQ==",
    "NEPTUNE_PROJECT": "MachineLearningBrewery/gate-exp-0-8-6",
    "NEPTUNE_ALLOW_SELF_SIGNED_CERTIFICATE": "TRUE",
    "WANDB_API_KEY": "821661c6ee1657a2717093701ab76574ae1a9be0",
    "WANDB_ENTITY": "machinelearningbrewery",
    "WANDB_PROJECT": "gate-exp-0-8-6",
    "KAGGLE_USERNAME": "antreasantoniou",
    "KAGGLE_KEY": "d14aab63e71334cfa118bd5251bf85da",
    "PYTEST_DIR": "/data/",
    "EXPERIMENT_NAME": "gate-exp-0-8-6",
    "HF_USERNAME": "Antreas",
    "HF_TOKEN": "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",
    "HF_CACHE_DIR": "/data/",
    "TOKENIZERS_PARALLELISM": "false",
    "CODE_DIR": "/app/",
    "PROJECT_DIR": "/app/",
    "EXPERIMENT_NAME_PREFIX": "gate-exp",
    "EXPERIMENTS_DIR": "/data/experiments/",
    "EXPERIMENT_DIR": "/data/experiments/",
    "TALI_DATASET_DIR": "/tali-data/",
    "WIT_DATASET_DIR": "/tali-data/wit/",
    "DATASET_DIR": "/data/",
    "MODEL_DIR": "/data/model/",
}
=======

env_vars = {}
>>>>>>> 38efc841ec3bc60ac886c8d0fa2455937c2dc8fd

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
