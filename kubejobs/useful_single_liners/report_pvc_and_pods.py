import json
import subprocess

from rich.console import Console
from rich.table import Table
from tqdm.auto import tqdm


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

# Create a console instance
console = Console()

# Prepare data for the table
data = []
for pod in tqdm(pods):
    # Get the PVC name associated with the pod
    pod_json = run_command(f"kubectl get pod {pod} -o json")
    pod_data = json.loads(pod_json)
    volumes = pod_data["spec"]["volumes"]

    pvc_names = []
    for volume in volumes:
        if "persistentVolumeClaim" in volume:
            pvc_names.append(volume["persistentVolumeClaim"]["claimName"])

    for pvc_name in pvc_names:
        data.append((pvc_name, pod))

# Sort data by PVC name
data.sort(key=lambda x: x[0])

# Add index to the data
data = [
    (str(idx), pvc_name, pod)
    for idx, (pvc_name, pod) in enumerate(data, start=1)
]

# Calculate the maximum length of the strings in each column
max_lengths = [max(len(x) for x in col) for col in zip(*data)]

# Create a table
table = Table(show_header=True, header_style="bold cyan")
table.add_column("idx", style="white", width=max_lengths[0])
table.add_column("PVC Name", style="white", width=max_lengths[1])
table.add_column("Pod Name", style="white", width=max_lengths[2])

# Add rows to the table
for row in data:
    table.add_row(*row)

# Print the table
console.print(table)
