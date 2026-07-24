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


def collect_needs(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a flat ``{id: need}`` mapping of every need in a needs.json structure."""
    all_needs: dict[str, dict[str, Any]] = {}
    for version in data.get("versions", {}).values():
        for need_id, need in version.get("needs", {}).items():
            all_needs[need_id] = need
    return all_needs


def _resolve_needs_json(path: Path) -> Path:
    """Return ``path`` or ``path/needs.json`` when ``path`` is a directory."""
    return path / "needs.json" if path.is_dir() else path


def _normalize_id(need_id: str) -> str:
    """Strip a trailing ``[...]`` version constraint and whitespace from ``need_id``."""
    return need_id.split("[", 1)[0].strip()


def _link_targets(need: dict[str, Any], field: str) -> list[str]:
    """Return the normalized link targets stored under ``field`` of ``need``."""
    value = need.get(field)
    if value is None:
        return []
    raw = value if isinstance(value, list) else [value]
    return [_normalize_id(str(v)) for v in raw if str(v).strip()]  # pyright: ignore[reportUnknownArgumentType]


def detect_link_fields(needs: dict[str, dict[str, Any]]) -> set[str]:
    """Return the set of forward link field names used in ``needs``.

    sphinx-needs creates a companion ``<field>_back`` reverse-link field for
    every configured link field, so a field ``F`` is a forward link field iff
    ``F + "_back"`` occurs as a key on some need. This detects the link fields
    directly from the data, independent of the metamodel definition.
    """
    suffix = "_back"
    fields: set[str] = set()
    for need in needs.values():
        for key in need:
            if key.endswith(suffix):
                fields.add(key[: -len(suffix)])
    return fields


def find_dangling_links(
    kept: dict[str, dict[str, Any]],
    universe: set[str],
    link_fields: set[str],
) -> list[tuple[str, str, str]]:
    """Return ``(need_id, field, target)`` for every link target missing from ``universe``.

    A link target is dangling when the referenced need id is present neither in
    the source needs.json nor in any external needs.json input (together forming
    ``universe``).
    """
    dangling: list[tuple[str, str, str]] = []
    for need_id, need in sorted(kept.items()):
        for field in sorted(link_fields):
            for target in _link_targets(need, field):
                if target not in universe:
                    dangling.append((need_id, field, target))
    return dangling


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
        "--extra-needs-json",
        dest="extra_needs_json",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help=(
            "Additional needs.json file (or a directory containing one) that "
            "provides the full content of needs referenced from the kept "
            "elements but not contained in the input (e.g. requirements "
            "imported from an upstream repository). In --strict mode such "
            "external needs count as resolved link targets. May be given "
            "multiple times."
        ),
    )
    _ = parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Fail (exit 1, no output written) when any kept need has a dangling "
            "link, i.e. a link target present neither in the input needs.json "
            "nor in any --extra-needs-json input."
        ),
    )
    _ = parser.add_argument(
        "--link-field",
        dest="link_fields",
        action="append",
        default=[],
        metavar="FIELD",
        help=(
            "Link field to check for dangling references in --strict mode "
            "(e.g. 'derived_from'). May be given multiple times. If omitted, "
            "every link field is checked (auto-detected from the data via the "
            "sphinx-needs '<field>_back' convention)."
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

    # Full set of needs available locally (before filtering) plus any external
    # needs.json inputs, used to resolve link targets for the strict check.
    source_needs = collect_needs(data)
    extra_needs: dict[str, dict[str, Any]] = {}
    for extra in args.extra_needs_json:
        with open(_resolve_needs_json(extra)) as f:
            extra_needs.update(collect_needs(json.load(f)))

    filtered = filter_needs(
        data,
        types=set(args.types),
        names=set(args.names),
    )

    kept_needs = collect_needs(filtered)

    if args.strict:
        universe = set(source_needs) | set(extra_needs)
        if args.link_fields:
            link_fields = set(args.link_fields)
        else:
            link_fields = detect_link_fields({**extra_needs, **source_needs})
        dangling = find_dangling_links(kept_needs, universe, link_fields)
        if dangling:
            logger.error(
                "Refusing to export '%s': %d dangling link reference(s) found. "
                "Each target below is present neither in the source needs.json "
                "nor in any --extra-needs-json input:",
                args.output,
                len(dangling),
            )
            for need_id, field, target in dangling:
                logger.error("  %s --%s--> %s  (target not found)", need_id, field, target)
            logger.error(
                "Provide the missing needs via --extra-needs-json (e.g. an "
                "upstream repository's needs_json), or fix the broken links."
            )
            return 1

    logger.info(
        "Filtered '%s' -> '%s' (%d needs kept, types=%s, names=%s%s)",
        args.input,
        args.output,
        len(kept_needs),
        sorted(args.types) or "ALL",
        sorted(args.names) or "ALL",
        ", strict" if args.strict else "",
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(filtered, f, indent=2, sort_keys=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
