import subprocess
import yaml
import json
import re


def get_gpu_usage():
    pods_info = json.loads(
        subprocess.check_output(["kubectl", "get", "pods", "-o", "json"])
    )

    gpu_usage = {}
    user_gpu_usage = {}
    for item in pods_info["items"]:
        pod_name = item["metadata"]["name"]
        user_name = item["metadata"]["annotations"]["kubernetes.io/created-by"]

        pod_info = json.loads(
            subprocess.check_output(
                ["kubectl", "describe", "pod", pod_name, "-o", "json"]
            )
        )
        for container in pod_info["spec"]["containers"]:
            gpu_request = (
                container["resources"]
                .get("requests", {})
                .get("nvidia.com/gpu")
            )
            gpu_model = pod_info["spec"]["nodeSelector"].get(
                "nvidia.com/gpu.product"
            )

            if gpu_model and gpu_request:
                gpu_usage[gpu_model] = gpu_usage.get(gpu_model, 0) + int(
                    gpu_request
                )
                user_gpu_usage[user_name] = user_gpu_usage.get(user_name, {})
                user_gpu_usage[user_name][gpu_model] = user_gpu_usage[
                    user_name
                ].get(gpu_model, 0) + int(gpu_request)

    return gpu_usage, user_gpu_usage


def dict_to_yaml(dictionary):
    return yaml.dump(dictionary, default_flow_style=False)


gpu_usage, user_gpu_usage = get_gpu_usage()

print("Overall GPU Usage:")
print(dict_to_yaml(gpu_usage))
print("\nUser Specific GPU Usage:")
print(dict_to_yaml(user_gpu_usage))
