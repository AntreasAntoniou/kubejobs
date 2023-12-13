# test_kubemanager.py
import subprocess

import pytest

from kubejobs.helper import KubeManager

kmanager = KubeManager()

# Assuming 'workspace_name' is the name of your test namespace
# and 'user_name' corresponds to a label value, you've set up for test PVCs.
workspace_name = "informatics"
user_name = "aantoniou-infk8s"


def setup_function(function):
    # Create a PVC for testing purposes
    subprocess.run(
        [
            "kubectl",
            "create",
            "pvc",
            "test-pvc-delete",
            "--namespace",
            workspace_name,
        ]
    )


def teardown_function(function):
    # Clean up test PVC
    subprocess.run(
        [
            "kubectl",
            "delete",
            "pvc",
            "test-pvc-delete",
            "--namespace",
            workspace_name,
        ]
    )


def test_delete_pvc_with_name():
    # Use the method from KubeManager
    kmanager.delete_pvc_with_name("test-pvc-delete", workspace_name, user_name)

    # Verify PVC has been deleted
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "pvc",
            "test-pvc-delete",
            "--namespace",
            workspace_name,
        ],
        capture_output=True,
    )

    assert "test-pvc-delete" not in result.stdout.decode()


# Additional tests can be added following a similar setup and teardown structure
