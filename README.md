# KubeJobs: Pythonic Kubernetes for MLOps and ML Research 🚀

**Are you...**
- Engaged in MLOps or ML research? :mag:
- Frustrated by YAML and kubectl complexities? :triumph:
- Wishing for a Python-Kubernetes blend in your ML pipelines? :sparkling_heart:

**Discover KubeJobs:**
- **Python-Powered Kubernetes:** Write Kubernetes operations in Python, get rid of YAML files. 🎉
- **MLOps Made Magical:** Manage Kubernetes Jobs, PVs, PVCs effortlessly, tailored for ML workflows. 🪄
- **Research Reading, Writing Kubernetes:** Set up and run multiple jobs for varied experiment parameters systematically. 📚
- **Visualized Data:** Track Kubernetes job and pod information via a Streamlit-powered web interface. 🖥️


**Kubejobs** is a Python package for creating and running Kubernetes Jobs, Persistent Volumes (PVs), and Persistent Volume Claims (PVCs). This package simplifies the process of deploying and managing jobs, PVs, and PVCs on Kubernetes, making it easier for users without Kubernetes experience to get started.

## Features

- Easy creation and management of Kubernetes Jobs through Python code.
- Supports GPU selection, shared memory size configuration, environment variables, and volume mounts.
- Initialize the KubernetesJob class using command-line arguments with Google Fire.
- Automatically generates YAML files for Kubernetes Jobs.

## Installation

Install KubeJobs using pip:

```
pip install git+https://github.com/AntreasAntoniou/kubejobs.git
```

## Usage

### KubernetesJob

The `KubernetesJob` class helps you create a Kubernetes Job, generate its YAML configuration, and run the job. Kubernetes Jobs are useful for running short-lived, one-off tasks in your cluster.

```python
from kubejobs.jobs import KubernetesJob

# Create a Kubernetes Job with a name, container image, and command
job = KubernetesJob(
    name="my-job",
    image="ubuntu:20.04",
    command=["/bin/bash", "-c", "echo 'Hello, World!'"],
)

# Generate the YAML configuration for the Job
print(job.generate_yaml())

# Run the Job on the Kubernetes cluster
job.run()
```

### create_jobs_for_experiments

The create_jobs_for_experiments function allows you to create and run a series of Kubernetes Jobs for a list of commands. This can be helpful for running multiple experiments or tasks with different parameters in parallel.


```python
from kubejobs.jobs import create_jobs_for_experiments

# List of commands to run as separate Kubernetes Jobs
commands = [
    "python experiment.py --param1 value1",
    "python experiment.py --param1 value2",
    "python experiment.py --param1 value3",
]

# Create and run Kubernetes Jobs for each command in the list
create_jobs_for_experiments(
    commands,
    image="nvcr.io/nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04",
    gpu_type="nvidia.com/gpu",  # Request GPU resources
    gpu_limit=1,                # Number of GPU resources to allocate
    backoff_limit=4,            # Maximum number of retries before marking job as failed
)
```

### create_pvc

The create_pvc function helps you create a Persistent Volume Claim (PVC) in your Kubernetes cluster. PVCs are used to request storage resources from your cluster, allowing your applications to store and retrieve data.

```python
from kubejobs.jobs import create_pvc

# Create a PVC with a name, storage size, and access mode
create_pvc("my-pvc", "5Ti", access_modes=["ReadWriteOnce"])
```

### create_pv

The create_pv function helps you create a Persistent Volume (PV) in your Kubernetes cluster. PVs represent physical storage resources in a cluster, which can be consumed by PVCs. This allows you to manage storage resources independently from applications that use them.

```python
from kubejobs.jobs import create_pv

# Create a PV with a name, storage size, storage class, access mode, and other properties
create_pv(
    pv_name="my-pv",
    storage="1500Gi",
    storage_class_name="my-storage-class",
    access_modes=["ReadOnlyMany"],
    pv_type="local",          # Type of Persistent Volume, either 'local' or 'gcePersistentDisk'
    claim_name="my-pvc",      # Name of the PVC to bind to the PV
    local_path="/mnt/data",   # Path on the host for a local PV (required when pv_type is 'local')
)
```

## Utilities

### `web_pod_info.py`

#### Overview

`web_pod_info.py` fetches, processes, and displays Kubernetes pod information. It can produce both console-based and web-based outputs using the Rich and Streamlit libraries, respectively.

#### Features

- Fetch Kubernetes Pod information from a specific namespace.
- Display the fetched data in a table format in the console.
- Utilize Streamlit to render the data in a web interface.

#### Usage

##### Command Line

Run the script from the command line with an optional `namespace` parameter:

```bash
python kubejobs/web_pod_info.py --namespace=<your-namespace>
```

##### With Streamlit

Run the script as above, and then navigate to the Streamlit URL displayed in the console to view the web table.

```bash
streamlit run kubejobs/web_pod_info.py
```

### `web_job_info.py`

#### Overview

`web_job_info.py` is a utility script for fetching and displaying information about Kubernetes jobs. It uses the Rich library for console-based output and Streamlit for web-based visualization.

#### Features

- Fetch Kubernetes Job information from a specific namespace.
- Display the fetched data in a table format in the console.
- Utilize Streamlit to render the data in a web interface.

#### Usage

##### Command Line

Run the script from the command line with an optional `namespace` parameter:

```bash
python kubejobs/web_job_info.py --namespace=<your-namespace>
```

##### With Streamlit

Run the script as above, and then navigate to the Streamlit URL displayed in the console to view the web table.

```bash
streamlit run kubejobs/web_job_info.py
```

### `manage_user_jobs.py`

#### Overview

`manage_user_jobs.py` is a Python script for listing or deleting Kubernetes jobs initiated by a specific user. It offers console-based output using the Rich library.

#### Features

- Fetch Kubernetes Jobs from a specific namespace.
- Filter jobs based on username and a search term.
- Optionally delete jobs that meet the filter criteria.

#### Usage

##### Command Line

Run the script from the command line with optional parameters for namespace, username, search term, and actions.

```bash
python kubejobs/manage_user_jobs.py --namespace=<your-namespace> --username=<your-username> --term=<search-term> --delete=<True/False>
```

#### Note: This script does not support Streamlit.


For more detailed examples and usage information, please refer to the official [documentation](https://antreas.io/kubejobs/).

## Contributing

Contributions are welcome! If you'd like to contribute, please:

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Commit your changes and push them to your fork
4. Open a pull request

## License

KubeJobs is released under the MIT [License](LICENSE).
