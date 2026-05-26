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

from pathlib import Path

from incremental import clean_builddir_if_stale, update_module_hash

_BUILD = Path("/build")
_MODULE = Path("/MODULE.bazel")
_LOCK = Path("/MODULE.bazel.lock")


def _simulate_old_state(fs, warnings: str | None) -> None:
    """Helper function to set up a build directory with an old hash and warnings."""

    fs.create_dir(_BUILD)
    fs.create_file(_MODULE, contents="stable")
    fs.create_file(_LOCK, contents="old lock")
    update_module_hash(_BUILD, [_MODULE, _LOCK])
    if warnings is not None:
        fs.create_file(_BUILD / "warnings.txt", contents=warnings)


def test_clean_removes_build_dir_when_previous_build_had_warnings(fs) -> None:
    """If warnings.txt exists and is not empty, the build dir is removed."""

    _simulate_old_state(fs, warnings="WARNING: something went wrong")

    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


def test_clean_keeps_build_dir_when_warnings_txt_is_empty(fs) -> None:
    """If warnings.txt exists and is empty, the build dir is kept."""

    _simulate_old_state(fs, warnings="")

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


def test_clean_is_noop_when_warnings_txt_is_absent(fs) -> None:
    """If warnings.txt does not exist, the build dir is kept (no error)."""

    _simulate_old_state(fs, warnings=None)

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


def test_clean_is_noop_when_build_dir_is_absent(fs) -> None:
    fs.create_file(_MODULE, contents="stable")

    clean_builddir_if_stale(_BUILD, [_MODULE])


def test_module_changed_removes_build_dir_when_one_sentinel_file_changed(fs) -> None:
    _simulate_old_state(fs, warnings=None)

    _LOCK.write_bytes(b"new lock")
    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert not _BUILD.exists()


def test_module_changed_keeps_build_dir_when_all_sentinel_files_unchanged(fs) -> None:
    _simulate_old_state(fs, warnings=None)

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


def test_module_change_after_successful_build_forces_clean(fs) -> None:
    _simulate_old_state(fs, warnings=None)

    _MODULE.write_bytes(b"version 2")
    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


def test_missing_hash_file_triggers_clean(fs) -> None:
    """If _build/ exists but hash file is absent, treat as stale (e.g. upgrade from old version)."""
    fs.create_dir(_BUILD)
    fs.create_file(_MODULE, contents="stable")
    # No hash file written

    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()
