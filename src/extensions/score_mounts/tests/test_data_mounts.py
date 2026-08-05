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
"""Tests for ``_resolve_data_mounts`` in the ``score_mounts`` extension."""

from pathlib import Path

import pytest

from src.extensions.score_mounts import _resolve_data_mounts
from src.extensions.score_mounts._resolver import MountSpec


def test_missing_data_file_raises(tmp_path: Path) -> None:
    """A manifest with an unavailable data file must fail fast."""
    manifest_mounts = [
        MountSpec(
            src_root="",
            runtime_path="",
            mount_at="missing",
            data=["bazel-out/k8-fastbuild/bin/nonexistent.rst"],
        )
    ]

    with pytest.raises(ValueError, match="resolved data file does not exist"):
        _resolve_data_mounts(
            type("Manifest", (), {"mounts": manifest_mounts})(),
            tmp_path,
            tmp_path,
        )


def test_existing_data_file_resolved(tmp_path: Path) -> None:
    """An existing data file resolves to its parent directory."""
    data_file = tmp_path / "bazel-bin" / "file.rst"
    data_file.parent.mkdir(parents=True)
    data_file.write_text("..", encoding="utf-8")

    manifest_mounts = [
        MountSpec(
            src_root="",
            runtime_path="",
            mount_at="exists",
            data=["bazel-out/k8-fastbuild/bin/file.rst"],
        )
    ]

    mounts = _resolve_data_mounts(
        type("Manifest", (), {"mounts": manifest_mounts})(),
        tmp_path,
        tmp_path / "runfiles",
    )

    assert str(tmp_path / "bazel-bin") in mounts