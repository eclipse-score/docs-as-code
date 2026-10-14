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

"""Load the composition manifest emitted by Bazel.

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
class BazelTarget:
    """One direct code target associated with a bundle.

    This is deliberately not just a Bazel label: the label identifies the
    target, while ``type`` carries ``ctx.rule.kind`` (for example
    ``cc_library`` or ``filegroup``). Both values are needed by consumers of
    the composition manifest.
    """

    # Canonical Bazel label, for example
    # ``@@//score/components/memory:implementation``.
    label: str
    # Bazel rule kind, for example ``cc_library`` or ``filegroup``. The rule
    # kind is not encoded in the label itself.
    type: str

    @classmethod
    def from_manifest_entry(cls, entry: dict[str, str]) -> BazelTarget:
        """Create a target from the producer-owned manifest representation."""
        return cls(label=entry["label"], type=entry["type"])


@dataclass(frozen=True)
class BundleMetadata:
    """Identity, primary Need, and direct targets of one bundle in a composition.

    ``MountSpec`` describes one physical source entry and its placement.
    ``BundleMetadata`` describes the logical bundle that declared that entry.
    A bundle can produce several mount entries after nesting and rebasing, so
    each of those ``MountSpec`` objects carries the same bundle metadata while
    retaining its own source and placement fields.
    """

    # Canonical Bazel label of the declaring bundle, for example
    # ``@@//score/components/memory:docs``.
    label: str = ""
    # The name passed to ``docs_bundle(name = ...)``, for example ``docs``.
    name: str = ""
    # Targets declared directly by this bundle, for example
    # ``(BazelTarget("@@//score/components/memory:implementation", "cc_library"),)``.
    # Targets inherited from dependencies or nested bundles do not belong here.
    code_targets: tuple[BazelTarget, ...] = ()
    # The local Sphinx-Needs ID representing the primary subject of this
    # bundle. A bundle may contain many other Needs; this identifies the one
    # that receives metadata belonging to the bundle itself.
    primary_need_id: str = ""

    @classmethod
    def from_manifest_entry(cls, entry: dict[str, object]) -> BundleMetadata:
        """Create bundle metadata from one producer-owned manifest entry."""
        bundle = cast("dict[str, object]", entry["bundle"])
        targets = cast("list[dict[str, str]]", bundle["code_targets"])
        return cls(
            label=cast("str", bundle["label"]),
            name=cast("str", bundle["name"]),
            # Older manifests do not carry an explicit primary Need. Treat
            # the field as absent so those manifests remain readable while
            # avoiding any name-based fallback.
            primary_need_id=cast("str", bundle.get("primary_need_id", "")),
            code_targets=tuple(
                BazelTarget.from_manifest_entry(target) for target in targets
            ),
        )


@dataclass(frozen=True)
class MountSpec:
    """Describe one physical mount and its associated logical bundle.

    The source, path, and placement fields describe where this particular
    entry is read and mounted. ``bundle`` links that physical entry back to
    the logical bundle that declared it. For example, the bundle
    ``@@//score/components/memory:docs`` may be rebased to
    ``components/memory``: ``mount_at`` changes, while ``bundle.name`` remains
    ``docs`` and ``bundle.label`` remains the bundle's Bazel label.
    """

    src_root: str
    runtime_path: str
    mount_at: str
    attach_to: str | None = None
    toctree_index: int = 0
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
    # Whether this physical entry belongs to the composition's root bundle.
    # Rebasing a nested bundle changes this to false while preserving the
    # logical bundle metadata below.
    root_bundle: bool = False
    # Logical bundle association and direct-target metadata for this physical
    # mount entry.
    bundle: BundleMetadata = field(default_factory=BundleMetadata)

    @classmethod
    def from_manifest_entry(cls, entry: dict[str, object]) -> MountSpec:
        """Create one mount spec from the producer-owned manifest entry."""
        attach_to = cast("str", entry["attach_to"])
        raw_toctree_index = entry.get("toctree_index", 0)
        # ``type is`` (not ``isinstance``) also rejects booleans, which are ints.
        if type(raw_toctree_index) is not int:
            raise ValueError(
                "mounts manifest entry field 'toctree_index' must be an int: "
                f"{raw_toctree_index!r}"
            )
        return cls(
            src_root=cast("str", entry["src_root"]),
            runtime_path=cast("str", entry["runtime_path"]),
            mount_at=cast("str", entry["mount_at"]),
            attach_to=attach_to or None,
            toctree_index=raw_toctree_index,
            entry_doc=cast("str", entry["entry_doc"]),
            external=cast("bool", entry["external"]),
            repository=cast("str", entry["repository"]),
            generated=cast("bool", entry["generated"]),
            files=cast("list[str]", entry.get("files", [])),
            data=cast("list[str]", entry["data"]),
            root_bundle=cast("bool", entry["root_bundle"]),
            bundle=BundleMetadata.from_manifest_entry(entry),
        )


@dataclass(frozen=True)
class MountsManifest:
    mounts: list[MountSpec]


def load_mounts_manifest(manifest_path: str | Path) -> MountsManifest:
    """Read the manifest JSON at ``manifest_path`` (an already-resolved path).

    Context-dependent path resolution (runfiles under ``bazel run`` vs. the
    exec root in a sandbox) is the caller's responsibility.
    """
    manifest_path = Path(manifest_path)
    data = cast(
        "dict[str, object]",
        json.loads(manifest_path.read_text(encoding="utf-8")),
    )
    entries = cast("list[dict[str, object]]", data["mounts"])
    return MountsManifest(
        mounts=[MountSpec.from_manifest_entry(entry) for entry in entries]
    )


def _bazel_bin_relative(execroot_path: str) -> str | None:
    """Return the part of ``execroot_path`` below ``bazel-out/<config>/bin``.

    The configuration segment is not fixed (``k8-fastbuild``, ``k8-opt``,
    ...), so any single segment is accepted. Returns ``None`` when the path
    is not below a configuration's ``bin`` directory.
    """
    output_parts = execroot_path.split("/")
    if (
        # A generated file may be directly below the configuration's
        # ``bin`` directory, so the path itself can end there.
        len(output_parts) >= 3
        and output_parts[0] == "bazel-out"
        and output_parts[2] == "bin"
    ):
        return "/".join(output_parts[3:])
    return None


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
            bin_relative = _bazel_bin_relative(spec.src_root)
            if bin_relative is not None:
                return ws_root / "bazel-bin" / bin_relative
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


def resolve_output_file(
    execroot_path: str,
    ws_root: Path | None,
    runfiles_dir: Path | None = None,
) -> Path:
    """Resolve an execroot-relative manifest path to a file on disk.

    In a sandbox the runfiles directory lives below the execroot's
    ``bazel-out``, so the execroot prefix is reused unchanged. Under
    ``bazel run`` the same artifact is exposed below the workspace's
    ``bazel-bin``, which drops the ``bazel-out/<configuration>/bin`` prefix
    for any configuration (``k8-fastbuild``, ``k8-opt``, ...). Without a
    workspace root the path is relative to the current directory.
    """
    if ws_root is None or runfiles_dir is None:
        return Path.cwd() / execroot_path
    runfiles_str = str(runfiles_dir)
    if "/bazel-out/" in runfiles_str:
        # Execroot = runfiles path before the first /bazel-out/ occurrence
        # e.g. runfiles=execroot/_main/bazel-out/... => execroot=execroot/_main
        return Path(runfiles_str.split("/bazel-out/")[0]) / execroot_path
    bin_relative = _bazel_bin_relative(execroot_path)
    if bin_relative is not None:
        return ws_root / "bazel-bin" / bin_relative
    return ws_root / "bazel-bin" / execroot_path
