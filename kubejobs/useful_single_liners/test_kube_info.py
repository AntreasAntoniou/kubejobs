import os
from datetime import datetime
import yaml  # You can install it with pip install PyYAML

class KubernetesJob:

    def __init__(self, name):
        self.name = name  # Assume the Job name is passed during initialization
        self.metadata = {
            "username": os.getenv("USER", "unknown"),  # Fetch username
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Add a timestamp
            "host": os.uname()[1]  # Host machine details
        }

    def generate_yaml(self):
        # Define Kubernetes Job YAML as a Python dict
        job = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": self.name,
                "annotations": self.metadata  # Add metadata here
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "pi",
                                "image": "perl",
                                "command": ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
                            }
                        ],
                        "restartPolicy": "Never"
                    }
                }
            }
        }
        # Convert Python dict to YAML string
        yaml_str = yaml.dump(job, default_flow_style=False)
        return yaml_str

# Usage Example
if __name__ == '__main__':
    k8s_job = KubernetesJob(name="example-job")
    yaml_output = k8s_job.generate_yaml()
    print(yaml_output)
