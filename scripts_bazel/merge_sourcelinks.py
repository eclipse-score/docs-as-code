# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
Merge multiple sourcelinks JSON files into a single JSON file.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import cast

from src.extensions.score_source_code_linker.helpers import parse_info_from_known_good

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _reference_key(reference: dict[str, object]) -> str:
    """Return a stable, hashable representation of one source-link reference."""
    # References are dictionaries and therefore cannot be added to ``seen`` directly.
    # Sorting their JSON keys makes semantically identical dictionaries produce the
    # same key even when their input key order differs.
    return json.dumps(reference, sort_keys=True)


def _merge_sourcelinks_file(
    json_file: Path,
    known_good: Path | None,
    merged: list[dict[str, object]],
    seen: set[str],
) -> None:
    """Add the unique references from one sourcelinks JSON file to ``merged``."""
    with open(json_file, encoding="utf-8") as file:
        data = cast(list[object], json.load(file))
    if not data:
        return

    raw_metadata = data[0]
    if not isinstance(raw_metadata, dict) or "repo_name" not in raw_metadata:
        logger.warning(
            f"Unexpected schema in sourcelinks file '{json_file}': "
            "expected first element to be a metadata dict "
            "with a 'repo_name' key. "
        )
        return
    metadata = cast(dict[str, object], raw_metadata)
    repo_name = metadata["repo_name"]
    if not isinstance(repo_name, str):
        logger.warning(
            f"Unexpected schema in sourcelinks file '{json_file}': "
            "expected metadata 'repo_name' to be a string. "
        )
        return

    # A known-good file is optional for standalone builds that include
    # documentation from external modules.  In that case, keep the metadata
    # produced by the individual sourcelinks file.
    if known_good and repo_name and repo_name != "local_repo":
        hash, repo = parse_info_from_known_good(
            known_good_json=known_good, repo_name=repo_name
        )
        metadata["hash"] = hash
        metadata["url"] = repo

    for raw_reference in data[1:]:
        reference = cast(dict[str, object], raw_reference)
        reference.update(metadata)
        key = _reference_key(reference)
        if key not in seen:
            seen.add(key)
            merged.append(reference)


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple sourcelinks JSON files into one"
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output merged JSON file path",
    )
    _ = parser.add_argument(
        "--known_good",
        type=Path,
        help="Path to a required 'known good' JSON file (provided by Bazel).",
    )
    _ = parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input JSON files to merge",
    )

    args = parser.parse_args()

    merged: list[dict[str, object]] = []
    seen: set[str] = set()
    for json_file in args.files:
        if "known_good.json" not in str(json_file):
            _merge_sourcelinks_file(json_file, args.known_good, merged, seen)

    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(merged, file, indent=2, ensure_ascii=False)

    logger.info(f"Merged {len(args.files)} files into {len(merged)} total references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
