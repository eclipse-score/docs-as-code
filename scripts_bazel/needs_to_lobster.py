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

"""Convert a sphinx-needs ``needs.json`` into a LOBSTER ``lobster-req-trace`` file.

Data flow::

    docs build  ->  sphinx-needs writes needs.json  (single source of truth)
    this tool   ->  needs.json  ->  <module>.lobster (lobster-req-trace, v3)
    LOBSTER CLI ->  lobster-report / lobster-ci-report over all *.lobster

The converter reads the already metamodel-validated ``needs.json`` and emits the
LOBSTER common interchange format so ``lobster-report`` can aggregate the
sphinx-needs requirements with the code/test ``.lobster`` artifacts produced by
``rules_score``. Authoring (RST) and rendering (sphinx-needs dashboards) are
untouched -- LOBSTER only sits downstream of ``needs.json``.

Licensing note: LOBSTER is AGPLv3. This converter deliberately produces the
plain ``.lobster`` JSON via the documented schema and never imports the LOBSTER
Python packages, keeping the Apache-2.0 code at arm's length from the AGPL tool.
The emitted files are consumed by the LOBSTER CLI as an external process.

Schema reference: LOBSTER ``lobster-req-trace``, item version 3
(``tag``, ``location``, ``name``, ``refs``, ``just_up``/``just_down``/
``just_global``, plus requirement ``framework``/``kind``/``text``/``status``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# LOBSTER lobster-req-trace item schema version we emit (see documentation/schemas.md).
_LOBSTER_SCHEMA = "lobster-req-trace"
_LOBSTER_VERSION = 3
_GENERATOR = "needs_to_lobster"

# sphinx-needs link fields treated as up-traces (child -> parent) by default.
# ``satisfies`` is how tool_req__* needs reference their process gd_req__* parents.
_DEFAULT_UP_LINKS = ("satisfies",)

# Need fields that may already carry LOBSTER-style justifications, if authored.
_JUST_FIELDS = ("just_up", "just_down", "just_global")


def _select_version(needs_data: dict[str, Any], version: str | None) -> dict[str, Any]:
    """Return the ``versions`` entry to convert.

    Uses ``version`` when given, else ``current_version``, else the last key.
    """
    versions = needs_data.get("versions")
    if not versions:
        raise ValueError("needs.json contains no 'versions' object")
    if version is not None:
        if version not in versions:
            raise ValueError(f"version {version!r} not found in needs.json")
        return versions[version]
    current = needs_data.get("current_version")
    if current and current in versions:
        return versions[current]
    return versions[list(versions)[-1]]


def _as_id_list(value: Any) -> list[str]:
    """Normalise a sphinx-needs link field into a list of target ids.

    Link fields may be a list, a comma-separated string, or a single id.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]


def _location(need: dict[str, Any]) -> dict[str, Any]:
    """Build a LOBSTER 'file' source reference from a need's docname/lineno."""
    docname = need.get("docname")
    filename = f"{docname}.rst" if docname else "unknown"
    lineno = need.get("lineno")
    return {
        "kind": "file",
        "file": filename,
        "line": int(lineno) if isinstance(lineno, int) else None,
        "column": None,
    }


def _refs(need: dict[str, Any], namespace: str, up_links: tuple[str, ...]) -> list[str]:
    """Collect up-trace targets from the configured link fields as LOBSTER tags."""
    refs: list[str] = []
    seen: set[str] = set()
    for field in up_links:
        for target in _as_id_list(need.get(field)):
            tag = f"{namespace} {target}"
            if tag not in seen:
                seen.add(tag)
                refs.append(tag)
    return refs


def _text(need: dict[str, Any]) -> str | None:
    """Return the need body text, tolerating sphinx-needs field naming."""
    for field in ("content", "description"):
        value = need.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return None


def need_to_item(
    need: dict[str, Any],
    namespace: str,
    up_links: tuple[str, ...],
) -> dict[str, Any]:
    """Convert a single sphinx-needs need into a LOBSTER requirement item."""
    need_id = str(need["id"])
    item: dict[str, Any] = {
        "tag": f"{namespace} {need_id}",
        "location": _location(need),
        "name": need.get("title") or need_id,
        "messages": [],
        "just_up": _as_id_list(need.get("just_up")),
        "just_down": _as_id_list(need.get("just_down")),
        "just_global": _as_id_list(need.get("just_global")),
        "refs": _refs(need, namespace, up_links),
        "framework": "sphinx-needs",
        "kind": need.get("type") or "need",
        "text": _text(need),
        "status": need.get("status"),
    }
    return item


def convert(
    needs_data: dict[str, Any],
    namespace: str = "req",
    up_links: tuple[str, ...] = _DEFAULT_UP_LINKS,
    include_types: set[str] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Convert a parsed ``needs.json`` document into a lobster-req-trace document."""
    version_data = _select_version(needs_data, version)
    needs = version_data.get("needs", {})
    items = [
        need_to_item(need, namespace, up_links)
        for need in needs.values()
        if include_types is None or need.get("type") in include_types
    ]
    return {
        "data": items,
        "generator": _GENERATOR,
        "schema": _LOBSTER_SCHEMA,
        "version": _LOBSTER_VERSION,
    }


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _resolve(path: Path) -> Path:
    """Resolve a relative path against the invocation directory.

    Under ``bazel run`` the process working directory is the runfiles tree, so
    relative paths would resolve there instead of where the user invoked the
    command. Bazel exposes the original directory via ``BUILD_WORKING_DIRECTORY``;
    resolve relative paths against it when present so ``--needs-json``/``--output``
    behave as expected. Absolute paths are returned unchanged.
    """
    if path.is_absolute():
        return path
    base = os.environ.get("BUILD_WORKING_DIRECTORY")
    return Path(base) / path if base else path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a sphinx-needs needs.json into a LOBSTER "
            "lobster-req-trace (.lobster) file."
        )
    )
    parser.add_argument(
        "--needs-json",
        required=True,
        type=Path,
        help="Path to the input needs.json produced by the docs build.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to the output .lobster file (default: stdout).",
    )
    parser.add_argument(
        "--namespace",
        default="req",
        help="LOBSTER tag namespace for the emitted items (default: 'req').",
    )
    parser.add_argument(
        "--up-links",
        default=",".join(_DEFAULT_UP_LINKS),
        help=(
            "Comma-separated sphinx-needs link fields to emit as up-trace refs "
            "(default: 'satisfies')."
        ),
    )
    parser.add_argument(
        "--types",
        default=None,
        help=(
            "Comma-separated need types to include (default: all types). "
            "Example: 'tool_req' or 'gd_req'."
        ),
    )
    parser.add_argument(
        "--version",
        default=None,
        help="needs.json version key to convert (default: current_version).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    needs_json = _resolve(args.needs_json)
    output = _resolve(args.output) if args.output is not None else None

    needs_data = json.loads(needs_json.read_text(encoding="utf-8"))
    include_types = set(_parse_csv(args.types)) or None
    report = convert(
        needs_data,
        namespace=args.namespace,
        up_links=_parse_csv(args.up_links) or _DEFAULT_UP_LINKS,
        include_types=include_types,
        version=args.version,
    )

    payload = json.dumps(report, indent=2, sort_keys=True)
    if output is None:
        print(payload)
    else:
        output.write_text(payload + "\n", encoding="utf-8")
        print(
            f"Wrote {len(report['data'])} requirement item(s) to {output}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
