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
``MountSpec`` objects, applying defaults, resolving ``runtime_dir`` relative
to the manifest, and rejecting malformed
input. Context-dependent path resolution (runfiles vs. exec root) lives in the
extension's ``__init__`` and is exercised via the consumer tests instead."""

import json
import os
from pathlib import Path

import pytest

from src.extensions.score_mounts.__init__ import _resolve_walk_dir
from src.extensions.score_mounts._resolver import (
    MountSpec,
    load_mounts_manifest,
)


def _write_manifest(tmp_path: Path, payload: dict) -> Path:
    manifest = tmp_path / "_mounts_manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_load_single_entry(tmp_path: Path):
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


def test_load_entry_with_attach_to_and_entry_doc(tmp_path: Path):
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


def test_external_mount_keeps_execroot_and_runfiles_locations(tmp_path: Path):
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
                    "src_root": "external/score_process+/docs_as_mount",
                    "runtime_path": "../score_process+/docs_as_mount",
                    "mount_at": "process",
                    "external": True,
                },
            ],
        },
    )
    specs = load_mounts_manifest(str(manifest)).mounts
    assert specs[0].src_root == "src/docs"
    assert specs[1].src_root == "external/score_process+/docs_as_mount"
    assert specs[1].external is True


def test_runtime_dir_resolves_next_to_manifest(tmp_path: Path):
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "src/docs",
                    "runtime_path": "src/docs_dir",
                    "mount_at": "x",
                }
            ],
        },
    )
    result = load_mounts_manifest(str(manifest))
    assert result.runtime_dir(result.mounts[0]) == tmp_path / "src" / "docs_dir"


def test_load_missing_required_key_raises(tmp_path: Path):
    manifest = _write_manifest(tmp_path, {"mounts": [{"runtime_path": "src/docs_dir"}]})
    with pytest.raises(ValueError, match="missing 'src_root'/'mount_at'"):
        load_mounts_manifest(str(manifest))


def test_load_non_object_raises(tmp_path: Path):
    manifest = tmp_path / "_mounts_manifest.json"
    manifest.write_text('["not", "an", "object"]', encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_mounts_manifest(str(manifest))


def test_runtime_dir_external_path_resolves_relative_to_manifest(tmp_path: Path):
    # Under `bazel run`, the '../<repo>+/...' short_path resolves natively in
    # the runfiles tree. runtime_dir must NOT remap '../' to 'external/'.
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "external/score_process+/docs_as_mount",
                    "runtime_path": "../score_process+/docs_as_mount",
                    "mount_at": "process",
                    "external": True,
                }
            ],
        },
    )
    result = load_mounts_manifest(str(manifest))
    # runtime_dir uses os.path.abspath (lexical, no symlink resolution); mirror
    # that here so the assertion never diverges on a symlinked tmp dir.
    expected = Path(
        os.path.abspath(tmp_path / ".." / "score_process+" / "docs_as_mount")
    )
    assert result.runtime_dir(result.mounts[0]) == expected


def test_external_mount_uses_execroot_path_in_sandbox(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    manifest = _write_manifest(
        tmp_path,
        {
            "mounts": [
                {
                    "src_root": "external/score_process+/docs_as_mount",
                    "runtime_path": "../score_process+/docs_as_mount",
                    "mount_at": "process",
                    "external": True,
                }
            ]
        },
    )
    spec = load_mounts_manifest(manifest).mounts[0]
    assert _resolve_walk_dir(load_mounts_manifest(manifest), spec, None) == (
        tmp_path / "external" / "score_process+" / "docs_as_mount"
    )
