# Example usage:
from collections import defaultdict
import time
from tqdm.auto import tqdm

from kubejobs import KubernetesJob, create_jobs_for_experiments, create_pvc
from kubejobs.experiments.experiment_command_generator import get_commands
from kubejobs.experiments.pvc_status import PVCStatus, get_pvc_status

import logging
from rich.logging import RichHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RichHandler(markup=True)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

env_vars = dict(
    NEPTUNE_API_TOKEN="eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiJkOTFjMTY5Zi03ZGUwLTQ4ODYtYWI0Zi1kZDEzNjlkMGI5ZjQifQ==",
    NEPTUNE_PROJECT="MachineLearningBrewery/gate-exp-0-8-6",
    NEPTUNE_ALLOW_SELF_SIGNED_CERTIFICATE="TRUE",
    WANDB_API_KEY="821661c6ee1657a2717093701ab76574ae1a9be0",
    WANDB_ENTITY="machinelearningbrewery",
    WANDB_PROJECT="gate-exp-0-8-6",
    KAGGLE_USERNAME="antreasantoniou",
    KAGGLE_KEY="d14aab63e71334cfa118bd5251bf85da",
    PYTEST_DIR="/data/",
    EXPERIMENT_NAME="gate-exp-0-8-6",
    HF_USERNAME="Antreas",
    HF_TOKEN="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",
    HF_CACHE_DIR="/data/",
    TOKENIZERS_PARALLELISM="false",
    CODE_DIR="/app/",
    PROJECT_DIR="/app/",
    EXPERIMENT_NAME_PREFIX="gate-exp",
    EXPERIMENTS_DIR="/data/experiments/",
    EXPERIMENT_DIR="/data/experiments/",
    DATASET_DIR="/data/",
    MODEL_DIR="/data/model/",
)


pvc_dict = get_pvc_status()

prefix = "hephaestus"

experiment_dict = get_commands(prefix=prefix)

# Initialize a dictionary to keep track of PVC usage
pvc_usage = defaultdict(int)

total_pvc_count = 50

for i in range(total_pvc_count):
    pvc_name = f"gate-pvc-{i}"
    pvc_name = create_pvc(
        pvc_name=pvc_name, storage="2Ti", access_modes="ReadWriteOnce"
    )

for idx, (name, command) in tqdm(enumerate(experiment_dict.items())):
    pvc_dict: PVCStatus = get_pvc_status()
    while len(pvc_dict.available) == 0:
        pvc_dict: PVCStatus = get_pvc_status()
        time.sleep(10)

    # Select the PVC that has been used the least number of times
    pvc_name = min(pvc_dict.available, key=lambda pvc: pvc_usage[pvc])
    pvc_dict.available.remove(pvc_name)
    pvc_dict.in_use.append(pvc_name)

    # Increment the usage count for the selected PVC
    pvc_usage[pvc_name] += 1

    job = KubernetesJob(
        name=f"{name}",
        image="ghcr.io/antreasantoniou/gate:latest",
        command=["/bin/bash", "-c", "--"],
        args=[f"{command}"],
        gpu_type="nvidia.com/gpu",
        gpu_product="NVIDIA-A100-SXM4-40GB",
        shm_size="100G",  # "200G" is the maximum value for shm_size
        gpu_limit=1,
        backoff_limit=4,
        volume_mounts={
            "gate-disk": {
                "pvc": pvc_name,
                "mountPath": "/data/",
            },
        },
        env_vars=env_vars,
    )

    job_yaml = job.generate_yaml()
    try:
        job.run()
    except Exception as e:
        logger.warning(f"Job {name} failed with error: {e}")
    time.sleep(2)
