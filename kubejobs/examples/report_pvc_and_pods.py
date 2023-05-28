import subprocess
import json


# Function to execute a shell command and return the output
def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error:
        raise Exception("Error executing command: " + command)
    return output.decode("utf-8")


# Get the list of pods
pods_json = run_command(f"kubectl get pods  -o json")
pods_data = json.loads(pods_json)
pods = [pod["metadata"]["name"] for pod in pods_data["items"]]

print("POD NAME\tPVC NAME")

# Loop through the list of pods
for pod in pods:
    # Get the PVC name associated with the pod
    pod_json = run_command(f"kubectl get pod {pod} -o json")
    pod_data = json.loads(pod_json)
    volumes = pod_data["spec"]["volumes"]

    pvc_names = []
    for volume in volumes:
        if "persistentVolumeClaim" in volume:
            pvc_names.append(volume["persistentVolumeClaim"]["claimName"])

    print(f"{pod}\t{', '.join(pvc_names)}")
