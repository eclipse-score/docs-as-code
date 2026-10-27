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

import json
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem as FFS
from score_pytest.attribute_plugin import add_test_properties

from src.docs_cli import cli as docs_cli
from src.docs_cli.cli import (
    clean_builddir_if_stale,
    mounted_watch_dirs,
    update_module_hash,
)

_BUILD = Path("/build")
_MODULE = Path("/MODULE.bazel")
_LOCK = Path("/MODULE.bazel.lock")
_WORKSPACE = Path("/workspace")


@pytest.fixture
def docs_workspace(fs: FFS, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create the minimal workspace environment used by ``cli.main``."""
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(_WORKSPACE))
    monkeypatch.setenv("PACKAGE_DIR", "component")
    monkeypatch.setenv("SOURCE_DIRECTORY", "docs")
    monkeypatch.setenv("DATA", "[]")
    monkeypatch.delenv("SCORE_CODE_FILE_LISTS", raising=False)
    fs.create_dir(_WORKSPACE / "component")
    for name in ("MODULE.bazel", "MODULE.bazel.lock", "component/BUILD"):
        fs.create_file(_WORKSPACE / name, contents="stable")
    return _WORKSPACE


def _simulate_old_state(fs: FFS, warnings: str | None) -> None:
    """Helper function to set up a build directory with an old hash and warnings."""

    fs.create_dir(_BUILD)
    fs.create_file(_MODULE, contents="stable")
    fs.create_file(_LOCK, contents="old lock")
    update_module_hash(_BUILD, [_MODULE, _LOCK])
    if warnings is not None:
        fs.create_file(_BUILD / "warnings.txt", contents=warnings)


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_clean_removes_build_dir_when_previous_build_had_warnings(
    fs: FFS,
) -> None:
    """If warnings.txt exists and is not empty, the build dir is removed."""

    _simulate_old_state(fs, warnings="WARNING: something went wrong")

    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_clean_keeps_build_dir_when_warnings_txt_is_empty(fs: FFS) -> None:
    """If warnings.txt exists and is empty, the build dir is kept."""

    _simulate_old_state(fs, warnings="")

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_clean_is_noop_when_warnings_txt_is_absent(fs: FFS) -> None:
    """If warnings.txt does not exist, the build dir is kept (no error)."""

    _simulate_old_state(fs, warnings=None)

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_clean_is_noop_when_build_dir_is_absent(fs: FFS) -> None:
    """Test clean is noop when build dir is absent."""
    fs.create_file(_MODULE, contents="stable")

    clean_builddir_if_stale(_BUILD, [_MODULE])


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_module_changed_removes_build_dir_when_one_sentinel_file_changed(
    fs: FFS,
) -> None:
    """Test module changed removes build dir when one sentinel file changed."""
    _simulate_old_state(fs, warnings=None)

    _LOCK.write_bytes(b"new lock")
    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert not _BUILD.exists()


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_module_changed_keeps_build_dir_when_all_sentinel_files_unchanged(
    fs: FFS,
) -> None:
    """Test module changed keeps build dir when all sentinel files unchanged."""
    _simulate_old_state(fs, warnings=None)

    clean_builddir_if_stale(_BUILD, [_MODULE, _LOCK])

    assert _BUILD.exists()


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_module_change_after_successful_build_forces_clean(fs: FFS) -> None:
    """Test module change after successful build forces clean."""
    _simulate_old_state(fs, warnings=None)

    _MODULE.write_bytes(b"version 2")
    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_missing_hash_file_triggers_clean(fs: FFS) -> None:
    """If _build/ exists but hash file is absent, treat as stale (e.g. upgrade from old version)."""
    fs.create_dir(_BUILD)
    fs.create_file(_MODULE, contents="stable")
    # No hash file written

    clean_builddir_if_stale(_BUILD, [_MODULE])

    assert not _BUILD.exists()


@pytest.mark.parametrize(
    "action,builder",
    [
        ("incremental", "html"),
        ("check", "needs"),
        ("linkcheck", "linkcheck"),
    ],
)
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_successful_build_reuses_output_until_module_changes(
    docs_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    builder: str,
) -> None:
    """A successful CLI run records a reusable cache and invalidates it on changes."""
    monkeypatch.setenv("ACTION", action)
    build_dir = docs_workspace / "component/_build"
    reused: list[bool] = []

    def build(arguments: list[str]) -> int:
        assert arguments[-2:] == ["-b", builder]
        reused.append((build_dir / "output").exists())
        build_dir.mkdir(exist_ok=True)
        (build_dir / "output").touch()
        return 0

    monkeypatch.setattr(docs_cli, "sphinx_main", build)

    # The first run creates the output and records its module-input hash.
    assert docs_cli.main([]) == 0
    # An unchanged successful build can reuse the existing output directory.
    assert docs_cli.main([]) == 0
    (docs_workspace / "MODULE.bazel.lock").write_text("changed")
    # A changed module input forces a clean build before Sphinx runs again.
    assert docs_cli.main([]) == 0
    assert reused == [False, True, False]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_mounted_watch_dirs_match_sphinx_mount_paths(tmp_path: Path) -> None:
    """Test mounted watch dirs match sphinx mount paths."""
    manifest_path = tmp_path / "_mounts_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "mounts": [
                    {
                        "src_root": "primary/docs",
                        "runtime_path": "primary/docs",
                        "mount_at": "",
                        "attach_to": "",
                        "entry_doc": "index",
                        "external": False,
                        "repository": "",
                        "generated": False,
                        "data": ["bazel-out/k8-fastbuild/bin/primary/generated.rst"],
                        "root_bundle": True,
                        "bundle": {
                            "label": "@@//:root_bundle",
                            "name": "root_bundle",
                            "code_targets": [],
                        },
                    },
                    {
                        "src_root": "extensions/local/docs",
                        "runtime_path": "extensions/local/docs",
                        "mount_at": "local",
                        "attach_to": "",
                        "entry_doc": "index",
                        "external": False,
                        "repository": "",
                        "generated": False,
                        "data": [],
                        "root_bundle": False,
                        "bundle": {
                            "label": "@@//:local_bundle",
                            "name": "local_bundle",
                            "code_targets": [],
                        },
                    },
                    {
                        "src_root": "external/vendor+/docs",
                        "runtime_path": "../vendor+/docs",
                        "mount_at": "external",
                        "attach_to": "",
                        "entry_doc": "index",
                        "external": True,
                        "repository": "vendor+",
                        "generated": False,
                        "data": [],
                        "root_bundle": False,
                        "bundle": {
                            "label": "@@vendor+//:docs_bundle",
                            "name": "docs_bundle",
                            "code_targets": [],
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    runfiles_dir = tmp_path / "runfiles"

    assert mounted_watch_dirs(manifest_path, workspace, runfiles_dir) == [
        str(workspace / "extensions/local/docs"),
        str(runfiles_dir / "vendor+" / "docs"),
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_mounted_watch_dirs_use_data_directories_for_pure_data_bundles(
    tmp_path: Path,
) -> None:
    """Test mounted watch dirs use data directories for pure data bundles."""
    manifest_path = tmp_path / "_mounts_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "mounts": [
                    {
                        "src_root": "",
                        "runtime_path": "__data__/pkg/data_bundle",
                        "mount_at": "generated",
                        "attach_to": "",
                        "entry_doc": "index",
                        "external": False,
                        "repository": "",
                        "generated": False,
                        "data": ["bazel-out/k8-fastbuild/bin/pkg/generated/index.rst"],
                        "root_bundle": False,
                        "bundle": {
                            "label": "@@//:data_bundle",
                            "name": "data_bundle",
                            "code_targets": [],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    runfiles_dir = tmp_path / "runfiles"

    assert mounted_watch_dirs(manifest_path, workspace, runfiles_dir) == [
        str(workspace / "bazel-bin/pkg/generated")
    ]


def test_coverage_summary_is_a_sentinel_preserved_during_output_cleanup(
    docs_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raw reports are read at startup; only summarized changes invalidate output."""
    monkeypatch.setenv("ACTION", "incremental")
    file_lists = docs_workspace / "files.json"
    file_lists.write_text(
        json.dumps(
            {
                "version": 1,
                "code_file_lists": [
                    {
                        "primary_need_id": "mod__test",
                        "files": [{"repository": "_main", "path": "source.cc"}],
                    }
                ],
            }
        )
    )
    monkeypatch.setenv("SCORE_CODE_FILE_LISTS", str(file_lists))
    report = docs_workspace / "coverage-report/coverage_report.dat"
    report.parent.mkdir()
    original = "SF:source.cc\nDA:1,1\nDA:2,1\nDA:3,0\n"
    report.write_text(original)
    build_dir = docs_workspace / "component/_build"
    summary = build_dir / "coverage_summary.json"
    reused = []

    def build(arguments: list[str]) -> int:
        # Coverage is an optional extension. Its input is available at the
        # conventional path without adding overrides unknown to other builds.
        assert not any("score_coverage_summary" in argument for argument in arguments)
        assert summary.is_file()
        reused.append((build_dir / "output").exists())
        build_dir.mkdir(exist_ok=True)
        (build_dir / "output").touch()
        return 0

    monkeypatch.setattr(docs_cli, "sphinx_main", build)
    assert docs_cli.main([]) == 0
    initial = summary.read_bytes()
    initial_mtime = summary.stat().st_mtime_ns
    report.write_text(original.replace("DA:1,1", "DA:1,900"))
    assert docs_cli.main([]) == 0
    assert summary.read_bytes() == initial
    assert summary.stat().st_mtime_ns == initial_mtime
    report.write_text(original.replace("DA:1,1", "DA:1,0"))
    assert docs_cli.main([]) == 0
    assert (
        json.loads(summary.read_bytes())["coverage_summaries"][0]["lines"]["percent"]
        == 33
    )
    report.unlink()
    assert docs_cli.main([]) == 0
    assert json.loads(summary.read_bytes())["coverage_summaries"][0]["files"] == {
        "total": 1,
        "measured": 0,
    }
    assert docs_cli.main([]) == 0
    assert reused == [False, True, False, False, True]

    # A malformed report leaves both cached documentation and summary intact.
    previous = summary.read_bytes()
    report.write_text("SF:source.cc\nDA:invalid\n")
    with pytest.raises(ValueError):
        docs_cli.main([])
    assert summary.read_bytes() == previous
    assert (build_dir / "output").exists()


def test_cleanup_preserves_generated_sentinels_and_removes_stale_outputs(
    fs: FFS,
) -> None:
    """Generated inputs survive cleanup with their bytes and modification time intact."""
    summary = _BUILD / "coverage_summary.json"
    fs.create_file(summary, contents="previous")
    update_module_hash(_BUILD, [summary])
    fs.create_file(_BUILD / "index.html", contents="stale")
    fs.create_file(_BUILD / "nested/page.html", contents="stale")
    fs.create_file("/external/keep.txt", contents="keep")
    fs.create_symlink(_BUILD / "external", "/external")
    summary.write_text("changed")
    modified = summary.stat().st_mtime_ns

    clean_builddir_if_stale(_BUILD, [summary])

    assert set(_BUILD.iterdir()) == {summary}
    assert summary.read_text() == "changed"
    assert summary.stat().st_mtime_ns == modified
    assert Path("/external/keep.txt").read_text() == "keep"


@pytest.mark.parametrize("action", ["check", "linkcheck"])
def test_checks_ignore_coverage_even_with_a_configured_file_list(
    docs_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    """Coverage cannot break validation or link checks that do not display it."""
    monkeypatch.setenv("ACTION", action)
    monkeypatch.setenv(
        "SCORE_CODE_FILE_LISTS", str(docs_workspace / "missing-files.json")
    )
    build_dir = docs_workspace / "component/_build"

    def build(arguments: list[str]) -> int:
        assert not any("score_coverage_summary" in argument for argument in arguments)
        build_dir.mkdir(exist_ok=True)
        return 0

    monkeypatch.setattr(docs_cli, "sphinx_main", build)
    assert docs_cli.main([]) == 0
    assert not (build_dir / "coverage_summary.json").exists()
