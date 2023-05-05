# KubeJobs

KubeJobs is a Python library that simplifies the creation and management of Kubernetes Jobs. It provides an easy-to-use interface for running experiments, tasks, and other workloads on Kubernetes clusters.

## Features

- Easy creation and management of Kubernetes Jobs through Python code.
- Supports GPU selection, shared memory size configuration, environment variables, and volume mounts.
- Initialize the KubernetesJob class using command-line arguments with Google Fire.
- Automatically generates YAML files for Kubernetes Jobs.

## Installation

Install KubeJobs using pip:

pip install git+https://github.com/AntreasAntoniou/kubejobs.git

## Usage

Here's a basic example of how to use KubeJobs:

```python
from kubejobs import KubernetesJob

kubernetes_job = KubernetesJob(
    name="node-info",
    image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
    command=["/bin/bash"],
    args=["-c", "ls"],
    gpu_type="nvidia.com/gpu",
    gpu_limit=1,
    backoff_limit=4,
)

kubernetes_job.run()
```

For more detailed examples and usage information, please refer to the official documentation.

##Contributing

Contributions are welcome! If you'd like to contribute, please:

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Commit your changes and push them to your fork
4. Open a pull request

##License

KubeJobs is released under the MIT [License](LICENSE).