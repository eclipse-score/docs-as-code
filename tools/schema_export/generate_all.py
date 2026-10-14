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
"""Generate metamodel data export for MCP server consumption.

This script exports the metamodel data from metamodel.yaml into a JSON format
that can be consumed by downstream tools like the MCP server metamodel-flow package.

Usage:
    generate_all.py --output-dir DIR [--source-commit SHA] [METAMODEL_YAML]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate metamodel data export for MCP server consumption"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("metamodel", type=Path, nargs="?", default=None)
    parser.add_argument(
        "--source-commit", default=os.environ.get("SOURCE_COMMIT", "unknown")
    )
    parser.add_argument(
        "--source-repo", default="https://github.com/eclipse-score/docs-as-code.git"
    )
    args = parser.parse_args()

    # Resolve metamodel path
    meta_path = args.metamodel
    if meta_path is None:
        # Path: tools/schema_export/generate_all.py -> src/extensions/score_metamodel/metamodel.yaml
        # From tools/schema_export, go up 2 levels to reach root
        meta_path = (
            Path(__file__).resolve().parent.parent.parent
            / "src/extensions/score_metamodel/metamodel.yaml"
        )

    if not meta_path.is_file():
        print(f"Error: metamodel.yaml not found at {meta_path}", file=sys.stderr)
        return 1

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Set environment for subprocesses
    env = os.environ.copy()
    env["SOURCE_COMMIT"] = args.source_commit

    # Generate data export
    data_path = args.output_dir / "metamodel-data.json"
    print(f"Exporting metamodel data: {data_path}")
    result = subprocess.run(
        [
            sys.executable,
            Path(__file__).parent / "export_data.py",
            "--output",
            str(data_path),
            "--source-repo",
            args.source_repo,
            str(meta_path),
        ],
        env=env,
    )
    if result.returncode != 0:
        return result.returncode

    print(f"\n✓ Generated file in {args.output_dir}:")
    print(f"  - {data_path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
