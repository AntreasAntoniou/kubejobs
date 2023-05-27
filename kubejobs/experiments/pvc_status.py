from dataclasses import dataclass
import subprocess
import re
from typing import List


@dataclass
class PVCStatus:
    available: List[str]
    in_use: List[str]


def get_pvc_status():
    """
    This function returns a dictionary containing the status of Persistent Volume Claims (PVCs) in a Kubernetes cluster.
    The dictionary has two keys: 'available' and 'in-use', each containing a list of PVCs in the respective status.

    Returns:
        dict: A dictionary with keys 'available' and 'in-use', each containing a list of PVCs in the respective status.
    """

    # Function to sort PVCs by name and index
    def sort_key(pvc):
        match = re.match(r"([a-z-]+)-([0-9]+)", pvc, re.I)
        if match:
            name, index = match.groups()
            return name, int(index)
        return pvc, 0

    # Function to run a subprocess and return the stdout as a list
    def run_subprocess(command):
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.split()

    # Get all PVCs and Pods
    pvcs = run_subprocess(
        ["kubectl", "get", "pvc", "-o", "jsonpath={.items[*].metadata.name}"]
    )
    pods = run_subprocess(
        ["kubectl", "get", "pods", "-o", "jsonpath={.items[*].metadata.name}"]
    )

    # Create a dictionary to store PVC usage status
    pvc_usage = {pvc: False for pvc in pvcs}

    # Check each pod for PVC usage
    for pod in pods:
        describe_pod = subprocess.run(
            ["kubectl", "describe", "pod", pod], capture_output=True, text=True
        ).stdout
        for pvc in pvcs:
            if pvc in describe_pod:
                pvc_usage[pvc] = True

    # Create a dictionary to store PVCs by usage status
    pvc_status = {"available": [], "in-use": []}

    # Populate the pvc_status dictionary
    for pvc, used in sorted(pvc_usage.items(), key=sort_key):
        if used:
            pvc_status["in-use"].append(pvc)
        else:
            pvc_status["available"].append(pvc)

    # Return the pvc_status dictionary
    return PVCStatus(
        available=pvc_status["available"], in_use=pvc_status["in-use"]
    )
