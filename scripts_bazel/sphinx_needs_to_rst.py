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
Render the sphinx-needs elements of a needs.json file as a reStructuredText
document.

The input is a needs.json file (typically the output of ``filtered_needs_json``).
Unlike ``sphinx_needs_to_md`` -- which renders a human readable *description* of
the needs -- this tool emits real sphinx-needs directives (``.. comp_req::``,
``.. feat_req::`` ...) so that the resulting ``.rst`` file can be ``include``\\ d
into a Sphinx project and is picked up by sphinx-needs itself.

Each need becomes a directive whose name is the need ``type``. The need ``title``
is placed on the directive line, every other (non internal) attribute is rendered
as a directive option (``:id:``, ``:status:``, ...) and the ``content`` is
rendered as the directive body. Needs are grouped by their ``type`` and sorted by
``id`` so the output is stable and diff friendly.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Attributes that are not rendered as directive options because they are handled
# specially or are internal sphinx-needs bookkeeping.
#   * ``type``      -> becomes the directive name.
#   * ``title``     -> rendered on the directive line.
#   * ``content``   -> rendered as the directive body.
#   * ``type_name`` -> derived from ``type``, not a valid need option.
#   * ``version``   -> managed by sphinx-needs itself.
_SKIP_ATTRS: frozenset[str] = frozenset(
    {"type", "title", "content", "type_name", "version"}
)

# Preferred ordering for the directive options; any remaining attributes are
# appended afterwards in alphabetical order for a stable output.
_OPTION_ORDER: list[str] = [
    "id",
    "status",
    "safety",
    "security",
    "reqtype",
    "tags",
    "derived_from",
    "satisfies",
    "covers",
]

# Indentation used for directive options and body (aligned under the directive).
_INDENT = "   "


def _format_value(value: object) -> str:
    """Render an attribute value as a single line option string."""
    if isinstance(value, list):
        return ", ".join(
            str(v)  # pyright: ignore[reportUnknownArgumentType]
            for v in value  # pyright: ignore[reportUnknownVariableType]
        )
    return str(value)


def _collect_needs(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all needs across every version, sorted by id."""
    needs: list[dict[str, Any]] = []
    for version in data.get("versions", {}).values():
        needs.extend(version.get("needs", {}).values())
    return sorted(needs, key=lambda need: str(need.get("id", "")))


def _ordered_option_keys(need: dict[str, Any]) -> list[str]:
    """Return the attribute keys to render as options, in a stable order."""
    keys = [k for k in need if k not in _SKIP_ATTRS]
    preferred = [k for k in _OPTION_ORDER if k in keys]
    remaining = sorted(k for k in keys if k not in _OPTION_ORDER)
    return preferred + remaining


def _render_need(need: dict[str, Any]) -> str:
    """Render a single need as a sphinx-needs RST directive."""
    type_ = str(need.get("type", "need"))
    title = str(need.get("title", "")).strip()

    lines: list[str] = [f".. {type_}:: {title}".rstrip()]

    for key in _ordered_option_keys(need):
        value = need[key]
        if value in (None, "", []):
            continue
        lines.append(f"{_INDENT}:{key}: {_format_value(value)}")

    content = str(need.get("content", "")).strip()
    if content:
        lines.append("")
        lines.extend(f"{_INDENT}{line}".rstrip() for line in content.splitlines())

    return "\n".join(lines)


def render_document(data: dict[str, Any], title: str) -> str:
    """Render the whole needs document as reStructuredText."""
    needs = _collect_needs(data)

    blocks: list[str] = [f"{title}\n{'=' * len(title)}"]

    current_type = None
    for need in sorted(
        needs, key=lambda n: (str(n.get("type", "")), str(n.get("id", "")))
    ):
        type_ = str(need.get("type", "<no type>"))
        if type_ != current_type:
            current_type = type_
            blocks.append(f"{type_}\n{'-' * len(type_)}")
        blocks.append(_render_need(need))

    return "\n\n".join(blocks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render the sphinx-needs elements of a needs.json file as "
            "reStructuredText sphinx-needs directives."
        )
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the reStructuredText file to write.",
    )
    _ = parser.add_argument(
        "--title",
        default="Sphinx-needs elements",
        help="Title rendered at the top of the document.",
    )
    _ = parser.add_argument(
        "input",
        type=Path,
        help="Input needs.json file to render.",
    )

    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    document = render_document(data, title=args.title)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        _ = f.write(document)

    need_count = sum(
        len(version.get("needs", {})) for version in data.get("versions", {}).values()
    )
    logger.info(
        "Rendered '%s' -> '%s' (%d needs)",
        args.input,
        args.output,
        need_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
