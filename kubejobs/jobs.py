import os
import subprocess
from typing import List

import fire
import yaml
from kubernetes import client, config
from rich import print


class KubernetesJob:
    """
    A class for generating Kubernetes Job YAML configurations.

    Attributes:
        name (str): Name of the job and associated resources.
        image (str): Container image to use for the job.
        command (list): Command to execute in the container.
        args (list): Arguments for the command.
        gpu_type (str): Type of GPU resource, e.g. "nvidia.com/gpu".
        gpu_product (str): GPU product, e.g. "NVIDIA-A100-SXM4-80GB".
        gpu_limit (int): Number of GPU resources to allocate.
        backoff_limit (int): Maximum number of retries before marking job as failed.
        restart_policy (str): Restart policy for the job, default is "Never".
        shm_size (str): Size of shared memory, e.g. "2Gi". If not set, defaults to None.
        secret_env_vars (dict): Dictionary of secret environment variables.
        env_vars (dict): Dictionary of normal (non-secret) environment variables.
        volume_mounts (dict): Dictionary of volume mounts.

    Methods:
        generate_yaml() -> dict: Generate the Kubernetes Job YAML configuration.
    """

    def __init__(
        self,
        name: str,
        image: str,
        command: List[str] = None,
        args: List[str] = None,
        gpu_type: str = None,
        gpu_product: str = None,
        gpu_limit: int = None,
        backoff_limit: int = 4,
        restart_policy: str = "Never",
        shm_size: str = None,
        secret_env_vars: dict = None,
        env_vars: dict = None,
        volume_mounts: dict = None,
    ):
        self.name = name
        self.image = image
        self.command = command
        self.args = args
        self.gpu_type = gpu_type
        self.gpu_product = gpu_product
        self.gpu_limit = gpu_limit
        self.backoff_limit = backoff_limit
        self.restart_policy = restart_policy
        self.shm_size = shm_size
        self.secret_env_vars = secret_env_vars
        self.env_vars = env_vars
        self.volume_mounts = volume_mounts

    def _add_shm_size(self, container: dict):
        """Adds shared memory volume if shm_size is set."""
        if self.shm_size:
            # container["resources"]["limits"]["memory"] = self.shm_size
            # container["resources"]["requests"] = {"memory": self.shm_size}
            container["volumeMounts"].append(
                {"name": "dshm", "mountPath": "/dev/shm"}
            )
        return container

    def _add_env_vars(self, container: dict):
        """Adds secret and normal environment variables to the
        container."""
        if self.secret_env_vars or self.env_vars:
            container["env"] = []
            if self.secret_env_vars:
                for key, value in self.secret_env_vars.items():
                    container["env"].append(
                        {
                            "name": key,
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": value["secret_name"],
                                    "key": value["key"],
                                }
                            },
                        }
                    )

            if self.env_vars:
                for key, value in self.env_vars.items():
                    container["env"].append({"name": key, "value": value})

        return container

    def _add_volume_mounts(self, container: dict):
        """Adds volume mounts to the container."""
        if self.volume_mounts:
            for mount_name, mount_data in self.volume_mounts.items():
                container["volumeMounts"].append(
                    {
                        "name": mount_name,
                        "mountPath": mount_data["mountPath"],
                    }
                )

        return container

    def generate_yaml(self):
        container = {
            "name": self.name,
            "image": self.image,
            "command": self.command,
            "args": self.args,
            "volumeMounts": [],
        }

        if not (
            self.gpu_type is None
            or self.gpu_limit is None
            or self.gpu_product is None
        ):
            container["resources"] = {"limits": {f"{self.gpu_type}": self.gpu_limit}}
            

        container = self._add_shm_size(container)
        container = self._add_env_vars(container)
        container = self._add_volume_mounts(container)

        job = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": self.name},
            "spec": {
                "template": {
                    "spec": {
                        "containers": [container],
                        "restartPolicy": self.restart_policy,
                        "volumes": [],
                    }
                },
                "backoffLimit": self.backoff_limit,
            },
        }
        if not (
            self.gpu_type is None
            or self.gpu_limit is None
            or self.gpu_product is None
        ):
            job["spec"]["template"]["spec"]["nodeSelector"] = {
                f"{self.gpu_type}.product": self.gpu_product
            }
        # Add shared memory volume if shm_size is set
        if self.shm_size:
            job["spec"]["template"]["spec"]["volumes"].append(
                {"name": "dshm", "emptyDir": {"medium": "Memory", "sizeLimit": self.shm_size}}
            )

        # Add volumes for the volume mounts
        if self.volume_mounts:
            for mount_name, mount_data in self.volume_mounts.items():
                volume = {"name": mount_name}

                if "pvc" in mount_data:
                    volume["persistentVolumeClaim"] = {
                        "claimName": mount_data["pvc"]
                    }
                elif "emptyDir" in mount_data:
                    volume["emptyDir"] = {}
                # Add more volume types here if needed

                job["spec"]["template"]["spec"]["volumes"].append(volume)

        return yaml.dump(job)

    def run(self):
        config.load_kube_config()

        job_yaml = self.generate_yaml()

        # Save the generated YAML to a temporary file
        with open("temp_job.yaml", "w") as temp_file:
            temp_file.write(job_yaml)

        # Run the kubectl command with --validate=False
        cmd = ["kubectl", "apply", "-f", "temp_job.yaml", "--validate=False"]
        subprocess.run(cmd, check=True)

        # Remove the temporary file
        os.remove("temp_job.yaml")

    @classmethod
    def from_command_line(cls):
        """Create a KubernetesJob instance from command-line arguments
        and run the job."""
        fire.Fire(cls)


