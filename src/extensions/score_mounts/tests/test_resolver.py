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
"""Unit tests for the mounts manifest loader (``_resolver``).

These cover the pure parsing layer only: reading the synchronized producer
format into ``MountSpec`` objects and resolving source roots in runfiles versus
an exec root."""

import json
from pathlib import Path
from typing import cast

import pytest

from src.extensions.score_mounts._resolver import (
    BazelTarget,
    BundleMetadata,
    MountSpec,
    load_mounts_manifest,
    resolve_source_files,
    resolve_walk_dir,
)


def _write_manifest(
    tmp_path: Path,
    payload: dict[str, object],
) -> Path:
    """Write one complete producer-shaped manifest fixture."""
    if isinstance(payload.get("mounts"), list):
        mounts: list[object] = []
        for raw_entry in cast("list[object]", payload["mounts"]):
            if isinstance(raw_entry, dict):
                entry = cast("dict[str, object]", raw_entry)
                mounts.append(
                    {
                        "src_root": "",
                        "runtime_path": "",
                        "mount_at": "",
                        "attach_to": "",
                        "entry_doc": "index",
                        "external": False,
                        "repository": "",
                        "generated": False,
                        "data": [],
                        "root_bundle": False,
                        "bundle": {
                            "label": "@@//:test_bundle",
                            "name": "test_bundle",
                            "code_targets": [],
                        },
                        **entry,
                    }
                )
            else:
                mounts.append(raw_entry)
        payload = {**payload, "mounts": mounts}
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = tmp_path / "_mounts_manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_load_single_entry(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "src/docs",
                    "runtime_path": "src/docs_dir",
                    "mount_at": "internals/code_docs",
                }
            ],
        },
    )
    result = load_mounts_manifest(str(manifest))
    assert result is not None
    assert result.mounts == [
        MountSpec(
            src_root="src/docs",
            runtime_path="src/docs_dir",
            mount_at="internals/code_docs",
            bundle=BundleMetadata(
                label="@@//:test_bundle",
                name="test_bundle",
            ),
        )
    ]


def test_load_entry_with_attach_to_and_entry_doc(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "src/docs",
                    "runtime_path": "src/docs_dir",
                    "mount_at": "x",
                    "attach_to": "internals/index",
                    "entry_doc": "start",
                }
            ],
        },
    )
    spec = load_mounts_manifest(str(manifest)).mounts[0]
    assert spec.attach_to == "internals/index"
    assert spec.entry_doc == "start"


def test_load_bundle_metadata_and_direct_targets(tmp_path: Path) -> None:
    """Decode bundle identity and direct target pairs from the manifest."""
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "docs",
                    "runtime_path": "docs",
                    "mount_at": "component",
                    "root_bundle": True,
                    "bundle": {
                        "label": "@@//pkg:memory",
                        "name": "memory",
                        "code_targets": [
                            {"label": "@@//pkg:memory_core", "type": "cc_library"},
                            {"label": "@@//pkg:memory_api", "type": "cc_library"},
                        ],
                    },
                }
            ],
        },
    )

    result = load_mounts_manifest(manifest)

    assert result.mounts[0].root_bundle is True
    assert result.mounts[0].bundle == BundleMetadata(
        label="@@//pkg:memory",
        name="memory",
        code_targets=(
            BazelTarget(label="@@//pkg:memory_core", type="cc_library"),
            BazelTarget(label="@@//pkg:memory_api", type="cc_library"),
        ),
    )


def test_external_mount_keeps_execroot_and_runfiles_locations(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "src/docs",
                    "runtime_path": "src/docs_dir",
                    "mount_at": "x",
                },
                {
                    "src_root": "external/score_process_description+/docs_as_mount",
                    "runtime_path": "../score_process_description+/docs_as_mount",
                    "mount_at": "process",
                    "external": True,
                    "repository": "score_process_description+",
                },
            ],
        },
    )
    specs = load_mounts_manifest(str(manifest)).mounts
    assert specs[0].src_root == "src/docs"
    assert specs[1].src_root == "external/score_process_description+/docs_as_mount"
    assert specs[1].external is True
    assert specs[1].repository == "score_process_description+"


def test_external_mount_uses_execroot_path_in_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "external/score_process_description+/docs_as_mount",
                    "runtime_path": "../score_process_description+/docs_as_mount",
                    "mount_at": "process",
                    "external": True,
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]
    assert resolve_walk_dir(load_mounts_manifest(manifest), spec, None) == (
        tmp_path / "external" / "score_process_description+" / "docs_as_mount"
    )


def test_external_mount_uses_runfiles_root_under_bazel_run(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "_main" / "package",
        {
            "mounts": [
                {
                    "src_root": "external/score_process_description+/docs_as_mount",
                    "runtime_path": "../score_process_description+/docs_as_mount",
                    "mount_at": "process",
                    "external": True,
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]
    assert resolve_walk_dir(
        load_mounts_manifest(manifest),
        spec,
        tmp_path / "workspace",
        tmp_path,
    ) == (tmp_path / "score_process_description+" / "docs_as_mount")


def test_generated_source_mount_uses_bazel_bin_under_bazel_run(tmp_path: Path) -> None:
    """Translate an execroot-relative generated source to workspace bazel-bin."""
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "bazel-out/k8-fastbuild/bin/pkg/generated",
                    "runtime_path": "bazel-out/k8-fastbuild/bin/pkg/generated",
                    "mount_at": "generated",
                    "generated": True,
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]

    assert (
        resolve_walk_dir(
            load_mounts_manifest(manifest),
            spec,
            tmp_path / "workspace",
            tmp_path / "workspace" / "docs.runfiles",
        )
        == tmp_path / "workspace" / "bazel-bin" / "pkg" / "generated"
    )


def test_generated_root_source_mount_uses_bazel_bin_under_bazel_run(
    tmp_path: Path,
) -> None:
    """Translate a generated root-level source to the bazel-bin directory."""
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "bazel-out/k8-fastbuild/bin",
                    "runtime_path": "bazel-out/k8-fastbuild/bin",
                    "mount_at": "generated",
                    "generated": True,
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]

    assert (
        resolve_walk_dir(load_mounts_manifest(manifest), spec, tmp_path / "workspace")
        == tmp_path / "workspace" / "bazel-bin"
    )


def test_explicit_source_files_resolve_below_original_root(tmp_path: Path) -> None:
    """Resolve an explicit file allowlist without copying its source files."""
    source_root = tmp_path / "workspace" / "docs"
    source_root.mkdir(parents=True)
    (source_root / "index.rst").write_text("Index", encoding="utf-8")
    (source_root / "guide.rst").write_text("Guide", encoding="utf-8")
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "docs",
                    "runtime_path": "docs",
                    "mount_at": "generated",
                    "files": ["index.rst", "guide.rst"],
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]

    assert resolve_source_files(
        load_mounts_manifest(manifest),
        spec,
        tmp_path / "workspace",
    ) == [source_root / "index.rst", source_root / "guide.rst"]


def test_generated_source_mount_uses_execroot_in_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the generated source's execroot path inside a sandbox."""
    monkeypatch.chdir(tmp_path)
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "bazel-out/k8-fastbuild/bin/pkg/generated",
                    "runtime_path": "bazel-out/k8-fastbuild/bin/pkg/generated",
                    "mount_at": "generated",
                    "generated": True,
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]

    assert resolve_walk_dir(load_mounts_manifest(manifest), spec, None) == (
        tmp_path / "bazel-out" / "k8-fastbuild" / "bin" / "pkg" / "generated"
    )
