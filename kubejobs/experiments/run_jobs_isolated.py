import json
import logging
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
            job_deadlineseconds=7200,
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
    gpu_types_to_use = set(list(GPU_DETAIL_DICT.keys())[:2])

    ENV_VARS = {
        "NEPTUNE_API_TOKEN": "eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiJkOTFjMTY5Zi03ZGUwLTQ4ODYtYWI0Zi1kZDEzNjlkMGI5ZjQifQ==",
        "NEPTUNE_PROJECT": "MachineLearningBrewery/gate-exp-0-8-6",
        "NEPTUNE_ALLOW_SELF_SIGNED_CERTIFICATE": "TRUE",
        "WANDB_API_KEY": "821661c6ee1657a2717093701ab76574ae1a9be0",
        "WANDB_ENTITY": "machinelearningbrewery",
        "WANDB_PROJECT": "gate-0-8-12",
        "KAGGLE_USERNAME": "antreasantoniou",
        "KAGGLE_KEY": "d14aab63e71334cfa118bd5251bf85da",
        "PYTEST_DIR": "/data/",
        "EXPERIMENT_NAME": "gate-0-9-0-exp",
        "HF_USERNAME": "Antreas",
        "HF_TOKEN": "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",
        "HF_CACHE_DIR": "/data/",
        "TOKENIZERS_PARALLELISM": "false",
        "CODE_DIR": "/app/",
        "PROJECT_DIR": "/app/",
        "EXPERIMENT_NAME_PREFIX": "gate-0-8-12",
        "EXPERIMENTS_DIR": "/data/experiments/",
        "EXPERIMENT_DIR": "/data/experiments/",
        "DATASET_DIR": "/data/",
        "MODEL_DIR": "/data/model/",
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
