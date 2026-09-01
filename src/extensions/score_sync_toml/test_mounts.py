# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
from pathlib import Path
from typing import Any, cast

import pytest
from sphinx.application import Sphinx

from src.extensions import score_sync_toml
from src.extensions.score_sync_toml import _mounts
from src.extensions.score_sync_toml._mounts import materialize_mounts


def test_materialize_mounts_serializes_structured_entries():
    fragment = materialize_mounts(
        [
            {
                "dir": 'docs/with "quotes"',
                "mount_at": "guide",
                "attach_to": "index",
                "entry_doc": "start",
            }
        ]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        "[[mounts]]\n"
        'dir = "docs/with \\"quotes\\""\n'
        'mount_at = "guide"\n'
        'attach_to = "index"\n'
        'entry_doc = "start"\n'
    )


def test_materialize_mounts_omits_default_fields():
    fragment = materialize_mounts(
        [{"dir": "docs", "mount_at": "guide", "attach_to": None, "entry_doc": "index"}]
    )

    assert fragment is not None
    assert (
        fragment.read_text(encoding="utf-8")
        == '[[mounts]]\ndir = "docs"\nmount_at = "guide"\n'
    )


def test_materialize_mounts_preserves_non_default_path_check():
    fragment = materialize_mounts(
        [{"dir": "docs", "mount_at": "guide", "path_check": "off"}]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        '[[mounts]]\ndir = "docs"\nmount_at = "guide"\npath_check = "off"\n'
    )


def test_materialize_mounts_maps_external_runfiles_path_to_bazel_bin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runfiles_dir = tmp_path / "runfiles"
    walk_dir = runfiles_dir / "score_process_description+" / "process"
    walk_dir.mkdir(parents=True)
    monkeypatch.setattr(_mounts, "find_git_root", lambda: None)
    monkeypatch.setattr(_mounts, "get_runfiles_dir", lambda: runfiles_dir)

    fragment = materialize_mounts(
        [
            {
                "dir": str(walk_dir),
                "mount_at": "process",
            }
        ]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        '[[mounts]]\ndir = "bazel-bin/external/score_process_description+/process"\nmount_at = "process"\n'
    )


def test_setup_skips_toml_sync_without_git_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ConfigWithoutTomlSync:
        suppress_warnings: list[str] = []

        @property
        def _raw_config(self) -> Any:
            raise AssertionError(
                "setup must not configure TOML sync without a Git worktree"
            )

    class AppWithoutGitWorktree:
        config = ConfigWithoutTomlSync()

        def connect(self, *args: Any, **kwargs: Any) -> None:
            raise AssertionError(
                "setup must not register TOML sync without a Git worktree"
            )

    monkeypatch.setattr(score_sync_toml, "find_git_root", lambda: None)

    metadata = score_sync_toml.setup(cast(Sphinx, AppWithoutGitWorktree()))

    assert metadata == {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
    assert AppWithoutGitWorktree.config.suppress_warnings == [
        "needs_config_writer.unsupported_type",
        "needs_config_writer.path_conversion",
    ]
