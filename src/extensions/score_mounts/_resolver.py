# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""Load the mounts manifest JSON emitted by the ``_mounts_manifest`` Bazel rule.

All mount paths are authored by Bazel (where ``File`` objects have real paths)
and shipped in a small JSON manifest. This module only *reads* that manifest — it
performs no label-to-path reconstruction. The caller provides the Bazel execution
context needed to resolve the manifest's ``short_path`` values safely."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class MountSpec:
    src_root: str
    runtime_path: str
    mount_at: str
    attach_to: str | None = None
    entry_doc: str = "index"
    external: bool = False
    repository: str = ""
    include: list[str] = field(default_factory=list)
    data: list[str] = field(default_factory=list)
    path_check: str = "error"


@dataclass(frozen=True)
class MountsManifest:
    mounts: list[MountSpec]
    primary_source: MountSpec | None = None


def _load_mount_spec(raw_entry: object) -> MountSpec:
    """Validate and convert one mount manifest entry."""
    if not isinstance(raw_entry, dict):
        raise ValueError(f"mounts manifest entry must be an object: {raw_entry!r}")
    entry = cast("dict[str, object]", raw_entry)
    if "src_root" not in entry or "mount_at" not in entry:
        raise ValueError(
            f"mounts manifest entry missing 'src_root'/'mount_at': {entry!r}"
        )
    raw_data = entry.get("data", [])
    if not isinstance(raw_data, list):
        raise ValueError(
            f"mounts manifest entry field 'data' must be a list: {raw_data!r}"
        )
    raw_include = entry.get("include", [])
    if not isinstance(raw_include, list):
        raise ValueError(
            f"mounts manifest entry field 'include' must be a list: {raw_include!r}"
        )
    return MountSpec(
        src_root=str(entry["src_root"]),
        runtime_path=str(entry.get("runtime_path", "")),
        mount_at=str(entry["mount_at"]),
        attach_to=str(entry["attach_to"]) if entry.get("attach_to") else None,
        entry_doc=str(entry["entry_doc"]) if entry.get("entry_doc") else "index",
        external=bool(entry.get("external", False)),
        repository=str(entry.get("repository", "")),
        include=[str(path) for path in cast("list[object]", raw_include)],
        data=[str(f) for f in cast("list[object]", raw_data)],
        path_check=str(entry.get("path_check", "error")),
    )


def load_mounts_manifest(manifest_path: str | Path) -> MountsManifest:
    """Read the manifest JSON at ``manifest_path`` (an already-resolved path).

    Context-dependent path resolution (runfiles under ``bazel run`` vs. the
    exec root in a sandbox) is the caller's responsibility.
    """
    manifest_path = Path(manifest_path)
    raw_data: object = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        raise ValueError(
            f"mounts manifest must be a JSON object, got {type(raw_data).__name__}: {raw_data!r}"
        )
    data = cast("dict[str, object]", raw_data)
    mounts: list[MountSpec] = []
    mounts_data = data.get("mounts", [])
    if not isinstance(mounts_data, list):
        raise ValueError("mounts manifest field 'mounts' must be a list")
    typed_mounts_data = cast("list[object]", mounts_data)
    for raw_entry in typed_mounts_data:
        mounts.append(_load_mount_spec(raw_entry))
    raw_primary_source = data.get("primary_source")
    primary_source = (
        _load_mount_spec(raw_primary_source) if raw_primary_source is not None else None
    )
    return MountsManifest(mounts=mounts, primary_source=primary_source)


def resolve_walk_dir(
    manifest: MountsManifest,
    spec: MountSpec,
    ws_root: Path | None,
    runfiles_dir: Path | None = None,
) -> Path:
    """Resolve a mount directory for either ``bazel run`` or a sandbox build."""
    if spec.external and ws_root is not None:
        if runfiles_dir is None:
            raise ValueError("external mounts under bazel run require RUNFILES_DIR")
        # External short paths begin with ``../<repo>+`` relative to the
        # runfiles ``_main`` directory, not relative to a manifest nested in a
        # Bazel package. Prefixing ``_main`` preserves that Bazel convention.
        return Path(os.path.abspath(runfiles_dir / "_main" / spec.runtime_path))
    if ws_root is not None:
        return ws_root / spec.src_root
    return Path.cwd() / spec.src_root
