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
    # `needs_json` and `needs_json_file` are the public inventory labels.
    # Bazel's analysis-time resolver replaces public docs targets with the
    # private inventory label carried by their LocalNeedsInfo provider.
    target: str
    # True for a same-repo mount (`//pkg:needs_json`), whose runfiles live under
    # `_main/…`. False for a cross-module mount (`@repo//…:needs_json`), whose
    # runfiles live under `{bazel_module}+/…`.
    is_local: bool = False


def parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
    """Recognize supported Bazel inventory labels and ignore ordinary data.

    ``needs_json`` and ``needs_json_file`` are both accepted inventory labels.
    The docs macro reports inventory labels in the deprecated ``data`` input
    route before combining labels with explicit ``external_needs``.
    """
    # Analysis-time provider labels may use Bazel's canonical ``@@`` spelling.
    # The runfiles resolver uses the corresponding public label form instead.
    if s.startswith("@@//"):
        s = s[2:]
    elif s.startswith("@@"):
        s = s[1:]

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
    if source.is_local:
        return "_main"
    # Provider labels may already contain Bazel's canonical repository name,
    # including the ``+`` used for Bzlmod runfiles. Older public labels contain
    # the apparent module name and still need that suffix added here.
    if source.bazel_module.endswith("+"):
        return source.bazel_module
    return f"{source.bazel_module}+"


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
    """Find the inventory JSON emitted by the selected Bazel target.

    The public `needs_json` target is a directory output containing
    `_build/needs/needs.json`. The `needs_json_file` target and private
    bundle-local exports point directly at JSON file artifacts.
    """
    if runfiles_dir is None:
        raise ValueError("An external needs source has no runfiles root.")

    if source.target == "needs_json":
        suffix = (source.target, "_build", "needs", "needs.json")
    elif source.target == "needs_json_file":
        suffix = ("needs.json",)
    elif source.target.endswith(".__internal__.needs_local"):
        # The genrule exposes `<target>/needs.json`. This target-scoped path is
        # independent of the private Sphinx builder's output directory layout.
        suffix = (source.target, "needs.json")
    else:
        raise ValueError(f"Unsupported external needs target: {source.target}")
    return external_needs_runfiles_path(runfiles_dir, source, *suffix)
