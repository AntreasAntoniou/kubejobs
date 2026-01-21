"""Utilities to label Kubernetes nodes with accelerator labels.

This enables shorthand selection in kubejobs via the `accelerator` parameter
(e.g., "h100x1", "a100-80x2") by ensuring nodes carry labels like:
- accel.family=h100
- accel.mem_gb=80 (optional)

Usage examples:
  python -m kubejobs.label_nodes --node_selector 'cloud.google.com/gke-nodepool=gpu-pool' --family h100 --mem_gb 80
  python -m kubejobs.label_nodes --node_selector 'cloud.google.com/gke-nodepool=gpu-pool' --family a100 --mem_gb 40

Requires kubeconfig context pointing to the target cluster.
"""

from __future__ import annotations

from typing import Optional, Dict
import logging
import subprocess
import json
import shutil
import re

from kubernetes import client, config
from rich.logging import RichHandler
from rich import print as rprint
from rich.table import Table
import fire

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RichHandler(markup=True)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


def _infer_family_and_mem(
    accelerator_label: str,
) -> tuple[str | None, int | None]:
    """Infer accelerator family and memory (GB) from GKE accelerator label.

    Args:
        accelerator_label: Value of node label 'cloud.google.com/gke-accelerator'.

    Returns:
        Tuple of (family, mem_gb). If unable to infer, returns (None, None).
    """
    if not accelerator_label:
        return None, None
    s = accelerator_label.lower()
    if "h100" in s:
        # GCP H100 is 80GB at the time of writing
        return "h100", 80
    if "a100" in s:
        mem_gb = 80 if "80" in s else 40
        return "a100", mem_gb
    if "l4" in s:
        return "l4", 24
    return None, None


def _infer_from_gpu_product(
    product_label: str,
) -> tuple[str | None, int | None]:
    """Infer from 'nvidia.com/gpu.product' if present.

    Examples observed:
      - 'NVIDIA H100 80GB HBM3'
      - 'NVIDIA A100-PCIE-80GB'
      - 'NVIDIA A100-PCIE-40GB'
      - 'NVIDIA L4'
    """
    if not product_label:
        return None, None
    s = product_label.lower()
    if "h100" in s:
        return "h100", 80
    if "a100" in s:
        mem_gb = 80 if "80" in s else 40
        return "a100", mem_gb
    if " l4" in s or s.endswith("l4") or s.startswith("l4"):
        return "l4", 24
    return None, None


def _parse_gce_provider_id(
    provider_id: Optional[str],
) -> tuple[str | None, str | None, str | None]:
    """Parse GCE providerID of form 'gce://PROJECT/ZONE/INSTANCE'."""
    if not provider_id or not provider_id.startswith("gce://"):
        return None, None, None
    try:
        parts = provider_id.replace("gce://", "").split("/")
        if len(parts) >= 3:
            return parts[0], parts[1], "/".join(parts[2:])
    except Exception:
        return None, None, None
    return None, None, None


def _infer_from_gcloud(
    project: str, zone: str, instance: str, timeout_s: int = 15
) -> tuple[str | None, int | None, int | None]:
    """Use gcloud to describe instance and infer (family, mem_gb, count).

    Returns (family, mem_gb, count) or (None, None, None) on failure.
    """
    if shutil.which("gcloud") is None:
        return None, None, None
    try:
        cmd = [
            "gcloud",
            "compute",
            "instances",
            "describe",
            instance,
            f"--zone={zone}",
            f"--project={project}",
            "--format=json",
        ]
        out = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_s,
            text=True,
        )
        if out.returncode != 0:
            return None, None, None
        data = json.loads(out.stdout or "{}")
        gas = data.get("guestAccelerators") or []
        if not gas:
            return None, None, None
        acc = gas[0]
        acc_type = acc.get("acceleratorType", "")
        acc_count = acc.get("acceleratorCount")
        # Extract last path segment if it's a URL
        if "/" in acc_type:
            acc_type = acc_type.rsplit("/", 1)[-1]
        # Map to family/mem
        fam, mem = _infer_family_and_mem(acc_type)
        # If acc_type is like 'nvidia-tesla-a100-80gb' our _infer_family_and_mem
        # will catch 'a100' and '80'. If not, try product-based mapping.
        if fam is None:
            fam, mem = _infer_from_gpu_product(acc_type)
        count_val = int(acc_count) if isinstance(acc_count, int) else None
        return fam, mem, count_val
    except Exception:
        return None, None, None


