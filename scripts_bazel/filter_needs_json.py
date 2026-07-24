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
* ``--name``: the need belongs to one of the requested features/components. The
  owning feature/component is resolved by following a link and reading the
  linked element's ``title``:

  * ``feat_req`` / ``comp_req`` follow ``satisfied_by`` (falling back to the
    legacy ``belongs_to`` link) to their ``feat`` / ``comp`` element.
  * ``feat_arc_*`` / ``comp_arc_*`` follow ``belongs_to`` to their ``feat`` /
    ``comp`` element.

  The link target is looked up in the input needs.json (plus any
  ``--extra-needs-json`` inputs) and its ``title`` is matched against the
  requested names. For any other element type the name falls back to the second
  ``__``-separated segment of the need ID (``<type>__<name>__...``). If no
  ``--name`` is given, needs of any feature/component are kept.

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


# For each element type, the ordered link field(s) whose target ``feat`` /
# ``comp`` element carries the owning feature/component ``title`` used for
# --name matching. Requirements prefer the new ``satisfied_by`` link and fall
# back to the legacy ``belongs_to`` link; architecture views use ``belongs_to``.
_NAME_LINK_FIELDS: dict[str, tuple[str, ...]] = {
    "feat_req": ("satisfied_by", "belongs_to"),
    "comp_req": ("satisfied_by", "belongs_to"),
    "feat_arc_sta": ("belongs_to",),
    "feat_arc_dyn": ("belongs_to",),
    "comp_arc_sta": ("belongs_to",),
    "comp_arc_dyn": ("belongs_to",),
}


def _id_name_segment(need_id: str) -> str | None:
    """Return the feature/component name in the second ``__`` segment of a need ID.

    Fallback for element types without a configured owning link (see
    ``_NAME_LINK_FIELDS``). Need IDs follow ``<type>__<name>__<rest>`` (e.g.
    ``aou_req__baselibs__foo``), so the second ``__``-separated segment is the
    name. Returns ``None`` when the ID does not follow the convention.
    """
    parts = need_id.split("__")
    if len(parts) < 2 or not parts[1]:
        return None
    return parts[1]


def _need_names(
    need_id: str,
    need: dict[str, Any],
    universe: dict[str, dict[str, Any]],
) -> set[str]:
    """Return the feature/component names a need belongs to.

    For requirement and architecture element types the owning feature/component
    is resolved by following the configured link (``satisfied_by`` /
    ``belongs_to``, see ``_NAME_LINK_FIELDS``) and reading the linked element's
    ``title`` from ``universe``. For any other type the name falls back to the
    second ``__`` segment of the need ID.
    """
    fields = _NAME_LINK_FIELDS.get(str(need.get("type")))
    if fields is None:
        segment = _id_name_segment(need_id)
        return {segment} if segment is not None else set()
    names: set[str] = set()
    for field in fields:
        for target in _link_targets(need, field):
            target_need = universe.get(target)
            if target_need is None:
                continue
            title = target_need.get("title")
            if title:
                names.add(str(title).strip())
    return names


def _keep_need(
    need_id: str,
    need: dict[str, Any],
    types: set[str],
    names: set[str],
    universe: dict[str, dict[str, Any]],
) -> bool:
    if types and need.get("type") not in types:
        return False
    if names and names.isdisjoint(_need_names(need_id, need, universe)):
        return False
    return True


def filter_needs(
    data: dict[str, Any],
    types: set[str],
    names: set[str],
    universe: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return a copy of ``data`` keeping only the needs that match the filters."""
    for version in data.get("versions", {}).values():
        needs = version.get("needs", {})
        version["needs"] = {
            need_id: need
            for need_id, need in needs.items()
            if _keep_need(need_id, need, types, names, universe)
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
            "Feature/component name to keep, matched against the 'title' of the "
            "feat/comp element linked via 'satisfied_by' (requirements) or "
            "'belongs_to' (architecture). May be given multiple times. If "
            "omitted, all features/components are kept."
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

    # Universe used to resolve a need's owning feature/component title for --name
    # filtering (link targets may live in the input or an external needs.json).
    name_universe = {**source_needs, **extra_needs}

    filtered = filter_needs(
        data,
        types=set(args.types),
        names=set(args.names),
        universe=name_universe,
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
