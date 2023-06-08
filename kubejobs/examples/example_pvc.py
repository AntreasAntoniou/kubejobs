from kubejobs import create_pv
from kubejobs.jobs import create_pvc
from rich import print

if __name__ == "__main__":
    access_modes = ["ReadWriteOnce"]
    pv_type = "node"

    create_pvc(
        pvc_name="test-pvc", storage="1Gi", access_modes="ReadWriteOnce"
    )

    print(
        "Created a local PersistentVolume named 'test-pvc' with 1Gi of storage."
    )
