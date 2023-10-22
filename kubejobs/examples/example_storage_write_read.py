from rich import print

from kubejobs.jobs import KubernetesJob as Job
from kubejobs.jobs import create_pvc

# Create PVC if not created
pvc_name = "datasets-pvc-0"

# Write a sample file to the PVC
write_job = Job(
    name="write-sample-file",
    image="ubuntu:20.04",
    command=["/bin/bash", "-c"],
    args=["echo 'Hello, World!' > /mnt/data/sample.txt"],
    volume_mounts={
        "dataset-disk": {
            "pvc": "datasets-pvc-0",
            "mountPath": "/mnt/data",
        }
    },
)
print(write_job.generate_yaml())
write_job.run()

# Read and inspect the sample file from the PVC
read_job = Job(
    name="read-sample-file",
    image="ubuntu:20.04",
    command=["/bin/bash", "-c"],
    args=["cat /mnt/data/sample.txt"],
    volume_mounts={
        "dataset-disk": {
            "pvc": "datasets-pvc-0",
            "mountPath": "/mnt/data",
        }
    },
)
print(read_job.generate_yaml())
read_job.run()
