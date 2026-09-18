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

"""Shared parsing and path resolution for Bazel external documentation inputs."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExternalNeedsSource:
    bazel_module: str
    path_to_target: str
    target: str
    # True for a same-repo mount (`//pkg:needs_json`), whose runfiles live under
    # `_main/…`. False for a cross-module mount (`@repo//…:needs_json`), whose
    # runfiles live under `{bazel_module}+/…`.
    is_local: bool = False


def parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
    is_cross_module = s.startswith("@")
    is_local = s.startswith("//")
    if not is_cross_module and not is_local:
        # Local need, not external needs
        return None

    if "//" not in s or ":" not in s:
        raise ValueError(
            f"Unsupported external data dependency: '{s}'. Must contain '//' & ':'"
        )
    repo_and_path, target = s.split(":", 1)
    repo, path_to_target = repo_and_path.split("//", 1)
    repo = repo.lstrip("@")

    if target in ("needs_json", "needs_json_file"):
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
    return "_main" if source.is_local else f"{source.bazel_module}+"


def external_needs_runfiles_path(
    runfiles_dir: Path, source: ExternalNeedsSource, *suffix: str
) -> Path:
    return (
        runfiles_dir
        / _runfiles_module_dir(source)
        / source.path_to_target
        / Path(*suffix)
    )


def external_needs_source_path(
    runfiles_dir: Path | None, source: ExternalNeedsSource
) -> Path:
    """Derive a source path from the Bazel runfiles root."""
    if runfiles_dir is None:
        raise ValueError("An external needs source has no runfiles root.")

    if source.target == "needs_json":
        suffix = (source.target, "_build", "needs", "needs.json")
    elif source.target == "needs_json_file":
        suffix = ("needs.json",)
    else:
        raise ValueError(f"Unsupported external needs target: {source.target}")
    return external_needs_runfiles_path(runfiles_dir, source, *suffix)
