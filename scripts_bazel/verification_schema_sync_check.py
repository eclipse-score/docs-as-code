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

"""Gate to detect drift between process template section contracts and schema text.

Vertical slice scope (v1): validates the `verification_coverage` section only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    workspace_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY", "").strip()
    if not path.is_absolute() and workspace_dir:
        return Path(workspace_dir) / path
    return path


def _extract_section_description(template_text: str, section_key: str) -> str:
    # list-table rows are represented as:
    # * - <index>
    #       - <section_key>
    #       - <section_description>
    pattern = re.compile(
        r"\*\s*-\s*\d+\s*\n\s*-\s*"
        + re.escape(section_key)
        + r"\s*\n\s*-\s*(.+)",
        re.MULTILINE,
    )
    match = pattern.search(template_text)
    if not match:
        raise ValueError(
            f"Could not find section_key '{section_key}' in template section contract table"
        )
    return match.group(1).strip()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect drift between process template section contract fields and "
            "verification schema descriptions."
        )
    )
    parser.add_argument(
        "--process-template",
        required=True,
        help="Path to process_description module verification template rst file.",
    )
    parser.add_argument(
        "--report-schema",
        required=True,
        help="Path to verification_report_schema.json.",
    )
    parser.add_argument(
        "--section-key",
        default="verification_coverage",
        help="Section key to validate (default: verification_coverage).",
    )
    args = parser.parse_args()

    process_template = _resolve_path(args.process_template)
    report_schema = _resolve_path(args.report_schema)

    if not process_template.exists():
        print(f"Error: process template not found: {process_template}", file=sys.stderr)
        return 1
    if not report_schema.exists():
        print(f"Error: report schema not found: {report_schema}", file=sys.stderr)
        return 1

    template_text = process_template.read_text(encoding="utf-8")
    schema = _load_json(report_schema)

    try:
        expected_description = _extract_section_description(
            template_text, args.section_key
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    actual_description = (
        schema.get("properties", {})
        .get(args.section_key, {})
        .get("description", "")
        .strip()
    )

    if not actual_description:
        print(
            "Error: schema description missing for "
            f"properties.{args.section_key}.description",
            file=sys.stderr,
        )
        return 2

    if expected_description != actual_description:
        print("Schema sync check failed:")
        print(f"  section_key: {args.section_key}")
        print(f"  template:    {process_template}")
        print(f"  schema:      {report_schema}")
        print(f"  expected:    {expected_description}")
        print(f"  actual:      {actual_description}")
        return 2

    print("Schema sync check passed.")
    print(f"  section_key: {args.section_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
