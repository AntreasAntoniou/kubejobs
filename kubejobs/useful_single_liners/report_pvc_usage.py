import re
import subprocess

from rich import print

# Get all PVCs
get_pvcs = subprocess.run(
    ["kubectl", "get", "pvc", "-o", "jsonpath={.items[*].metadata.name}"],
    capture_output=True,
    text=True,
)
pvcs = get_pvcs.stdout.split()

# Create a dictionary to store PVC usage status
pvc_usage = {pvc: False for pvc in pvcs}

# Get all Pods
get_pods = subprocess.run(
    ["kubectl", "get", "pods", "-o", "jsonpath={.items[*].metadata.name}"],
    capture_output=True,
    text=True,
)
pods = get_pods.stdout.split()

# Check each pod for PVC usage
for pod in pods:
    describe_pod = subprocess.run(
        ["kubectl", "describe", "pod", pod], capture_output=True, text=True
    )
    for pvc in pvcs:
        if pvc in describe_pod.stdout:
            pvc_usage[pvc] = True


# Function to sort PVCs by name and index
def sort_key(pvc):
    if isinstance(pvc, str):
        match = re.match(r"([a-z-]+)-([0-9]+)", pvc, re.I)
        if match:
            name, index = match.groups()
            return name, int(index)
    return pvc, 0


# Print PVC usage status sorted by PVC name and index
for pvc, used in sorted(pvc_usage.items(), key=sort_key):
    if "gate" not in pvc:
        continue
    if used:
        print(f"[green]PVC {pvc} is in use[/green]")
    else:
        print(f"[red]PVC {pvc} is not in use[/red]")
