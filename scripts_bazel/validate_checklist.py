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
Validate a requirement checklist against the build output it was reviewed against.

A ``req_chklst`` sphinx-needs element pins the state of one or more build
outputs (e.g. the extracted component requirements) via a ``sha256`` attribute.
This script:

1. Reads ``needs.json`` and looks up the checklist need by its id.
2. Computes the SHA256 over the concatenated input files (sorted by path, so the
   result is independent of the order in which Bazel passes them).
3. Compares the computed hash with the ``sha256`` attribute of the checklist need.

On match it writes the verified hash to ``--output`` and exits ``0``. On mismatch
(or when the need / attribute is missing) it logs the expected and actual hashes
and exits ``1``, which fails the Bazel build.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def find_need(data: dict[str, Any], need_id: str) -> dict[str, Any] | None:
    """Return the need with id ``need_id`` from a needs.json structure."""
    for version in data.get("versions", {}).values():
        needs = version.get("needs", {})
        if need_id in needs:
            return needs[need_id]
    return None


def compute_sha256(paths: list[Path]) -> str:
    """Return the SHA256 over the concatenated contents of ``paths`` (sorted)."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a requirement checklist (req_chklst) against the SHA256 of "
            "the build output it was reviewed against."
        )
    )
    _ = parser.add_argument(
        "--needs-json",
        required=True,
        type=Path,
        help="Path of the needs.json file containing the checklist need.",
    )
    _ = parser.add_argument(
        "--checklist-id",
        required=True,
        help="Id of the req_chklst need to validate (e.g. 'req_chklst__foo').",
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path of the stamp file to write with the verified hash on success.",
    )
    _ = parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Build output files whose combined SHA256 is validated.",
    )

    args = parser.parse_args()

    with open(args.needs_json) as f:
        data = json.load(f)

    need = find_need(data, args.checklist_id)
    if need is None:
        logger.error(
            "Checklist need '%s' not found in '%s'.",
            args.checklist_id,
            args.needs_json,
        )
        return 1

    expected = need.get("sha256")
    if not expected:
        logger.error(
            "Checklist need '%s' has no 'sha256' attribute.",
            args.checklist_id,
        )
        return 1

    actual = compute_sha256(args.inputs)

    if expected != actual:
        logger.error(
            "Checklist '%s' is OUT OF DATE.\n"
            "  expected (sha256 in need): %s\n"
            "  actual   (build output):  %s\n"
            "The validated target output has changed since the checklist was "
            "last reviewed. Re-review the checklist and update its 'sha256' "
            "attribute to '%s'.",
            args.checklist_id,
            expected,
            actual,
            actual,
        )
        return 1

    logger.info("Checklist '%s' is up to date (sha256=%s).", args.checklist_id, actual)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    _ = args.output.write_text(actual + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