def label_nodes_for_accelerator(
    node_selector: str,
    family: str,
    mem_gb: Optional[int] = None,
    count: Optional[int] = None,
    overwrite: bool = True,
) -> Dict[str, int]:
    """Label nodes matching a selector with accelerator labels.

    Args:
        node_selector: Label selector for nodes to label, e.g.,
            'cloud.google.com/gke-nodepool=gpu-pool'.
        family: Accelerator family shorthand (e.g., 'h100', 'a100', 'l4').
        mem_gb: Optional memory in GB (e.g., 80 for H100 80GB, 40 for A100-40).
        count: Optional number of accelerators on the node (e.g., 1, 2, 8).
        overwrite: Whether to overwrite existing label values.

    Returns:
        A dict with counts of labeled nodes and total matched nodes.
    """
    family = family.lower().strip()
    if family not in {"h100", "a100", "l4"}:
        raise ValueError("family must be one of: h100, a100, l4")

    config.load_kube_config()
    v1 = client.CoreV1Api()
    nodes = v1.list_node(label_selector=node_selector).items
    logger.info(
        f"Found [bold]{len(nodes)}[/] node(s) for selector: [cyan]{node_selector}[/]"
    )

    patch_count = 0
    for node in nodes:
        name = node.metadata.name
        labels = node.metadata.labels or {}
        new_labels = labels.copy()
        new_labels["accel.family"] = family
        if mem_gb is not None:
            new_labels["accel.mem_gb"] = str(mem_gb)
        if count is not None:
            new_labels["accel.count"] = str(count)

        if not overwrite and (
            ("accel.family" in labels)
            or (mem_gb is not None and "accel.mem_gb" in labels)
            or (count is not None and "accel.count" in labels)
        ):
            logger.info(
                f"[yellow]Skipping[/] {name} (labels exist, overwrite=False)"
            )
            continue

        patch_body = {"metadata": {"labels": new_labels}}
        v1.patch_node(name, patch_body)
        patch_count += 1
        logger.info(
            f"Labeled node [green]{name}[/] with accel.family={family}"
            + (f", accel.mem_gb={mem_gb}" if mem_gb is not None else "")
            + (f", accel.count={count}" if count is not None else "")
        )

    logger.info(f"Updated [bold]{patch_count}[/] node(s)")
    return {"matched": len(nodes), "labeled": patch_count}


