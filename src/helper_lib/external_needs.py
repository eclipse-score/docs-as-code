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

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TypeGuard, cast


@dataclass
class ExternalNeedsSource:
    bazel_module: str
    path_to_target: str
    target: str
    # True for a same-repo mount (`//pkg:needs_json`), whose runfiles live under
    # `_main/…`. False for a cross-module mount (`@repo//…:needs_json`), whose
    # runfiles live under `{bazel_module}+/…`.
    is_local: bool = False
    resolved_path: Path | None = None


def parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
    is_cross_module = s.startswith("@")
    is_local = s.startswith("//")
    if not is_cross_module and not is_local:
        # Local need, not external needs
        return None

    if "//" not in s or ":" not in s:
        raise ValueError(
            f"Unsuported external data dependency: '{s}'. Must contain '//' & ':'"
        )
    repo_and_path, target = s.split(":", 1)
    repo, path_to_target = repo_and_path.split("//", 1)
    repo = repo.lstrip("@")

    if target in ("needs_json", "needs_json_file", "docs_sources"):
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
    """Return a source's resolved path or derive it from the runfiles root."""
    if source.resolved_path is not None:
        return source.resolved_path
    if runfiles_dir is None:
        raise ValueError(
            "An external needs source has no resolved path or runfiles root."
        )

    if source.target == "needs_json":
        suffix = (source.target, "_build", "needs", "needs.json")
    elif source.target == "needs_json_file":
        suffix = ("needs.json",)
    elif source.target == "docs_sources":
        suffix = ()
    else:
        raise ValueError(f"Unsupported external needs target: {source.target}")
    return external_needs_runfiles_path(runfiles_dir, source, *suffix)


def resolve_external_needs_sources(
    sources: list[ExternalNeedsSource], runfiles_dir: Path
) -> list[ExternalNeedsSource]:
    """Attach absolute runfiles paths to parsed external-needs sources."""
    return [
        replace(
            source,
            resolved_path=external_needs_source_path(runfiles_dir, source),
        )
        for source in sources
    ]


def serialize_external_needs_sources(
    sources: list[ExternalNeedsSource],
) -> str:
    """Serialize external-needs descriptors for a Sphinx config value."""
    return json.dumps(
        [
            {
                "bazel_module": source.bazel_module,
                "path_to_target": source.path_to_target,
                "target": source.target,
                "is_local": source.is_local,
                "resolved_path": (
                    str(source.resolved_path)
                    if source.resolved_path is not None
                    else None
                ),
            }
            for source in sources
        ]
    )


def _deserialize_external_needs_source(
    value: Mapping[str, object],
) -> ExternalNeedsSource:
    string_fields = ("bazel_module", "path_to_target", "target")
    fields: dict[str, str] = {}
    for field in string_fields:
        field_value = value.get(field)
        if not isinstance(field_value, str):
            raise ValueError(
                f"External needs descriptor field '{field}' must be a string."
            )
        fields[field] = field_value

    is_local = value.get("is_local")
    if not isinstance(is_local, bool):
        raise ValueError(
            "External needs descriptor field 'is_local' must be a boolean."
        )

    resolved_path = value.get("resolved_path")
    if resolved_path is not None and not isinstance(resolved_path, str):
        raise ValueError(
            "External needs descriptor field 'resolved_path' must be a string or null."
        )

    return ExternalNeedsSource(
        **fields,
        is_local=is_local,
        resolved_path=Path(resolved_path) if resolved_path else None,
    )


def _is_descriptor_list(
    value: object,
) -> TypeGuard[list[Mapping[str, object]]]:
    if not isinstance(value, list):
        return False
    items = cast(list[object], value)
    return all(isinstance(item, Mapping) for item in items)


def parse_external_needs_source_config(
    raw: str,
) -> list[ExternalNeedsSource]:
    """Parse the descriptor JSON supplied by the documentation CLI."""
    if raw in ("", "[]"):
        return []

    value: object = json.loads(raw)
    if not _is_descriptor_list(value):
        raise ValueError(
            "External needs configuration must contain descriptor objects."
        )
    return [_deserialize_external_needs_source(item) for item in value]