def create_jobs_for_experiments(commands: List[str], *args, **kwargs):
    """
    Creates and runs a Kubernetes Job for each command in the given list of commands.

    :param commands: A list of strings, where each string represents a command to be executed.
    :param args: Positional arguments to be passed to the KubernetesJob constructor.
    :param kwargs: Keyword arguments to be passed to the KubernetesJob constructor.

    :Example:

    .. code-block:: python

        from kubejobs import KubernetesJob

        commands = [
            "python experiment.py --param1 value1",
            "python experiment.py --param1 value2",
            "python experiment.py --param1 value3"
        ]

        create_jobs_for_experiments(
            commands,
            image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
            gpu_type="nvidia.com/gpu",
            gpu_limit=1,
            backoff_limit=4
        )
    """
    jobs = []
    for idx, command in enumerate(commands):
        job_name = f"{kwargs.get('name', 'experiment')}-{idx}"
        kubernetes_job = KubernetesJob(
            name=job_name,
            command=["/bin/bash"],
            args=["-c", command],
            *args,
            **kwargs,
        )
        kubernetes_job.run()
        jobs.append(kubernetes_job)

    return jobs


def create_pvc(
    pvc_name: str,
    storage: str,
    access_modes: list = None,
    namespace: str = "default",
):
    if access_modes is None:
        access_modes = ["ReadWriteOnce"]

    pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": pvc_name},
        "spec": {
            "accessModes": access_modes,
            "resources": {"requests": {"storage": storage}},
        },
    }

    config.load_kube_config()
    core_api = client.CoreV1Api()
    core_api.create_namespaced_persistent_volume_claim(
        namespace=namespace, body=pvc
    )


def create_pv(
    pv_name: str,
    storage: str,
    storage_class_name: str,
    access_modes: list,
    pv_type: str,
    namespace: str = "default",
    claim_name: str = None,
    local_path: str = None,
    fs_type: str = "ext4",
):
    """
    Create a PersistentVolume in the specified namespace with the specified type.

    :param pv_name: The name of the PersistentVolume.
    :param storage: The amount of storage for the PersistentVolume (e.g., "1500Gi").
    :param storage_class_name: The storage class name for the PersistentVolume.
    :param access_modes: A list of access modes for the PersistentVolume.
    :param pv_type: The type of PersistentVolume, either 'local' or 'gcePersistentDisk'.
    :param namespace: The namespace in which to create the PersistentVolume. Defaults to "default".
    :param claim_name: The name of the PersistentVolumeClaim to bind to the PersistentVolume.
    :param local_path: The path on the host for a local PersistentVolume. Required if pv_type is 'local'.
    :param fs_type: The filesystem type for the PersistentVolume. Defaults to "ext4".

    Example usage:

    .. code-block:: python

        create_pv("pv-instafluencer-data", "1500Gi", "sc-instafluencer-data", ["ReadOnlyMany"], "local",
                  claim_name="pvc-instafluencer-data", local_path="/mnt/data")
        # This will create a local PersistentVolume named "pv-instafluencer-data" with 1500Gi of storage,
        # "sc-instafluencer-data" storage class, ReadOnlyMany access mode, and a local path "/mnt/data".
    """

    if pv_type not in ["local", "node"]:
        raise ValueError(
            "pv_type must be either 'local' or 'gcePersistentDisk'"
        )

    if pv_type == "local" and not local_path:
        raise ValueError("local_path must be provided when pv_type is 'local'")

    pv = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {"name": pv_name},
        "spec": {
            "storageClassName": storage_class_name,
            "capacity": {"storage": storage},
            "accessModes": access_modes,
            "csi": {"driver": "pd.csi.storage.gke.io", "fsType": fs_type},
        },
    }

    if claim_name:
        pv["spec"]["claimRef"] = {"namespace": namespace, "name": claim_name}

    if pv_type == "local":
        pv["spec"]["hostPath"] = {"path": local_path}

    print(pv)
    config.load_kube_config()
    core_api = client.CoreV1Api()
    core_api.create_persistent_volume(body=pv)


if __name__ == "__main__":
    KubernetesJob.from_command_line()
