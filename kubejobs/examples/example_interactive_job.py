# Example usage:
import time

from kubejobs.jobs import KubernetesJob


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

# unique id generated using time


unique_id = time.strftime("%Y%m%d%H%M%S")


job = KubernetesJob(
    name="gate-node-0",
    image="ghcr.io/antreasantoniou/gate:latest",
    command=["/bin/bash", "-c", "--"],
    args=["while true; do sleep 60; done;"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-80GB",
    shm_size="900G",  # "200G" is the maximum value for shm_size
    gpu_limit=1,
    backoff_limit=4,
    volume_mounts={
        "gate-disk-0": {
            "pvc": "gate-pvc-0",
            "mountPath": "/data/",
        },
        # "tali-disk-0": {
        #     "pvc": "datasets-pvc-0",
        #     "mountPath": "/data/",
        # },
        # "tali-disk-1": {
        #     "pvc": "tali-pvc-1",
        #     "mountPath": "/data0/",
        # },
        # "tali-disk-2": {
        #     "pvc": "tali-pvc-2",
        #     "mountPath": "/data1/",
        # },
        # "tali-disk-0": {
        #     "pvc": "tali-pvc-0",
        #     "mountPath": "/data/",
        # },
    },
    env_vars=env_vars,
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
