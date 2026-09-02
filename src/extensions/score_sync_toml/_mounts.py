# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Serialize Bazel-derived mount metadata for ``needs-config-writer``."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sphinx.config import Config

from src.helper_lib import find_git_root, get_runfiles_dir


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_path(path: Path) -> str:
    """Derive a stable TOML path from a resolved runtime path."""
    resolved_path = path.resolve()
    git_root = find_git_root()
    if git_root is not None:
        try:
            return str(resolved_path.relative_to(git_root))
        except ValueError:
            pass

    try:
        external_path = resolved_path.relative_to(get_runfiles_dir())
    except ValueError:
        return str(resolved_path)
    if external_path.parts[0] == "_main":
        return str(Path(*external_path.parts[1:]))
    return "bazel-bin/external/" + str(external_path)


def _toml_dir(entry: dict[str, Any]) -> str:
    """Derive a stable TOML directory from a resolved mount entry."""
    return _toml_path(Path(entry["dir"]))


def materialize_mounts(entries: list[dict[str, Any]]) -> Path | None:
    """Write resolved mounts as a temporary, Git-root-relative TOML merge file."""
    if not entries:
        return None
    lines: list[str] = []
    for entry in entries:
        source_files = entry.get("files", [])
        lines.extend(
            [
                "[[mounts]]",
            ]
        )
        if source_files:
            # Preserve explicit source mounts as a file allowlist in the
            # generated TOML instead of widening them back to a directory.
            files = ", ".join(
                _toml_string(_toml_path(Path(source_file)))
                for source_file in source_files
            )
            lines.append(f"files = [{files}]")
        else:
            lines.append(f"dir = {_toml_string(_toml_dir(entry))}")
        lines.append(f"mount_at = {_toml_string(entry['mount_at'])}")
        if entry.get("attach_to"):
            lines.append(f"attach_to = {_toml_string(entry['attach_to'])}")
        if entry.get("entry_doc", "index") != "index":
            lines.append(f"entry_doc = {_toml_string(entry['entry_doc'])}")
        lines.append("")
    outdir = Path(tempfile.mkdtemp(prefix="score_sync_toml_"))
    fragment = outdir / "score_mounts.toml"
    fragment.write_text("\n".join(lines), encoding="utf-8")
    return fragment


def register_mounts(config: Config) -> None:
    """Merge configured mount entries into the generated ``ubproject.toml``."""
    fragment = materialize_mounts(config.mounts)
    if fragment is not None:
        config.needscfg_merge_toml_files.append(str(fragment))
