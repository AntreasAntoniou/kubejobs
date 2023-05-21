import subprocess
import re


def get_pods():
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-o",
            "jsonpath='{.items[*].metadata.name}'",
        ],
        capture_output=True,
        text=True,
    )
    pods = result.stdout.strip("'").split(" ")
    return pods


def describe_pod(pod):
    result = subprocess.run(
        ["kubectl", "describe", "pod", pod], capture_output=True, text=True
    )
    return result.stdout


def extract_gpu_info(pod_description):
    model_pattern = re.compile(r"nvidia\.com/gpu\.product=(\S+)")
    count_pattern = re.compile(r"nvidia\.com/gpu:\s+(\d+)")

    model_match = model_pattern.search(pod_description)
    count_match = count_pattern.search(pod_description)

    gpu_model = model_match.group(1) if model_match else None
    gpu_count = int(count_match.group(1)) if count_match else None

    return gpu_model, gpu_count


def main():
    gpu_usage = {}
    for pod in get_pods():
        pod_description = describe_pod(pod)
        gpu_model, gpu_count = extract_gpu_info(pod_description)

        if gpu_model and gpu_count:
            if gpu_model not in gpu_usage:
                gpu_usage[gpu_model] = gpu_count
            else:
                gpu_usage[gpu_model] += gpu_count

    return gpu_usage


import yaml


def dict_to_yaml(dictionary):
    return yaml.dump(dictionary, default_flow_style=False)


if __name__ == "__main__":
    gpu_usage = main()
    print(dict_to_yaml(gpu_usage))
