# Example usage:
# `python example_pod.py`
# Expected output:
# should print the pod yaml and run the pod on the cluster

# running `kubectl logs -f pod/pod-test-info-40gb-full-<unique_id>`
# should show the disk usage information

# make sure to delete the pod after running the example
# `kubectl delete pod pod-test-info-40gb-full-<unique_id>`

import time

from kubejobs.pods import KubernetesPod

# unique id generated using time
unique_id = time.strftime("%Y%m%d")

pod = KubernetesPod(
    name=f"pod-test-info-40gb-full-{unique_id}",
    image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
    command=["/bin/bash"],
    args=["-c", "df -h"],
    gpu_type="nvidia.com/gpu",
    gpu_product="NVIDIA-A100-SXM4-40GB",
    gpu_limit=1,
    cpu_request=1,
    ram_request="1Gi",
    volume_mounts={
        "nfs": {"mountPath": "/nfs", "server": "10.24.1.255", "path": "/"}
    },
)

pod_yaml = pod.generate_yaml()
print(pod_yaml)
pod.run()
