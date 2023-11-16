import json
import logging
import os
import random
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

import fire
from rich.logging import RichHandler

from kubejobs.experiments.pvc_status import PVCStatus, get_pvc_status
from kubejobs.jobs import KubernetesJob, create_pvc
from kubejobs.useful_single_liners.count_gpu_usage_general import (
    GPU_DETAIL_DICT,
    count_gpu_usage,
)

logger = logging.getLogger("kubejobs")
logger.setLevel(logging.INFO)
handler = RichHandler(markup=True)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


def get_gpu_type_to_use(gpu_types_to_use: List[str]) -> Optional[str]:
    available_gpus = count_gpu_usage().get(
        "Informatics Allowance Available", {}
    )
    available_gpu_types = [
        gpu_type
        for gpu_type in gpu_types_to_use
        if available_gpus.get(gpu_type, 0) > 0
    ]
    return random.choice(available_gpu_types) if available_gpu_types else None


def setup_pvcs(num_pvcs: int, pvc_storage: str, pvc_access_modes: str) -> None:
    for i in range(num_pvcs):
        pvc_name = f"gate-pvc-{i}"
        create_pvc(
            pvc_name, storage=pvc_storage, access_modes=pvc_access_modes
        )


def parse_commands_input(input_data: str) -> Dict[str, Any]:
    try:
        # Attempt to parse the input as JSON
        data = json.loads(input_data)
        if isinstance(data, dict):
            # If it's a dictionary, use it as-is
            return data
        elif isinstance(data, list):
            # If it's a list, generate a dictionary with auto-generated names
            return {f"exp-{i+1:03d}": cmd for i, cmd in enumerate(data)}
    except json.JSONDecodeError:
        # If JSON parsing fails, treat the input as a newline-separated list of commands
        return {
            f"exp-{i+1:03d}": cmd
            for i, cmd in enumerate(input_data.strip().split("\n"))
        }


def launch_jobs(
    experiments: Dict[str, str],
    num_pvcs: int,
    max_concurrent_jobs: int,
    pvc_storage: str,
    pvc_access_modes: str,
    gpu_types_to_use: List[str],
    env_vars: Optional[Dict[str, str]] = None,
) -> None:
    pvc_usage = defaultdict(int)
    setup_pvcs(num_pvcs, pvc_storage, pvc_access_modes)
    pvc_status = get_pvc_status()

    for exp_name, command in experiments.items():
        while len(pvc_status.in_use) >= max_concurrent_jobs:
            logger.info(
                "Maximum number of concurrent jobs reached, waiting..."
            )
            time.sleep(5)
            pvc_status = get_pvc_status()

        pvc_name = min(pvc_status.available, key=lambda p: pvc_usage[p])
        pvc_usage[pvc_name] += 1
        gpu_type = get_gpu_type_to_use(gpu_types_to_use)

        job = KubernetesJob(
            name=exp_name.lower(),
            image="ghcr.io/antreasantoniou/gate:latest",
            command=["/bin/bash", "-c", "--"],
            args=[command],
            gpu_type="nvidia.com/gpu",
            gpu_product=gpu_type,
            gpu_limit=1,
            backoff_limit=4,
            volume_mounts={
                "gate-disk": {"pvc": pvc_name, "mountPath": "/data/"}
            },
            env_vars=env_vars,
            job_deadlineseconds=None,
            ram_request="80G",
            cpu_request=16,
        )

        try:
            job_success = job.run() == 0
            logger.info(
                f"Launched job '{exp_name}' on '{gpu_type}' with PVC '{pvc_name}'. Success: {job_success}"
            )
        except Exception as e:
            logger.error(f"Job '{exp_name}' failed with error: {e}")

        time.sleep(2)


def main(
    num_pvcs: int = 50,
    max_concurrent_jobs: int = 10,
    pvc_storage: str = "4Ti",
    pvc_access_modes: str = "ReadWriteOnce",
    env_vars: Optional[Dict[str, str]] = None,
) -> None:
    input_data = sys.stdin.read() if not sys.stdin.isatty() else None
    if not input_data:
        logger.error("No commands provided to run.")
        sys.exit(1)

    experiments = parse_commands_input(input_data)
    gpu_types_to_use = set(list(GPU_DETAIL_DICT.keys())[:1])

    ENV_VARS = {
        "WANDB_API_KEY": os.getenv("WANDB_API_KEY"),
        "WANDB_ENTITY": os.getenv("WANDB_ENTITY"),
        "WANDB_PROJECT": os.getenv("WANDB_PROJECT"),
        "KAGGLE_USERNAME": os.getenv("KAGGLE_USERNAME"),
        "KAGGLE_KEY": os.getenv("KAGGLE_KEY"),
        "PYTEST_DIR": os.getenv("PYTEST_DIR"),
        "EXPERIMENT_NAME": os.getenv("EXPERIMENT_NAME"),
        "HF_USERNAME": os.getenv("HF_USERNAME"),
        "HF_TOKEN": os.getenv("HF_TOKEN"),
        "HF_CACHE_DIR": os.getenv("HF_CACHE_DIR"),
        "TOKENIZERS_PARALLELISM": os.getenv("TOKENIZERS_PARALLELISM"),
        "CODE_DIR": os.getenv("CODE_DIR"),
        "PROJECT_DIR": os.getenv("PROJECT_DIR"),
        "EXPERIMENT_NAME_PREFIX": os.getenv("EXPERIMENT_NAME_PREFIX"),
        "EXPERIMENTS_DIR": os.getenv("EXPERIMENTS_DIR"),
        "EXPERIMENT_DIR": os.getenv("EXPERIMENT_DIR"),
        "DATASET_DIR": os.getenv("DATASET_DIR"),
        "MODEL_DIR": os.getenv("MODEL_DIR"),
    }

    launch_jobs(
        experiments=experiments,
        num_pvcs=num_pvcs,
        max_concurrent_jobs=max_concurrent_jobs,
        pvc_storage=pvc_storage,
        pvc_access_modes=pvc_access_modes,
        gpu_types_to_use=gpu_types_to_use,
        env_vars=env_vars or ENV_VARS,
    )


if __name__ == "__main__":
    fire.Fire(main)
