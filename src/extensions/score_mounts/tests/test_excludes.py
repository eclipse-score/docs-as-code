# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Tests for structural source-directory exclusions."""

from pathlib import Path

from src.extensions.score_mounts import (
    _make_mount_entry,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    _nested_mount_excludes,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    _nested_mount_pattern,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    _primary_mount_excludes,  # pyright: ignore[reportPrivateUsage] - white-box unit test
)
from src.extensions.score_mounts._resolver import MountSpec


def _spec(mount_at: str) -> MountSpec:
    """Create the minimal mount specification used by path tests."""
    return MountSpec(src_root="docs", runtime_path="docs", mount_at=mount_at)


def test_nested_mount_pattern_only_matches_descendants(tmp_path: Path) -> None:
    """A mount excludes a child directory, not itself or a sibling."""
    parent = tmp_path / "parent"

    assert _nested_mount_pattern(parent, parent / "child") == "child/**"
    assert _nested_mount_pattern(parent, parent) is None
    assert _nested_mount_pattern(parent, tmp_path / "sibling") is None


def test_primary_mount_excludes_only_mounts_below_source(tmp_path: Path) -> None:
    """Only physically nested mounts are hidden from primary discovery."""
    source_dir = tmp_path / "docs"
    source_mounts = [
        (_spec("nested"), source_dir / "nested"),
        (_spec("external"), tmp_path / "external"),
    ]

    assert _primary_mount_excludes(source_dir, source_mounts) == ["nested/**"]


def test_parent_mount_excludes_nested_child_mount(tmp_path: Path) -> None:
    """A parent directory mount skips a child that has its own mount."""
    source_mounts = [
        (_spec("parent"), tmp_path / "parent"),
        (_spec("child"), tmp_path / "parent" / "child"),
        (_spec("other"), tmp_path / "other"),
    ]

    assert _nested_mount_excludes(0, source_mounts) == ["child/**"]
    assert _nested_mount_excludes(1, source_mounts) == []


def test_mount_entry_serializes_child_exclusions(tmp_path: Path) -> None:
    """Structural exclusions are passed to sphinx-mounts."""
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "index.rst").write_text("Index", encoding="utf-8")

    entry = _make_mount_entry(tmp_path, _spec("parent"), ("child/**",))

    assert entry["exclude"] == ["child/**"]
