# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""Parse the MOUNTS env-var payload supplied by docs.bzl and resolve each
Bazel label to its runfiles-relative path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.helper_lib import get_runfiles_dir


@dataclass(frozen=True)
class MountSpec:
    label: str
    mount_at: str
    attach_to: str | None = None
    entry_doc: str = "index"
    src_root: str | None = None


def parse_mounts_source(value: str) -> list[MountSpec]:
    """Decode the MOUNTS env-var JSON into MountSpec instances."""
    if not value or value.strip() in ("", "[]"):
        return []
    raw = json.loads(value)
    if not isinstance(raw, list):
        raise ValueError(
            f"MOUNTS must decode to a list, got {type(raw).__name__}: {raw!r}"
        )
    out: list[MountSpec] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValueError(f"MOUNTS entry must be a dict, got {entry!r}")
        if "label" not in entry or "mount_at" not in entry:
            raise ValueError(
                f"MOUNTS entry missing required keys 'label'/'mount_at': {entry!r}"
            )
        out.append(
            MountSpec(
                label=entry["label"],
                mount_at=entry["mount_at"],
                attach_to=entry.get("attach_to") or None,
                entry_doc=entry.get("entry_doc") or "index",
                src_root=entry.get("src_root") or None,
            )
        )
    return out


def label_to_runfile_path(label: str) -> str:
    """Convert a Bazel label to its runfiles-relative path.

    Main-workspace labels go under ``_main/...``; external module labels
    go under ``<module>+/...``. The target name is appended as the final
    path segment.
    """
    if label.startswith("@"):
        rest = label[1:]
        if "//" not in rest:
            raise ValueError(f"malformed external label: {label!r}")
        module, path_and_target = rest.split("//", 1)
        prefix = f"{module}+"
    elif label.startswith("//"):
        path_and_target = label[2:]
        prefix = "_main"
    else:
        raise ValueError(f"label must start with '//' or '@': {label!r}")

    if ":" in path_and_target:
        path, target = path_and_target.split(":", 1)
    else:
        path = path_and_target
        target = path.rsplit("/", 1)[-1] if "/" in path else path

    parts = [prefix]
    if path:
        parts.append(path)
    parts.append(target)
    return "/".join(parts)


def label_to_bazel_bin_path(label: str) -> str:
    """Convert a Bazel label to its bazel-bin-relative path.

    Returns a workspace-root-relative path of the form ``bazel-bin/<pkg>/<target>``.

    Examples::

        "//src:docs_dir"                  -> "bazel-bin/src/docs_dir"
        "//:docs_dir"                     -> "bazel-bin/docs_dir"
        "@score_process//:docs_sources"   -> "bazel-bin/external/score_process+/docs_sources"
        "@x//foo/bar:baz"                 -> "bazel-bin/external/x+/foo/bar/baz"
    """
    if label.startswith("@"):
        rest = label[1:]
        if "//" not in rest:
            raise ValueError(f"malformed external label: {label!r}")
        module, path_and_target = rest.split("//", 1)
        prefix = f"bazel-bin/external/{module}+"
    elif label.startswith("//"):
        path_and_target = label[2:]
        prefix = "bazel-bin"
    else:
        raise ValueError(f"label must start with '//' or '@': {label!r}")

    if ":" in path_and_target:
        path, target = path_and_target.split(":", 1)
    else:
        path = path_and_target
        target = path.rsplit("/", 1)[-1] if "/" in path else path

    parts = [prefix]
    if path:
        parts.append(path)
    parts.append(target)
    return "/".join(parts)


def resolve_mount_dir(spec: MountSpec) -> Path:
    """Resolve the runfile path of ``spec.label`` to an absolute filesystem path."""
    return get_runfiles_dir() / label_to_runfile_path(spec.label)
