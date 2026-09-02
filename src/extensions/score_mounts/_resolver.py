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
    """Describe one documentation mount and how its source root is resolved."""

    src_root: str
    runtime_path: str
    mount_at: str
    attach_to: str | None = None
    entry_doc: str = "index"
    external: bool = False
    repository: str = ""
    # Generated roots use bazel-bin under ``bazel run`` and bazel-out in a
    # sandbox; source and external roots follow their normal path rules.
    generated: bool = False
    # Explicit source bundles provide paths relative to ``runtime_path`` so
    # the mount can use the original files without recursively walking peers.
    files: list[str] = field(default_factory=list)
    data: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MountsManifest:
    mounts: list[MountSpec]


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
        raw_files = entry.get("files", [])
        if not isinstance(raw_files, list):
            raise ValueError(
                f"mounts manifest entry field 'files' must be a list: {raw_files!r}"
            )
        mounts.append(
            MountSpec(
                src_root=str(entry["src_root"]),
                runtime_path=str(entry.get("runtime_path", "")),
                mount_at=str(entry["mount_at"]),
                attach_to=str(entry["attach_to"]) if entry.get("attach_to") else None,
                entry_doc=str(entry["entry_doc"])
                if entry.get("entry_doc")
                else "index",
                external=bool(entry.get("external", False)),
                repository=str(entry.get("repository", "")),
                # Older manifests do not have this field and represent regular
                # workspace or external-repository source roots.
                generated=bool(entry.get("generated", False)),
                files=[str(f) for f in cast("list[object]", raw_files)],
                data=[str(f) for f in cast("list[object]", raw_data)],
            )
        )
    return MountsManifest(mounts=mounts)


def resolve_walk_dir(
    manifest: MountsManifest,
    spec: MountSpec,
    ws_root: Path | None,
    runfiles_dir: Path | None = None,
) -> Path:
    """Resolve a mount directory for either ``bazel run`` or a sandbox build.

    Generated source roots are recorded with their execroot-relative bazel-out
    path, while ``bazel run`` exposes the same artifacts below ``bazel-bin`` in
    the workspace. The ``generated`` flag selects that translation.

    For example, a generated ``bazel-out/k8-fastbuild/bin/pkg/docs`` root
    resolves to ``<workspace>/bazel-bin/pkg/docs`` under ``bazel run`` and to
    ``<execroot>/bazel-out/k8-fastbuild/bin/pkg/docs`` in a sandbox. A regular
    workspace source resolves to ``<workspace>/<src_root>`` under ``bazel run``
    and ``<execroot>/<src_root>`` in a sandbox.
    """
    if spec.generated:
        if ws_root is not None:
            # Generated source files are exposed through bazel-bin at runtime,
            # while their manifest paths are execroot-relative bazel-out paths.
            output_parts = spec.src_root.split("/")
            if (
                # A generated file may be directly below the configuration's
                # ``bin`` directory, so the source root itself can end there.
                len(output_parts) >= 3
                and output_parts[0] == "bazel-out"
                and output_parts[2] == "bin"
            ):
                return ws_root / "bazel-bin" / "/".join(output_parts[3:])
            return ws_root / spec.src_root
        return Path.cwd() / spec.src_root
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


def resolve_source_files(
    manifest: MountsManifest,
    spec: MountSpec,
    ws_root: Path | None,
    runfiles_dir: Path | None = None,
) -> list[Path]:
    """Resolve an explicit source allowlist below its original parent.

    ``src_root`` uses the same context-dependent resolution as directory
    mounts. The manifest's relative file names then identify only the Bazel
    artifacts declared by ``docs_bundle(srcs = [...])``.
    """
    walk_dir = resolve_walk_dir(manifest, spec, ws_root, runfiles_dir)
    resolved_files: list[Path] = []
    for relative_path in spec.files:
        source_file = walk_dir / relative_path
        if not source_file.is_file():
            raise ValueError(
                "score_mounts: resolved source file does not exist: "
                f"{source_file} (mount_at={spec.mount_at})"
            )
        resolved_files.append(source_file)
    return resolved_files
