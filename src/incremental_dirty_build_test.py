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

# Unit Tests of incremental.py

import json
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem as FFS

from incremental import (
    _mounted_watch_dirs,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    clean_builddir_if_stale,
    update_module_hash,
)

_BUILD = Path("/build")
_MODULE = Path("/MODULE.bazel")
_LOCK = Path("/MODULE.bazel.lock")


def _simulate_old_state(fs: FFS, warnings: str | None) -> None:
    """Helper function to set up a build directory with an old hash and warnings."""

    fs.create_dir(_BUILD)
    fs.create_file(_MODULE, contents="stable")
    fs.create_file(_LOCK, contents="old lock")
    update_module_hash(_BUILD, [_MODULE, _LOCK])
    if warnings is not None:
        fs.create_file(_BUILD / "warnings.txt", contents=warnings)


def test_clean_removes_build_dir_when_previous_build_had_warnings(
    fs: FFS,
) -> None:
    """If warnings.txt exists and is not empty, the build dir is removed."""

    _simulate_old_state(fs, warnings="WARNING: something went wrong")

    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


def test_clean_keeps_build_dir_when_warnings_txt_is_empty(fs: FFS) -> None:
    """If warnings.txt exists and is empty, the build dir is kept."""

    _simulate_old_state(fs, warnings="")

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


def test_clean_is_noop_when_warnings_txt_is_absent(fs: FFS) -> None:
    """If warnings.txt does not exist, the build dir is kept (no error)."""

    _simulate_old_state(fs, warnings=None)

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


def test_clean_is_noop_when_build_dir_is_absent(fs: FFS) -> None:
    fs.create_file(_MODULE, contents="stable")

    clean_builddir_if_stale(_BUILD, [_MODULE])


def test_module_changed_removes_build_dir_when_one_sentinel_file_changed(
    fs: FFS,
) -> None:
    _simulate_old_state(fs, warnings=None)

    _LOCK.write_bytes(b"new lock")
    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert not _BUILD.exists()


def test_module_changed_keeps_build_dir_when_all_sentinel_files_unchanged(
    fs: FFS,
) -> None:
    _simulate_old_state(fs, warnings=None)

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


def test_module_change_after_successful_build_forces_clean(fs: FFS) -> None:
    _simulate_old_state(fs, warnings=None)

    _MODULE.write_bytes(b"version 2")
    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


def test_missing_hash_file_triggers_clean(fs: FFS) -> None:
    """If _build/ exists but hash file is absent, treat as stale (e.g. upgrade from old version)."""
    fs.create_dir(_BUILD)
    fs.create_file(_MODULE, contents="stable")
    # No hash file written

    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


def test_mounted_watch_dirs_match_sphinx_mount_paths(tmp_path: Path) -> None:
    manifest_path = tmp_path / "_mounts_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "mounts": [
                    {
                        "src_root": "extensions/local/docs",
                        "runtime_path": "extensions/local/docs",
                        "mount_at": "local",
                    },
                    {
                        "src_root": "external/vendor+/docs",
                        "runtime_path": "../vendor+/docs",
                        "mount_at": "external",
                        "external": True,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    runfiles_dir = tmp_path / "runfiles"

    assert _mounted_watch_dirs(manifest_path, workspace, runfiles_dir) == [
        str(workspace / "extensions/local/docs"),
        str(runfiles_dir / "vendor+" / "docs"),
    ]


def test_mounted_watch_dirs_use_data_directories_for_pure_data_bundles(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "_mounts_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "mounts": [
                    {
                        "src_root": "",
                        "runtime_path": "__data__/pkg/data_bundle",
                        "mount_at": "generated",
                        "data": ["bazel-out/k8-fastbuild/bin/pkg/generated/index.rst"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    runfiles_dir = tmp_path / "runfiles"

    assert _mounted_watch_dirs(manifest_path, workspace, runfiles_dir) == [
        str(workspace / "bazel-bin/pkg/generated")
    ]
