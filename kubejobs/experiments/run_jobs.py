# Example usage:
import logging
import random
import time
from collections import defaultdict

from rich import print
from rich.logging import RichHandler
from tqdm.auto import tqdm


from kubejobs.experiments.few_shot_learning_command import (
    get_commands as get_few_shot_learning_commands,
)
from kubejobs.experiments.image_classification_command import (
    get_commands as get_image_classification_commands,
)
from kubejobs.experiments.medical_image_classification_command import (
    get_commands as get_medical_image_classification_commands,
)
from kubejobs.experiments.pvc_status import PVCStatus, get_pvc_status
from kubejobs.experiments.relational_reasoning_command import (
    get_commands as get_relational_reasoning_commands,
)
from kubejobs.experiments.zero_shot_learning_command import (
    get_commands as get_zero_shot_learning_commands,
)
from kubejobs.jobs import (
    KubernetesJob,
    create_jobs_for_experiments,
    create_pvc,
)
from kubejobs.useful_single_liners.count_gpu_usage_general import (
    count_gpu_usage,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RichHandler(markup=True)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

gpu_type_to_max_count = {
    "NVIDIA-A100-SXM4-80GB": 32,
    "NVIDIA-A100-SXM4-40GB": 88,
}


def get_gpu_type_to_use():
    active_gpus = count_gpu_usage()["active"]
    available_gpu_types = []

    for key, value in active_gpus.items():
        if key in gpu_type_to_max_count:
            remaining_gpu_count = gpu_type_to_max_count[key] - value
            if remaining_gpu_count > 0:
                available_gpu_types.append(key)

    return (
        random.choice(available_gpu_types)
        if len(available_gpu_types) > 0
        else None
    )


env_vars = dict(
    EXPERIMENT_NAME_PREFIX="gate-exp",
    EXPERIMENTS_DIR="/data/experiments/",
    EXPERIMENT_DIR="/data/experiments/",
    DATASET_DIR="/data/",
    MODEL_DIR="/data/model/",
)


pvc_dict = get_pvc_status()

prefix = "hades"

experiment_dict = 


# A summary of the GPU setup is:

# * 32 full Nvidia A100 80 GB GPUs
# * 70 full Nvidia A100 40 GB GPUs
# * 14 MIG Nvidia A100 40 GB GPUs equating to 28 Nvidia A100 3G.20GB GPUs
# * 20 MIG Nvidia A100 40 GB GPU equating to 140 A100 1G.5GB GPUs

# Total A100s in varying configurations: 136.

# Initialize a dictionary to keep track of PVC usage
pvc_usage = defaultdict(int)

total_pvc_count = 50

experiment_dict = list(experiment_dict.items())
# Shuffle the list
random.shuffle(experiment_dict)

# Create a new dictionary from the shuffled list
experiment_dict = dict(experiment_dict)

# experiment_dict = {
#     key: value for key, value in experiment_dict.items() if "winogr" not in key
# }

for name, command in experiment_dict.items():
    print(f"Command for {name}: {command}")

print(
    f"Total number of commands: {len(experiment_dict)}, each needs 1 GPU hour, so total GPU hours: {len(experiment_dict)}"
)

# for i in range(total_pvc_count):
#     pvc_name = f"gate-pvc-{i}"
#     pvc_name = create_pvc(
#         pvc_name=pvc_name, storage="2Ti", access_modes="ReadWriteOnce"
#     )
job_succesfully_launched = False
idx = 0
experiment_list = list(experiment_dict.items())
while idx < len(experiment_dict.items()):
    pvc_dict: PVCStatus = get_pvc_status()
    while len(pvc_dict.available) == 0:
        pvc_dict: PVCStatus = get_pvc_status()
        time.sleep(2)

    # Select the PVC that has been used the least number of times
    pvc_name = min(pvc_dict.available, key=lambda pvc: pvc_usage[pvc])
    pvc_dict.available.remove(pvc_name)
    pvc_dict.in_use.append(pvc_name)

    # Increment the usage count for the selected PVC
    pvc_usage[pvc_name] += 1
    gpu_type = None
    while gpu_type is None:
        gpu_type = get_gpu_type_to_use()
        job_succesfully_launched = False

    while not job_succesfully_launched:
        name, command = experiment_list[idx]

        if "fs" in name:
            gpu_type = "NVIDIA-A100-SXM4-80GB"

        job = KubernetesJob(
            name=f"{name}",
            image="ghcr.io/antreasantoniou/gate:0.8.8",
            command=["/bin/bash", "-c", "--"],
            args=[f"{command}"],
            gpu_type="nvidia.com/gpu",
            gpu_product=gpu_type,
            shm_size="100G",  # this is key for pytorch dataloaders and other operations that need access to shared memory (RAM) under the /dev/shm directory
            gpu_limit=1,
            backoff_limit=4,
            volume_mounts={
                "gate-disk": {
                    "pvc": pvc_name,
                    "mountPath": "/data/",
                },
            },
            env_vars=env_vars,
            job_deadlineseconds=3600 * 2 * 1,
        )

        job_yaml = job.generate_yaml()
        print(
            f"Attemping to launch job {name} on {gpu_type} with PVC {pvc_name}"
        )
        try:
            result = job.run()
            job_succesfully_launched = result.returncode == 0
        except Exception as e:
            logger.info(f"Job {name} failed with error: {e}")
        idx += 1

    time.sleep(2)
