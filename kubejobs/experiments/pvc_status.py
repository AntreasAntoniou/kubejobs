import re
import subprocess
from dataclasses import dataclass
from typing import List

from rich import print


@dataclass
class PVCStatus:
    available: List[str]
    in_use: List[str]


import json


def get_pvc_status():
    """
    This function returns a PVCStatus object containing the status of Persistent Volume Claims (PVCs) in a Kubernetes cluster.
    The PVCStatus has two attributes: 'available' and 'in-use', each containing a list of PVCs in the respective status.

    Returns:
        PVCStatus: A PVCStatus object with attributes 'available' and 'in-use', each containing a list of PVCs in the respective status.
    """

    # Function to sort PVCs by name and index
    def sort_key(pvc):
        if isinstance(pvc, str):
            match = re.match(r"([a-z-]+)-([0-9]+)", pvc, re.I)
            if match:
                name, index = match.groups()
                return name, int(index)
        return pvc, 0

    # Function to run a subprocess and return the stdout as a list
    def run_subprocess(command):
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.split()

    # Function to run a subprocess and return the stdout as a JSON object
    def run_subprocess_json(command):
        result = subprocess.run(command, capture_output=True, text=True)
        return json.loads(result.stdout)

    # Get all PVCs and Pods
    pvcs = run_subprocess(
        ["kubectl", "get", "pvc", "-o", "jsonpath={.items[*].metadata.name}"]
    )
    pods = run_subprocess_json(["kubectl", "get", "pods", "-o", "json"])

    # Create a dictionary to store PVC usage status
    pvc_usage = {pvc: False for pvc in pvcs}

    # Check each pod for PVC usage
    for pod in pods["items"]:
        if pod["status"]["phase"].lower() not in [
            "running",
            "containercreating",
            "pending",
        ]:
            continue
        for volume in pod["spec"].get("volumes", []):
            pvc = volume.get("persistentVolumeClaim")
            if pvc:
                pvc_name = pvc["claimName"]
                if pvc_name in pvc_usage:
                    pvc_usage[pvc_name] = True

    # Create a dictionary to store PVCs by usage status
    pvc_status = {"available": [], "in-use": []}

    # Populate the pvc_status dictionary
    for pvc, used in sorted(pvc_usage.items(), key=sort_key):
        if "gate" not in pvc:
            continue
        if used:
            pvc_status["in-use"].append(pvc)
        else:
            pvc_status["available"].append(pvc)

    # Return the pvc_status dictionary
    output = PVCStatus(
        available=pvc_status["available"],
        in_use=pvc_status["in-use"],
    )

    return output


if __name__ == "__main__":
    pvc_status = get_pvc_status()
    print(pvc_status)
