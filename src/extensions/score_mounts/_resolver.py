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
performs no label-to-path reconstruction. Every path stored in the manifest is a
Bazel ``short_path`` and therefore resolves relative to the manifest's own
directory."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MountSpec:
    src_root: str
    runtime_path: str
    mount_at: str
    attach_to: str | None = None
    entry_doc: str = "index"
    external: bool = False


@dataclass(frozen=True)
class MountsManifest:
    manifest_path: Path
    mounts: list[MountSpec]

    @property
    def root(self) -> Path:
        """Directory the manifest lives in — the base for its short_path entries."""
        return self.manifest_path.parent

    def runtime_dir(self, spec: MountSpec) -> Path:
        """Absolute path of a bundle's staged mount-root directory.

        ``runtime_path`` is a Bazel ``short_path`` (the bundle's source
        directory, staged in place — not a copy) and resolves relative to the
        manifest's own directory. Main-repo sources resolve the same way inside a
        sandbox build. External sources (``../<repo>+/X``) are only ever walked
        under ``bazel run`` with an external bundle, where ``../`` steps out
        of ``_main`` to the sibling repo dir in the runfiles tree — so no
        context-dependent mapping is needed here.
        """
        return Path(os.path.abspath(str(self.root / spec.runtime_path)))


def load_mounts_manifest(manifest_path: str | Path) -> MountsManifest:
    """Read the manifest JSON at ``manifest_path`` (an already-resolved path).

    Context-dependent path resolution (runfiles under ``bazel run`` vs. the
    exec root in a sandbox) is the caller's responsibility.
    """
    manifest_path = Path(manifest_path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(
            f"mounts manifest must be a JSON object, got {type(data).__name__}: {data!r}"
        )
    mounts: list[MountSpec] = []
    for entry in data.get("mounts", []):
        if "src_root" not in entry or "mount_at" not in entry:
            raise ValueError(
                f"mounts manifest entry missing 'src_root'/'mount_at': {entry!r}"
            )
        mounts.append(
            MountSpec(
                src_root=entry["src_root"],
                runtime_path=entry.get("runtime_path", ""),
                mount_at=entry["mount_at"],
                attach_to=entry.get("attach_to") or None,
                entry_doc=entry.get("entry_doc") or "index",
                external=entry.get("external", False),
            )
        )
    return MountsManifest(
        manifest_path=manifest_path,
        mounts=mounts,
    )


def resolve_walk_dir(
    manifest: MountsManifest, spec: MountSpec, ws_root: Path | None
) -> Path:
    """Resolve a mount directory for either ``bazel run`` or a sandbox build."""
    if spec.external and ws_root is not None:
        return manifest.runtime_dir(spec)
    if ws_root is not None:
        return ws_root / spec.src_root
    return Path(os.path.abspath(spec.src_root))