def auto_label_nodes(
    node_selector: Optional[str] = None,
    overwrite: bool = True,
    default_family: Optional[str] = None,
    default_mem_gb: Optional[int] = None,
) -> Dict[str, int]:
    """Automatically label nodes with accel.* labels based on GKE metadata.

    Discovers per-node accelerator family from 'cloud.google.com/gke-accelerator',
    infers memory size, and reads GPU count from node capacity 'nvidia.com/gpu'.
    If the accelerator label is missing but the node reports GPU capacity, this
    can fall back to the provided default family/memory.

    Args:
        node_selector: Optional label selector to restrict nodes (e.g., a pool).
        overwrite: Whether to overwrite existing accel.* labels.
        default_family: Optional family to use when inference fails but GPUs
            are present (one of: h100, a100, l4).
        default_mem_gb: Optional memory (GB) to pair with default_family.

    Returns:
        Dict summary with total matched and labeled counts.
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    nodes = v1.list_node(label_selector=node_selector or "").items
    logger.info(
        f"Scanning [bold]{len(nodes)}[/] node(s)"
        + (f" with selector [cyan]{node_selector}[/]" if node_selector else "")
    )

    matched = 0
    labeled = 0
    for node in nodes:
        matched += 1
        name = node.metadata.name
        labels = node.metadata.labels or {}
        accel_src = labels.get("cloud.google.com/gke-accelerator", "")

        # GPU count from capacity, fallback to allocatable
        gpu_capacity = None
        try:
            gpu_capacity = node.status.capacity.get("nvidia.com/gpu")
            if not gpu_capacity and node.status.allocatable:
                gpu_capacity = node.status.allocatable.get("nvidia.com/gpu")
        except Exception:
            gpu_capacity = None
        gpu_count: Optional[int] = int(gpu_capacity) if gpu_capacity else None

        # 1) Try GKE accelerator label
        family, mem_gb = _infer_family_and_mem(accel_src)
        # 2) Try nvidia.com/gpu.product label
        if family is None:
            product_label = labels.get("nvidia.com/gpu.product", "")
            family, mem_gb = _infer_from_gpu_product(product_label)
        # 3) Try instance-type heuristics (GCE machine families)
        if family is None:
            itype = (
                labels.get("node.kubernetes.io/instance-type")
                or labels.get("beta.kubernetes.io/instance-type")
                or ""
            ).lower()
            if itype.startswith("a3"):
                family, mem_gb = "h100", 80
            elif itype.startswith("a2"):
                family, mem_gb = "a100", 80
            elif itype.startswith("g2"):
                family, mem_gb = "l4", 24

        # 4) Try gcloud describe via providerID
        if family is None and node.spec and node.spec.provider_id:
            project, zone, inst = _parse_gce_provider_id(node.spec.provider_id)
            if project and zone and inst:
                fam2, mem2, cnt2 = _infer_from_gcloud(project, zone, inst)
                if fam2 is not None:
                    family, mem_gb = fam2, mem2 if mem2 is not None else mem_gb
                    if gpu_count is None and cnt2 is not None:
                        gpu_count = cnt2
        # 5) Optional user-provided default
        if family is None and gpu_count and default_family:
            fam_norm = default_family.lower().strip()
            if fam_norm in {"h100", "a100", "l4"}:
                family = fam_norm
                mem_gb = default_mem_gb
                logger.info(
                    f"[cyan]Fallback[/] {name}: using default family={family}"
                    + (f", mem_gb={mem_gb}" if mem_gb is not None else "")
                )
        # If still unknown, skip
        if family is None:
            logger.info(
                f"[yellow]Skip[/] {name}: cannot infer accelerator (no label/product/provider info)"
            )
            continue

        # Apply labels to this single node by targeting hostname selector
        res = label_nodes_for_accelerator(
            node_selector=f"kubernetes.io/hostname={name}",
            family=family,
            mem_gb=mem_gb,
            count=gpu_count,
            overwrite=overwrite,
        )
        labeled += res.get("labeled", 0)

    logger.info(
        f"Auto-labeled [bold]{labeled}[/] of [bold]{matched}[/] matched node(s)"
    )
    return {"matched": matched, "labeled": labeled}


def _gcloud_json(cmd: list[str], timeout_s: int = 30) -> Optional[dict]:
    if shutil.which("gcloud") is None:
        logger.error("gcloud CLI not found in PATH")
        return None
    try:
        out = subprocess.run(
            cmd + ["--format=json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_s,
            text=True,
        )
        if out.returncode != 0:
            logger.error(out.stderr.strip())
            return None
        return json.loads(out.stdout or "{}")
    except Exception as exc:
        logger.error(f"gcloud call failed: {exc}")
        return None


def _gcloud_ok(cmd: list[str], timeout_s: int = 900) -> bool:
    if shutil.which("gcloud") is None:
        logger.error("gcloud CLI not found in PATH")
        return False
    try:
        out = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_s,
            text=True,
        )
        if out.returncode != 0:
            logger.error(out.stderr.strip())
            return False
        return True
    except Exception as exc:
        logger.error(f"gcloud call failed: {exc}")
        return False


def _to_region(location: str) -> str:
    # Convert 'us-west1-a' -> 'us-west1' if zonal; otherwise return as-is
    if (
        location
        and location.count("-") >= 2
        and len(location.split("-")[-1]) == 1
    ):
        return "-".join(location.split("-")[:-1])
    return location


def _list_node_pools(
    cluster: str, location: str, project: Optional[str] = None
) -> list[dict]:
    cmd = [
        "gcloud",
        "container",
        "node-pools",
        "list",
        f"--cluster={cluster}",
        f"--location={location}",
    ]
    if project:
        cmd.append(f"--project={project}")
    data = _gcloud_json(cmd) or []
    if not data:
        region = _to_region(location)
        if region != location:
            cmd[-1] = f"--location={region}"
            data = _gcloud_json(cmd) or []
    return data if isinstance(data, list) else []


def _describe_node_pool(
    cluster: str, location: str, node_pool: str, project: Optional[str] = None
) -> Optional[dict]:
    cmd = [
        "gcloud",
        "container",
        "node-pools",
        "describe",
        node_pool,
        f"--cluster={cluster}",
        f"--location={location}",
    ]
    if project:
        cmd.append(f"--project={project}")
    data = _gcloud_json(cmd)
    if data is None:
        region = _to_region(location)
        if region != location:
            cmd[-2] = f"--location={region}"
            data = _gcloud_json(cmd)
    return data


def _infer_from_pool_config(
    pool_desc: dict,
    pool_name: Optional[str] = None,
) -> tuple[str | None, int | None, int | None]:
    # Prefer explicit accelerator description
    cfg = (pool_desc or {}).get("config") or {}
    accs = cfg.get("accelerators") or []
    if accs:
        acc = accs[0]
        acc_type = acc.get("acceleratorType", "")
        acc_count = acc.get("acceleratorCount")
        fam, mem = _infer_family_and_mem(acc_type)
        if fam is None:
            fam, mem = _infer_from_gpu_product(acc_type)
        cnt = int(acc_count) if isinstance(acc_count, int) else None
        return fam, mem, cnt
    # Heuristic from machineType if accelerators aren't present
    mtype = (cfg.get("machineType") or cfg.get("minCpuPlatform") or "").lower()
    fam, mem, cnt = None, None, None
    if "a3-highgpu-" in mtype:
        fam, mem = "h100", 80
        # parse suffix like a3-highgpu-4g
        try:
            suffix = mtype.split("a3-highgpu-")[-1]
            if suffix.endswith("g"):
                cnt = int(suffix[:-1])
        except Exception:
            cnt = None
    elif "a2-highgpu-" in mtype:
        fam, mem = "a100", 40
        try:
            suffix = mtype.split("a2-highgpu-")[-1]
            if suffix.endswith("g"):
                cnt = int(suffix[:-1])
        except Exception:
            cnt = None
    elif mtype.startswith("g2-"):
        fam, mem = "l4", 24
        # count not encoded in type; leave None
    # If count still None, try parse from machine type generically or from pool name
    if cnt is None:
        name_for_parse = pool_name or (pool_desc.get("name") or "")
        cnt = _parse_count_from_machine_type(
            mtype
        ) or _parse_count_from_pool_name(name_for_parse)
    return fam, mem, cnt


def _compute_pool_labels(
    existing: dict,
    family: Optional[str],
    mem_gb: Optional[int],
    count: Optional[int],
    overwrite: bool,
) -> dict:
    labels = dict(existing or {})
    if family is not None and (overwrite or "accel.family" not in labels):
        labels["accel.family"] = family
    if mem_gb is not None and (overwrite or "accel.mem_gb" not in labels):
        labels["accel.mem_gb"] = str(mem_gb)
    # Always ensure accel.count is present; default to 1 if unknown
    final_count = count if count is not None else 1
    if overwrite or "accel.count" not in labels:
        labels["accel.count"] = str(final_count)
    return labels


def _parse_count_from_machine_type(machine_type: str) -> Optional[int]:
    if not machine_type:
        return None
    # Matches a3-highgpu-4g or a2-highgpu-2g → capture 4 or 2
    m = re.search(r"highgpu-(\d+)g", machine_type)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def _parse_count_from_pool_name(pool_name: str) -> Optional[int]:
    if not pool_name:
        return None
    # Matches suffix like ...-x4 → capture 4
    m = re.search(r"-x(\d+)$", pool_name)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def label_node_pool(
    cluster: str,
    location: str,
    node_pool: str,
    family: str,
    mem_gb: Optional[int] = None,
    count: Optional[int] = None,
    project: Optional[str] = None,
    overwrite: bool = True,
    async_mode: bool = True,
) -> dict:
    """Set accel.* labels on a GKE node pool (nodes inherit labels).

    Overwrites only the accel.* keys by merging with existing pool labels.
    """
    desc = _describe_node_pool(cluster, location, node_pool, project) or {}
    existing = ((desc.get("config") or {}).get("labels")) or {}
    new_labels = _compute_pool_labels(
        existing, family, mem_gb, count, overwrite
    )
    # Assemble labels flag as comma-separated key=value
    labels_flag = ",".join([f"{k}={v}" for k, v in new_labels.items()])
    cmd = [
        "gcloud",
        "container",
        "node-pools",
        "update",
        node_pool,
        f"--cluster={cluster}",
        f"--location={location}",
        f"--node-labels={labels_flag}",
        "--quiet",
    ]
    if project:
        cmd.append(f"--project={project}")
    # Prefer async to avoid long-running rollouts causing timeouts
    if async_mode:
        cmd.append("--async")
        ok = _gcloud_ok(cmd, timeout_s=60)
    else:
        ok = _gcloud_ok(cmd, timeout_s=900)
    if ok:
        logger.info(
            f"Updated node pool [green]{node_pool}[/] labels: "
            f"accel.family={new_labels.get('accel.family')}, "
            f"accel.mem_gb={new_labels.get('accel.mem_gb')}, "
            f"accel.count={new_labels.get('accel.count')}"
        )
    return {"ok": ok, "labels": new_labels}


def auto_label_node_pool(
    cluster: str,
    location: str,
    node_pool: str,
    project: Optional[str] = None,
    overwrite: bool = True,
    async_mode: bool = True,
) -> dict:
    """Infer accel.* for a node pool from its accelerator config and update labels."""
    desc = _describe_node_pool(cluster, location, node_pool, project)
    if not desc:
        return {"ok": False, "error": "describe failed"}
    fam, mem, cnt = _infer_from_pool_config(desc, pool_name=node_pool)
    if fam is None:
        return {"ok": False, "error": "cannot infer from node pool config"}
    return label_node_pool(
        cluster=cluster,
        location=location,
        node_pool=node_pool,
        family=fam,
        mem_gb=mem,
        count=cnt,
        project=project,
        overwrite=overwrite,
        async_mode=async_mode,
    )


def auto_label_all_pools(
    cluster: str,
    location: str,
    project: Optional[str] = None,
    overwrite: bool = True,
    async_mode: bool = True,
) -> dict:
    """Infer and label accel.* on all node pools in a cluster."""
    pools = _list_node_pools(cluster, location, project)
    results: dict[str, dict] = {}
    for p in pools:
        name = p.get("name") or p.get("selfLink", "").rsplit("/", 1)[-1]
        if not name:
            continue
        results[name] = auto_label_node_pool(
            cluster=cluster,
            location=location,
            node_pool=name,
            project=project,
            overwrite=overwrite,
            async_mode=async_mode,
        )
    return results


if __name__ == "__main__":
    # CLI:
    #   python -m kubejobs.label_nodes label --node_selector '...' --family h100 --mem_gb 80 --count 1
    #   python -m kubejobs.label_nodes auto --node_selector 'cloud.google.com/gke-nodepool=gpu-pool'
    fire.Fire(
        {
            "label": label_nodes_for_accelerator,
            "auto": auto_label_nodes,
            "label_pool": label_node_pool,
            "auto_label_pool": auto_label_node_pool,
            "auto_label_all_pools": auto_label_all_pools,
        }
    )
