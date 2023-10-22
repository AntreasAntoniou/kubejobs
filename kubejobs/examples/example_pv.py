from kubejobs.jobs import create_pv

if __name__ == "__main__":
    pv_name = "datasets-pv"
    storage = "5000Gi"
    storage_class_name = "manual"
    access_modes = ["ReadWriteOnce"]
    pv_type = "node"
    local_path = "/mnt/local-storage"

    create_pv(
        pv_name,
        storage,
        storage_class_name,
        access_modes,
        pv_type,
        local_path=local_path,
    )

    print(
        f"Created a local PersistentVolume named '{pv_name}' with {storage} of storage, '{storage_class_name}' "
        f"storage class, and local path '{local_path}'."
    )
