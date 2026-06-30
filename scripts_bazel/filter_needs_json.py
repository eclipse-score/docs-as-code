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
* ``--name``: the feature/component name encoded in the need's ID matches one
  of the requested names. Need IDs follow the convention
  ``<type>__<name>__<rest>`` (e.g. ``feat_req__baselibs__core_utilities``), so
  the second ``__``-separated segment is the feature/component name. The
  ``comp_arc_sta`` and ``comp_arc_dyn`` types are an exception: their IDs follow
  ``<type>__<feature name>__<component name>`` (e.g.
  ``comp_arc_sta__baselibs__filesystem``), so the *third* segment holds the
  component name used for matching. Any underscores within that component
  segment are removed before matching, so ``comp_arc_sta__baselibs__bit_manipulation``
  matches the component name ``bitmanipulation``. If no ``--name`` is given,
  needs of any feature/component are kept.

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


# Element types whose IDs follow ``<type>__<feature name>__<component name>``,
# i.e. the component name used for matching is the *third* ``__`` segment.
_COMPONENT_NAME_THIRD_SEGMENT_TYPES = frozenset({"comp_arc_sta", "comp_arc_dyn"})


def _id_name_segment(need_id: str, need_type: str | None = None) -> str | None:
    """Return the feature/component name encoded in a need ID.

    Need IDs follow the convention ``<type>__<name>__<rest>`` (e.g.
    ``feat_req__baselibs__core_utilities``); the second ``__``-separated segment
    is the feature/component name. The ``comp_arc_sta`` and ``comp_arc_dyn``
    types are an exception: their IDs follow
    ``<type>__<feature name>__<component name>`` (e.g.
    ``comp_arc_sta__baselibs__filesystem``), so the *third* segment holds the
    component name. Any underscores within that component segment are removed,
    so ``comp_arc_sta__baselibs__bit_manipulation`` yields ``bitmanipulation``.
    Returns ``None`` when the ID does not follow the convention.
    """
    parts = need_id.split("__")
    if need_type in _COMPONENT_NAME_THIRD_SEGMENT_TYPES:
        if len(parts) < 3 or not parts[2]:
            return None
        return parts[2].replace("_", "")
    if len(parts) < 2 or not parts[1]:
        return None
    return parts[1]


def _keep_need(
    need_id: str,
    need: dict[str, Any],
    types: set[str],
    names: set[str],
) -> bool:
    if types and need.get("type") not in types:
        return False
    if names:
        segment = _id_name_segment(need_id, need.get("type"))
        if segment is None or segment not in names:
            return False
    return True


def filter_needs(
    data: dict[str, Any],
    types: set[str],
    names: set[str],
) -> dict[str, Any]:
    """Return a copy of ``data`` keeping only the needs that match the filters."""
    for version in data.get("versions", {}).values():
        needs = version.get("needs", {})
        version["needs"] = {
            need_id: need
            for need_id, need in needs.items()
            if _keep_need(need_id, need, types, names)
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
        "--name",
        dest="names",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Feature/component name to keep, matched against the second "
            "'__'-separated segment of each need ID (the '<type>__<name>__...' "
            "naming convention). May be given multiple times. If omitted, all "
            "features/components are kept."
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
        names=set(args.names),
    )

    kept = sum(
        len(version.get("needs", {}))
        for version in filtered.get("versions", {}).values()
    )
    logger.info(
        "Filtered '%s' -> '%s' (%d needs kept, types=%s, names=%s)",
        args.input,
        args.output,
        kept,
        sorted(args.types) or "ALL",
        sorted(args.names) or "ALL",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(filtered, f, indent=2, sort_keys=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
