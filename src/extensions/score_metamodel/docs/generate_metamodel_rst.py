#!/usr/bin/env python3
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
"""Generate an RST file with a list-table and Mermaid class diagram from metamodel.yaml.

Usage:
    generate_metamodel_rst.py --rst-output FILE --mmd-output FILE [METAMODEL_YAML]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import ruamel.yaml


def _parse_yaml(path: Path) -> dict:
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.load(fh)  # type: ignore[no-any-return]


def _split_targets(targets: str) -> list[str]:
    """Split a comma-separated target spec, ignoring the ``ANY`` wildcard."""
    if targets == "ANY":
        return []
    return [t.strip() for t in targets.split(",") if t.strip()]


def _incoming_mandatory_links(types: dict) -> dict[str, list[str]]:
    """Map each type to the source types that point at it via mandatory links."""
    incoming: dict[str, list[str]] = {name: [] for name in types}
    for source, ty in types.items():
        for targets in ty.get("mandatory_links", {}).values():
            for target in _split_targets(targets):
                if target in incoming and source not in incoming[target]:
                    incoming[target].append(source)
    return {name: sorted(sources) for name, sources in incoming.items()}


def _build_table(types: dict) -> list[str]:
    incoming = _incoming_mandatory_links(types)
    lines: list[str] = []
    lines.append(".. list-table:: Need Types")
    lines.append("   :header-rows: 1")
    lines.append("")
    lines.append("   * - Type")
    lines.append("     - Title")
    lines.append("     - Mandatory Options")
    lines.append("     - Links")
    lines.append("     - Incoming Mandatory Links")
    for name, ty in sorted(types.items()):
        title = ty.get("title", name)
        mandatory = (
            ", ".join(sorted(ty.get("mandatory_options", {}).keys())) or "\u2014"
        )
        optional_links = ty.get("optional_links", {})
        mandatory_links = ty.get("mandatory_links", {})
        link_strs = [
            f"**{n}**" if n in mandatory_links else n
            for n in sorted(set(optional_links) | set(mandatory_links))
        ]
        links = ", ".join(link_strs) or "\u2014"
        inc = ", ".join(incoming.get(name, [])) or "\u2014"
        lines.append("   * - " + name)
        lines.append("     - " + title)
        lines.append("     - " + mandatory)
        lines.append("     - " + links)
        lines.append("     - " + inc)
    return lines


def _build_mermaid(types: dict) -> list[str]:
    lines: list[str] = []
    # Declare every type so isolated nodes render and can be styled.
    # List the mandatory options as class members (optional ones are omitted).
    for name in sorted(types):
        mandatory_opts = sorted(types[name].get("mandatory_options", {}).keys())
        if mandatory_opts:
            lines.append(f"class {name} {{")
            for opt in mandatory_opts:
                lines.append(f"  +{opt}")
            lines.append("}")
        else:
            lines.append(f"class {name}")
    # Edges for all (mandatory + optional) links.
    seen: set[tuple[str, str, str]] = set()
    for name, ty in sorted(types.items()):
        links = list(ty.get("mandatory_links", {}).items()) + list(
            ty.get("optional_links", {}).items()
        )
        for link_name, targets in sorted(links):
            for target in _split_targets(targets):
                if target not in types:
                    continue
                key = (name, target, link_name)
                if key not in seen:
                    seen.add(key)
                    lines.append(f"{name} --> {target} : {link_name}")
    # Color nodes per the ``color`` option in metamodel.yaml.
    for name, ty in sorted(types.items()):
        color = ty.get("color")
        if color:
            lines.append(f"style {name} fill:{color},stroke:#666,color:#000")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RST from metamodel.yaml")
    parser.add_argument("--rst-output", type=Path, required=True)
    parser.add_argument("--mmd-output", type=Path, required=True)
    parser.add_argument("metamodel", nargs="?", default=None)
    args = parser.parse_args()

    meta_path = (
        Path(args.metamodel)
        if args.metamodel
        else Path(__file__).parent / "metamodel.yaml"
    )
    if not meta_path.is_file():
        print(f"Error: metamodel.yaml not found at {meta_path}", file=sys.stderr)
        return 1

    try:
        data = _parse_yaml(meta_path)
    except Exception as exc:
        print(f"Error parsing YAML: {exc}", file=sys.stderr)
        return 1

    types = data.get("needs_types", {})
    if not types:
        print(
            "Error: 'needs_types' section not found in metamodel.yaml", file=sys.stderr
        )
        return 1

    table = _build_table(types)
    mermaid_lines = [
        "---",
        "config:",
        "  layout: elk",
        "---",
        "classDiagram",
    ] + _build_mermaid(types)
    args.mmd_output.write_text("\n".join(mermaid_lines) + "\n", encoding="utf-8")
    output = "\n".join(
        [
            "..",
            "   # (generated \u2014 do not edit)",
            "   # SPDX-License-Identifier: Apache-2.0",
            "",
            ".. _metamodel-types-visualization:",
            "",
            "Metamodel Types Visualization",
            "==============================",
            "",
            f".. mermaid:: {args.mmd_output.name}",
            "",
            "Need Types",
            "----------",
            "",
        ]
        + table
        + [""]
    )

    args.rst_output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
