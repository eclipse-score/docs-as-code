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

"""
Extract a subset of sphinx-needs elements from a needs.json file.

A need is kept when it matches *all* of the active filters:

* ``--type``: the value of the need's ``type`` attribute is in the requested
  list of element types (e.g. ``feat_req``). If no ``--type`` is given, needs
  of any type are kept.
* ``--component``: the value of the need's component attribute (configurable
  via ``--component-attr``, default ``component``) matches one of the requested
  component names. The attribute may hold a single string or a list of strings;
  a need is kept when any of its values matches. If no ``--component`` is given,
  needs of any component are kept.

The top-level structure of the needs.json file is preserved; only the per-need
entries are filtered.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _attribute_values(need: dict[str, Any], attr: str) -> list[str]:
    """Return the values of ``attr`` on a need as a list of strings."""
    value = need.get(attr)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]  # pyright: ignore[reportUnknownVariableType]
    return [str(value)]


def _keep_need(
    need: dict[str, Any],
    types: set[str],
    components: set[str],
    component_attr: str,
) -> bool:
    if types and need.get("type") not in types:
        return False
    if components:
        values = set(_attribute_values(need, component_attr))
        if values.isdisjoint(components):
            return False
    return True


def filter_needs(
    data: dict[str, Any],
    types: set[str],
    components: set[str],
    component_attr: str,
) -> dict[str, Any]:
    """Return a copy of ``data`` keeping only the needs that match the filters."""
    for version in data.get("versions", {}).values():
        needs = version.get("needs", {})
        version["needs"] = {
            need_id: need
            for need_id, need in needs.items()
            if _keep_need(need, types, components, component_attr)
        }
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a subset of sphinx-needs elements from a needs.json file."
        )
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the filtered needs.json file to write.",
    )
    _ = parser.add_argument(
        "--type",
        dest="types",
        action="append",
        default=[],
        metavar="ELEMENT_TYPE",
        help=(
            "Sphinx-needs element type to keep (e.g. 'feat_req'). "
            "May be given multiple times. If omitted, all types are kept."
        ),
    )
    _ = parser.add_argument(
        "--component",
        dest="components",
        action="append",
        default=[],
        metavar="COMPONENT",
        help=(
            "Component name to keep. May be given multiple times. "
            "If omitted, all components are kept."
        ),
    )
    _ = parser.add_argument(
        "--component-attr",
        default="component",
        help=(
            "Need attribute matched against the values given via --component. "
            "Defaults to 'component'."
        ),
    )
    _ = parser.add_argument(
        "input",
        type=Path,
        help="Input needs.json file to filter.",
    )

    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    filtered = filter_needs(
        data,
        types=set(args.types),
        components=set(args.components),
        component_attr=args.component_attr,
    )

    kept = sum(
        len(version.get("needs", {}))
        for version in filtered.get("versions", {}).values()
    )
    logger.info(
        "Filtered '%s' -> '%s' (%d needs kept, types=%s, components=%s)",
        args.input,
        args.output,
        kept,
        sorted(args.types) or "ALL",
        sorted(args.components) or "ALL",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(filtered, f, indent=2, sort_keys=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
