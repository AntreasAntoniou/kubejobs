import json
import subprocess


def main():
    get_pods_output = subprocess.check_output(
        ["kubectl", "get", "pods", "-o", "json"]
    )
    pod_data = json.loads(get_pods_output)

    pods_with_errors = []
    for pod in pod_data["items"]:
        container_statuses = pod["status"].get("containerStatuses", [])
        for container_status in container_statuses:
            state = container_status.get("state", {})
            terminated_state = state.get("terminated", {})
            if terminated_state.get("reason") == "Error":
                pods_with_errors.append(
                    (pod["metadata"]["namespace"], pod["metadata"]["name"])
                )

    with open("error_logs.txt", "w") as logs_file:
        for namespace, pod_name in pods_with_errors:
            try:
                log_output = subprocess.check_output(
                    ["kubectl", "logs", "-n", namespace, pod_name]
                )
                decoded_log_output = log_output.decode()

                logs_file.write(f"Namespace: {namespace}, Pod: {pod_name}\n")
                logs_file.write(decoded_log_output)
                logs_file.write("\n\n")
            except subprocess.CalledProcessError as e:
                print(
                    f"Error fetching logs for Pod: {pod_name} in Namespace: {namespace}"
                )


if __name__ == "__main__":
    main()
