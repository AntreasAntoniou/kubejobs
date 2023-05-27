# Example usage:
import time
from tqdm.auto import tqdm

from kubejobs import KubernetesJob, create_jobs_for_experiments, create_pvc
from kubejobs.experiments.pvc_status import PVCStatus, get_pvc_status


env_vars = dict()


pvc_dict = get_pvc_status()

experiment_dict = {"name": "command"}

for name, command in tqdm(experiment_dict.items()):
    pvc_dict: PVCStatus = get_pvc_status()
    while len(pvc_dict.in_use) >= 30:
        time.sleep(30)
        pvc_dict = get_pvc_status()

    if len(pvc_dict.available) > 0:
        pvc_name = pvc_dict.available.pop()
        pvc_dict.in_use.append(pvc_name)
    else:
        print("No available PVCs, launching new PVC")
        pvc_dict = get_pvc_status()
        pvc_name = f"gate-pvc-{len(pvc_dict.in_use) + len(pvc_dict.available)}"
        pvc_name = create_pvc(
            pvc_name=pvc_name, storage="2Ti", access_modes="ReadWriteOnce"
        )

    job = KubernetesJob(
        name=name,
        image="ghcr.io/antreasantoniou/gate:latest",
        command=["/bin/bash", "-c", "--"],
        args=[f"{command}"],
        gpu_type="nvidia.com/gpu",
        gpu_product="NVIDIA-A100-SXM4-40GB",
        shm_size="200",  # "200G" is the maximum value for shm_size
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
    job.run()
    time.sleep(2)
