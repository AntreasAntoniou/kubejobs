import base64
import os
import subprocess

import fire


def create_secret_from_env_file(self, env_file, namespace, secret_name):
    """
    Read environment variables from a .env file and create a Kubernetes secret.
    :param env_file: Path to the .env file
    :param secret_name: Name of the Kubernetes secret to create/update
    """
    # Read environment variables from .env file
    with open(env_file, "r") as file:
        lines = file.readlines()

    # Filter out empty lines and lines starting with #
    lines = [
        line.strip()
        for line in lines
        if line.strip() and not line.startswith("#")
    ]

    # Base64 encode each value and create the data dictionary
    data_dict = {}
    for line in lines:
        key, value = line.split("=", 1)
        data_dict[key] = base64.b64encode(value.encode("utf-8")).decode(
            "utf-8"
        )

    # Create or update the Kubernetes Secret
    command = ["kubectl", "create", "secret", "generic", secret_name]
    for key, value in data_dict.items():
        command += ["--from-literal={0}={1}".format(key, value)]
    command += ["--namespace", self.namespace]
    command += ["--dry-run=client", "-o", "yaml"]

    # Execute kubectl command
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception("Failed to create secret: " + result.stderr)

    # Apply the secret using kubectl
    apply_command = ["kubectl", "apply", "-f", "-"]
    apply_result = subprocess.run(
        apply_command, input=result.stdout, capture_output=True, text=True
    )

    if apply_result.returncode != 0:
        raise Exception("Failed to apply secret: " + apply_result.stderr)

    print(
        "Secret '{}' created/updated successfully in namespace '{}'.".format(
            secret_name, self.namespace
        )
    )


if __name__ == "__main__":
    fire.Fire(EnvSecretsManager)
