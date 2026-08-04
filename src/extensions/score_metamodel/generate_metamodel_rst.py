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


def _build_table(types: dict) -> list[str]:
    lines: list[str] = []
    lines.append(".. list-table:: Need Types")
    lines.append("   :header-rows: 1")
    lines.append("")
    lines.append("   * - Type")
    lines.append("     - Title")
    lines.append("     - Mandatory Options")
    lines.append("     - Links")
    for name, ty in sorted(types.items()):
        title = ty.get("title", name)
        mandatory = (
            ", ".join(sorted(ty.get("mandatory_options", {}).keys())) or "\u2014"
        )
        optional_links = ", ".join(sorted(ty.get("optional_links", {}).keys()))
        mandatory_links = ", ".join(sorted(ty.get("mandatory_links", {}).keys()))
        if mandatory_links:
            links = f"{optional_links} | mandatory: {mandatory_links}"
        else:
            links = optional_links or "\u2014"
        lines.append("   * - " + name)
        lines.append("     - " + title)
        lines.append("     - " + mandatory)
        lines.append("     - " + links)
    return lines


def _build_mermaid(types: dict) -> list[str]:
    lines: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for name, ty in sorted(types.items()):
        for link_name, targets in sorted(
            list(ty.get("mandatory_links", {}).items())
            + list(ty.get("optional_links", {}).items())
        ):
            target_types = targets.split(", ") if targets != "ANY" else []
            for target in target_types:
                target = target.strip()
                if target and target in types:
                    key = (name, target, link_name)
                    if key not in seen:
                        seen.add(key)
                        lines.append(f"{name} --> {target} : {link_name}")
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
    mermaid_lines = ["classDiagram"] + _build_mermaid(types)
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
            "Need Types",
            "----------",
            "",
        ]
        + table
        + [
            "",
            "Class Diagram",
            "-------------",
            "",
            f".. mermaid:: {args.mmd_output.name}",
            "",
        ]
        + [""]
    )

    args.rst_output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
