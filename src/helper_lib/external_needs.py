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

"""Translate Bazel data labels into paths for Sphinx-Needs inventories.

The Bazel action passes labels across the process boundary rather than paths:
the same label can resolve differently in the main repository and in an
external module's runfiles tree. This module parses that label once and uses
its repository, package, and target components to find the inventory file.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExternalNeedsSource:
    """The Bazel coordinates needed to locate one external Needs inventory.

    ``needs_json`` and ``needs_json_file`` are the established public inputs;
    ``<bundle>.__internal__.needs_local`` is the owner-only inventory produced
    for a documentation bundle. All three use the same runfiles resolution.
    """

    bazel_module: str  # Bazel repository/module name; empty in the main workspace.
    path_to_target: str  # Bazel package path, used as a runfiles subdirectory.
    target: str  # Inventory target name, which selects the artifact layout below.
    # A label beginning with `//` names a target in the main repository, whose
    # files live under `_main/…`. A label beginning with `@repo//` names an
    # external Bazel module, whose files live under `{bazel_module}+/…`.
    is_local: bool = False


def parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
    """Parse a supported Bazel inventory label, ignoring ordinary data labels.

    ``docs(data = [...])`` can contain both Bazel targets and source-file paths.
    Only the inventory target names handled below become external Needs
    sources; unrelated labels and files remain the responsibility of their
    existing consumers.
    """
    is_cross_module = s.startswith("@")
    is_local = s.startswith("//")
    if not is_cross_module and not is_local:
        # Local need, not external needs
        return None

    if "//" not in s or ":" not in s:
        raise ValueError(
            f"Unsupported external data dependency: '{s}'. Must contain '//' & ':'"
        )
    # Bazel's label form separates the repository/package from its target at
    # the colon. Preserve the package path because it is also part of the
    # target's runfiles location.
    repo_and_path, target = s.split(":", 1)
    repo, path_to_target = repo_and_path.split("//", 1)
    repo = repo.lstrip("@")

    # Public inventory targets keep their historical names. Bundle inventories
    # are private siblings whose suffix marks them as generated Needs outputs.
    # Other data targets are deliberately ignored by this extension.
    if target in ("needs_json", "needs_json_file") or target.endswith(
        ".__internal__.needs_local"
    ):
        return ExternalNeedsSource(
            bazel_module=repo,
            path_to_target=path_to_target,
            target=target,
            is_local=is_local,
        )
    return None


def parse_external_needs_labels(labels: list[str]) -> list[ExternalNeedsSource]:
    """Parse supported external-needs labels and ignore ordinary data labels."""
    return [
        source
        for label in labels
        if (source := parse_bazel_external_need(label)) is not None
    ]


def _runfiles_module_dir(source: ExternalNeedsSource) -> str:
    """Return the runfiles directory selected by the label's repository."""
    return "_main" if source.is_local else f"{source.bazel_module}+"


def external_needs_runfiles_path(
    runfiles_dir: Path, source: ExternalNeedsSource, *suffix: str
) -> Path:
    """Append the source label's runfiles coordinates and artifact suffix.

    Callers provide only the artifact layout after the Bazel target directory;
    this helper supplies the repository and package prefix shared by every
    supported inventory target.
    """
    return (
        runfiles_dir
        / _runfiles_module_dir(source)
        / source.path_to_target
        / Path(*suffix)
    )


def external_needs_source_path(
    runfiles_dir: Path | None, source: ExternalNeedsSource
) -> Path:
    """Resolve the JSON file layout for a supported external inventory.

    Public ``needs_json`` targets and private bundle exports both produce a
    Sphinx build directory. ``needs_json_file`` is already a file target and
    therefore resolves directly to ``needs.json`` in its package.
    """
    if runfiles_dir is None:
        raise ValueError("An external needs source has no runfiles root.")

    if source.target == "needs_json":
        suffix = (source.target, "_build", "needs", "needs.json")
    elif source.target == "needs_json_file":
        suffix = ("needs.json",)
    elif source.target.endswith(".__internal__.needs_local"):
        suffix = (source.target, "_build", "needs", "needs.json")
    else:
        raise ValueError(f"Unsupported external needs target: {source.target}")
    return external_needs_runfiles_path(runfiles_dir, source, *suffix)
