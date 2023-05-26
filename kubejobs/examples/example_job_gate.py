# Example usage:
import time

from kubejobs import KubernetesJob, create_jobs_for_experiments, create_pvc


env_vars = {
    "NEPTUNE_API_TOKEN": "eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiJkOTFjMTY5Zi03ZGUwLTQ4ODYtYWI0Zi1kZDEzNjlkMGI5ZjQifQ==",
    "NEPTUNE_PROJECT": "MachineLearningBrewery/gate-dev-0-8-0",
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
    "EXPERIMENTS_DIR": "/experiments/",
    "EXPERIMENT_DIR": "/experiments/",
    "TALI_DATASET_DIR": "/tali-data/",
    "WIT_DATASET_DIR": "/tali-data/wit/",
    "MODEL_DIR": "/model/",
}

# unique id generated using time


unique_id = time.strftime("%Y%m%d%H%M%S")


job = KubernetesJob(
    name=f"gate-node-0-{unique_id}",
    image="ghcr.io/antreasantoniou/gate:latest",
    command=["/bin/bash", "-c", "--"],
    args=["export"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-40GB",
    shm_size="120G",  # "200G" is the maximum value for shm_size
    gpu_limit=1,
    backoff_limit=4,
    volume_mounts={
        "gate-disk": {
            "pvc": "datasets-pvc-0",
            "mountPath": "/data/",
        },
    },
    env_vars=env_vars,
)

job_yaml = job.generate_yaml()
print(job_yaml)
job.run()
