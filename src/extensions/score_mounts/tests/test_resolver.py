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

These cover the pure parsing layer only: reading the JSON manifest into
``MountSpec`` objects, applying defaults, rejecting malformed input, and
resolving source roots in runfiles versus an exec root."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.extensions.score_mounts._resolver import (
    MountSpec,
    load_mounts_manifest,
    resolve_source_files,
    resolve_walk_dir,
)


def _write_manifest(tmp_path: Path, payload: dict[str, object]) -> Path:
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


def test_load_missing_required_key_raises(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"mounts": [{"runtime_path": "src/docs_dir"}]})
    with pytest.raises(ValueError, match="missing 'src_root'/'mount_at'"):
        load_mounts_manifest(str(manifest))


def test_load_non_object_raises(tmp_path: Path) -> None:
    manifest = tmp_path / "_mounts_manifest.json"
    manifest.write_text('["not", "an", "object"]', encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_mounts_manifest(str(manifest))


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
    cli_config = Mock(is_bazel_run=False)
    cli_config.ws_root = tmp_path
    cli_config.resolve_input_path.return_value = (
        tmp_path / "external" / "score_process_description+" / "docs_as_mount"
    )

    assert resolve_walk_dir(spec, cli_config) == (
        tmp_path / "external" / "score_process_description+" / "docs_as_mount"
    )
    assert cli_config.ws_root == tmp_path


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
    cli_config = Mock(is_bazel_run=True)
    cli_config.resolve_input_path.return_value = (
        tmp_path / "score_process_description+" / "docs_as_mount"
    )

    assert resolve_walk_dir(spec, cli_config) == (
        tmp_path / "score_process_description+" / "docs_as_mount"
    )
    cli_config.resolve_input_path.assert_called_once_with(
        Path("_main") / spec.runtime_path
    )


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

    cli_config = Mock()
    cli_config.resolve_bazel_output_path.return_value = (
        tmp_path / "workspace" / "bazel-bin" / "pkg" / "generated"
    )

    assert resolve_walk_dir(spec, cli_config) == (
        tmp_path / "workspace" / "bazel-bin" / "pkg" / "generated"
    )
    cli_config.resolve_bazel_output_path.assert_called_once_with(spec.src_root)


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

    cli_config = Mock()
    cli_config.resolve_bazel_output_path.return_value = tmp_path / "workspace/bazel-bin"

    assert resolve_walk_dir(spec, cli_config) == tmp_path / "workspace/bazel-bin"


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

    cli_config = Mock()
    cli_config.ws_root = source_root.parent

    assert resolve_source_files(spec, cli_config) == [
        source_root / "index.rst",
        source_root / "guide.rst",
    ]


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

    cli_config = Mock()
    cli_config.resolve_bazel_output_path.return_value = (
        tmp_path / "bazel-out" / "k8-fastbuild" / "bin" / "pkg" / "generated"
    )

    assert resolve_walk_dir(spec, cli_config) == (
        tmp_path / "bazel-out" / "k8-fastbuild" / "bin" / "pkg" / "generated"
    )
