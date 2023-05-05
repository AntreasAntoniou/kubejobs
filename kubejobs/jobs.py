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
        command: list,
        args: list,
        gpu_type: str,
        gpu_product: str,
        gpu_limit: int,
        backoff_limit: int,
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
            container["resources"]["limits"]["memory"] = self.shm_size
            container["resources"]["requests"] = {"memory": self.shm_size}
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
                    {"name": mount_name, "mountPath": mount_data["mountPath"]}
                )

        return container

    def generate_yaml(self):
        container = {
            "name": self.name,
            "image": self.image,
            "command": self.command,
            "args": self.args,
            "resources": {"limits": {f"{self.gpu_type}": self.gpu_limit}},
            "volumeMounts": [],
        }

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
                        "nodeSelector": {
                            f"{self.gpu_type}.product": self.gpu_product
                        },
                        "containers": [container],
                        "restartPolicy": self.restart_policy,
                        "volumes": [],
                    }
                },
                "backoffLimit": self.backoff_limit,
            },
        }
        # Add shared memory volume if shm_size is set
        if self.shm_size:
            job["spec"]["template"]["spec"]["volumes"].append(
                {"name": "dshm", "emptyDir": {"medium": "Memory"}}
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
        """Run the Kubernetes Job using the generated YAML spec."""
        config.load_kube_config()
        batch_api = client.BatchV1Api()

        job = self.generate_yaml()

        # Create the Kubernetes Job
        namespace = job.get("metadata", {}).get("namespace", "default")
        created_job = batch_api.create_namespaced_job(
            namespace=namespace, body=job
        )
        print(f"Job {self.name} created in namespace {namespace}")

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


# Example usage:
job = KubernetesJob(
    name="node-info-80gb-full",
    image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
    command=["/bin/bash"],
    args=["-c", "ls"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-80GB",
    gpu_limit=2,
    backoff_limit=4,
    volume_mounts={"node-info-80gb-full": {"mountPath": "/node-info"}},
)

job_yaml = job.generate_yaml()
print(job_yaml)
