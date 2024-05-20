import logging
import os
import subprocess
from typing import List, Optional

import yaml
from kubernetes import config

from kubejobs.jobs import fetch_user_info

logger = logging.getLogger(__name__)
MAX_CPU = 192
MAX_RAM = 890
MAX_GPU = 8


class KubernetesPod:
    """
    A class for generating Kubernetes Pod YAML configurations.

    Attributes:
        name (str): Name of the pod and associated resources.
        image (str): Container image to use for the pod.
        command (List[str], optional): Command to execute in the container. Defaults to None.
        args (List[str], optional): Arguments for the command. Defaults to None.
        cpu_request (str, optional): Amount of CPU to request. For example, "500m" for half a CPU. Defaults to None. Max is 192 CPUs.
        ram_request (str, optional): Amount of RAM to request. For example, "1Gi" for 1 gibibyte. Defaults to None. Max is 890 GB.
        storage_request (str, optional): Amount of storage to request. For example, "10Gi" for 10 gibibytes. Defaults to None.
        gpu_type (str, optional): Type of GPU resource, e.g. "nvidia.com/gpu". Defaults to None.
        gpu_product (str, optional): GPU product, e.g. "NVIDIA-A100-SXM4-80GB". Defaults to None.
        gpu_limit (int, optional): Number of GPU resources to allocate. Defaults to None.
        restart_policy (str, optional): Restart policy for the pod, default is "Never".
        shm_size (str, optional): Size of shared memory, e.g. "2Gi". If not set, defaults to None.
        secret_env_vars (dict, optional): Dictionary of secret environment variables. Defaults to None.
        env_vars (dict, optional): Dictionary of normal (non-secret) environment variables. Defaults to None.
        volume_mounts (dict, optional): Dictionary of volume mounts. Defaults to None.
        namespace (str, optional): Namespace of the pod. Defaults to None.
        image_pull_secret (str, optional): Name of the image pull secret. Defaults to None.
    """

    def __init__(
        self,
        name: str,
        image: str,
        command: List[str] = None,
        args: Optional[List[str]] = None,
        cpu_request: Optional[str] = None,
        ram_request: Optional[str] = None,
        storage_request: Optional[str] = None,
        gpu_type: Optional[str] = None,
        gpu_product: Optional[str] = None,
        gpu_limit: Optional[int] = None,
        restart_policy: str = "Never",
        shm_size: Optional[str] = None,
        secret_env_vars: Optional[dict] = None,
        env_vars: Optional[dict] = None,
        volume_mounts: Optional[dict] = None,
        privileged_security_context: bool = False,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        labels: Optional[dict] = None,
        annotations: Optional[dict] = None,
        namespace: Optional[str] = None,
        image_pull_secret: Optional[str] = None,
        kueue_queue_name: str = "informatics-user-queue",
    ):
        self.name = name
        self.image = image
        self.command = command
        self.args = args
        self.cpu_request = cpu_request
        self.ram_request = ram_request
        self.storage_request = storage_request
        self.gpu_type = gpu_type
        self.gpu_product = gpu_product
        self.kueue_queue_name = kueue_queue_name

        self.gpu_limit = gpu_limit
        self.restart_policy = restart_policy
        self.shm_size = (
            shm_size
            if shm_size is not None
            else (
                ram_request
                if ram_request is not None
                else f"{MAX_RAM // (MAX_GPU - gpu_limit + 1)}G"
            )
        )
        self.secret_env_vars = secret_env_vars
        self.env_vars = env_vars
        self.volume_mounts = volume_mounts
        self.privileged_security_context = privileged_security_context

        self.user_name = user_name or os.environ.get("USER", "unknown")
        self.user_email = user_email  # This is now a required field.

        self.labels = {
            "eidf/user": self.user_name,
            "kueue.x-k8s.io/queue-name": self.kueue_queue_name,
        }

        if labels is not None:
            self.labels.update(labels)

        self.annotations = {"eidf/user": self.user_name}
        if user_email is not None:
            self.annotations["eidf/email"] = user_email

        if annotations is not None:
            self.annotations.update(annotations)

        self.user_info = fetch_user_info()
        self.annotations.update(self.user_info)
        logger.info(f"labels {self.labels}")
        logger.info(f"annotations {self.annotations}")

        self.namespace = namespace
        self.image_pull_secret = image_pull_secret

    def _add_shm_size(self, container: dict):
        """Adds shared memory volume if shm_size is set."""
        if self.shm_size:
            container["volumeMounts"].append(
                {"name": "dshm", "mountPath": "/dev/shm"}
            )
        return container

    def _add_env_vars(self, container: dict):
        """Adds secret and normal environment variables to the container."""
        container["env"] = []
        if self.secret_env_vars or self.env_vars:
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

        # Always export the POD_NAME environment variable
        container["env"].append(
            {
                "name": "POD_NAME",
                "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}},
            }
        )

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

    def _add_privileged_security_context(self, container: dict):
        """Adds privileged security context to the container."""
        if self.privileged_security_context:
            container["securityContext"] = {
                "privileged": True,
            }

        return container

    def generate_yaml(self):
        container = {
            "name": self.name,
            "image": self.image,
            "imagePullPolicy": "Always",
            "volumeMounts": [],
            "resources": {
                "requests": {},
                "limits": {},
            },
        }

        if self.command is not None:
            container["command"] = self.command

        if self.args is not None:
            container["args"] = self.args

        if not (
            self.gpu_type is None
            or self.gpu_limit is None
            or self.gpu_product is None
        ):
            container["resources"] = {
                "limits": {f"{self.gpu_type}": self.gpu_limit}
            }

        container = self._add_shm_size(container)
        container = self._add_env_vars(container)
        container = self._add_volume_mounts(container)
        container = self._add_privileged_security_context(container)

        if (
            self.cpu_request is not None
            or self.ram_request is not None
            or self.storage_request is not None
        ):
            if "resources" not in container:
                container["resources"] = {"requests": {}}

            if "requests" not in container["resources"]:
                container["resources"]["requests"] = {}

        if self.cpu_request is not None:
            container["resources"]["requests"]["cpu"] = self.cpu_request
            container["resources"]["limits"]["cpu"] = self.cpu_request

        if self.ram_request is not None:
            container["resources"]["requests"]["memory"] = self.ram_request
            container["resources"]["limits"]["memory"] = self.ram_request

        if self.storage_request is not None:
            container["resources"]["requests"][
                "storage"
            ] = self.storage_request

        if self.gpu_type is not None and self.gpu_limit is not None:
            container["resources"]["limits"][
                f"{self.gpu_type}"
            ] = self.gpu_limit

        pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": self.name,
                "labels": self.labels,  # Add labels here
                "annotations": self.annotations,  # Add metadata here
            },
            "spec": {
                "containers": [container],
                "restartPolicy": self.restart_policy,
                "volumes": [],
            },
        }

        if self.namespace:
            pod["metadata"]["namespace"] = self.namespace

        if not (
            self.gpu_type is None
            or self.gpu_limit is None
            or self.gpu_product is None
        ):
            pod["spec"]["nodeSelector"] = {
                f"{self.gpu_type}.product": self.gpu_product
            }

        # Add shared memory volume if shm_size is set
        if self.shm_size:
            pod["spec"]["volumes"].append(
                {
                    "name": "dshm",
                    "emptyDir": {
                        "medium": "Memory",
                        "sizeLimit": self.shm_size,
                    },
                }
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
                if "server" in mount_data:
                    volume["nfs"] = {
                        "server": mount_data["server"],
                        "path": mount_data["path"],
                    }

                pod["spec"]["volumes"].append(volume)

        if self.image_pull_secret:
            pod["spec"]["imagePullSecrets"] = [
                {"name": self.image_pull_secret}
            ]

        return yaml.dump(pod)

    def run(self):
        config.load_kube_config()

        pod_yaml = self.generate_yaml()

        # Save the generated YAML to a temporary file
        with open("temp_pod.yaml", "w") as temp_file:
            temp_file.write(pod_yaml)

        # Run the kubectl command with --validate=False
        cmd = ["kubectl", "apply", "-f", "temp_pod.yaml"]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Remove the temporary file
            os.remove("temp_pod.yaml")
            return result.returncode
        except subprocess.CalledProcessError as e:
            logger.info(
                f"Command '{' '.join(cmd)}' failed with return code {e.returncode}."
            )
            logger.info(f"Stdout:\n{e.stdout}")
            logger.info(f"Stderr:\n{e.stderr}")
            # Remove the temporary file
            os.remove("temp_pod.yaml")
            return e.returncode  # return the exit code
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred while running '{' '.join(cmd)}'."
            )  # This logs the traceback too
            # Remove the temporary file
            os.remove("temp_pod.yaml")
            return 1  # return the exit code
