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
Render the sphinx-needs elements of a needs.json file as a Markdown document.

The input is a needs.json file (typically the output of ``filtered_needs_json``).
Each need is rendered as a Markdown section. Needs are grouped by their ``type``
and sorted by ``id`` so the output is stable and diff friendly.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Attributes rendered (in this order) as a table for every need.
# Only attributes that are present and non-empty on a need are shown.
_HEADER_ATTRS: list[tuple[str, str]] = [
    ("title", "Title"),
    ("type_name", "Type name"),
    ("status", "Status"),
    ("safety", "Safety"),
    ("security", "Security"),
    ("reqtype", "Requirement type"),
    ("tags", "Tags"),
    ("docname", "Document"),
]


def _format_value(value: object) -> str:
    """Render an attribute value as a single line Markdown-safe string."""
    text = (
        ", ".join(str(v) for v in value)  # pyright: ignore[reportUnknownVariableType]
        if isinstance(value, list)
        else str(value)
    )
    # Escape the Markdown table cell separator.
    return text.replace("|", "\\|")


def _collect_needs(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all needs across every version, sorted by id."""
    needs: list[dict[str, Any]] = []
    for version in data.get("versions", {}).values():
        needs.extend(version.get("needs", {}).values())
    return sorted(needs, key=lambda need: str(need.get("id", "")))


def _render_need(need: dict[str, Any]) -> str:
    """Render a single need as a Markdown block."""
    lines: list[str] = []
    need_id = str(need.get("id", "<unknown id>"))
    lines.append(f"### `{need_id}`")
    lines.append("")

    rows = [
        (label, _format_value(value))
        for attr, label in _HEADER_ATTRS
        if (value := need.get(attr)) not in (None, "", [])
    ]
    if rows:
        lines.append("| Attribute | Value |")
        lines.append("| --- | --- |")
        for label, value in rows:
            lines.append(f"| {label} | {value} |")
        lines.append("")

    content = str(need.get("content", "")).strip()
    if content:
        lines.append("**Content:**")
        lines.append("")
        lines.append("```")
        lines.extend(content.splitlines())
        lines.append("```")
    return "\n".join(lines).rstrip()


def render_document(data: dict[str, Any], title: str) -> str:
    """Render the whole needs document as Markdown."""
    needs = _collect_needs(data)
    types: dict[str, int] = {}
    for need in needs:
        type_ = str(need.get("type", "<no type>"))
        types[type_] = types.get(type_, 0) + 1

    blocks: list[str] = []
    blocks.append(f"# {title}")
    blocks.append(f"Total needs: **{len(needs)}**")

    if types:
        summary_lines = ["| Type | Count |", "| --- | --- |"]
        summary_lines.extend(
            f"| `{type_}` | {count} |" for type_, count in sorted(types.items())
        )
        blocks.append("\n".join(summary_lines))

    current_type = None
    for need in sorted(
        needs, key=lambda n: (str(n.get("type", "")), str(n.get("id", "")))
    ):
        type_ = str(need.get("type", "<no type>"))
        if type_ != current_type:
            current_type = type_
            blocks.append(f"## `{type_}`")
        blocks.append(_render_need(need))

    return "\n\n".join(blocks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render the sphinx-needs elements of a needs.json file as Markdown."
        )
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the Markdown file to write.",
    )
    _ = parser.add_argument(
        "--title",
        default="Sphinx-needs elements",
        help="Title rendered at the top of the document.",
    )
    _ = parser.add_argument(
        "input",
        type=Path,
        help="Input needs.json file to document.",
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
        "Documented '%s' -> '%s' (%d needs)",
        args.input,
        args.output,
        need_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
