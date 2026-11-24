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
from typing import Any, cast

from src.helper_lib.repo_info import load_known_good, resolve_repo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


_LINK_KEYS = {"file", "line", "tag", "need", "full_line", "repo_name"}


def _reference_key(reference: dict[str, object]) -> str:
    """Return a stable, hashable representation of one source-link reference."""
    # References are dictionaries and therefore cannot be added to ``seen`` directly.
    # Sorting their JSON keys makes semantically identical dictionaries produce the
    # same key even when their input key order differs.
    return json.dumps(reference, sort_keys=True)


def _merge_sourcelinks_file(
    json_file: Path,
    known_good: dict[str, Any] | None,
    local_module: str,
    merged: list[dict[str, object]],
    seen: set[str],
) -> None:
    """Add the unique references from one sourcelinks JSON file to ``merged``."""
    with open(json_file, encoding="utf-8") as file:
        data = cast(list[object], json.load(file))
    # Also rejects the repository header that older caches start with.
    if not all(
        isinstance(reference, dict)
        and reference.keys() >= _LINK_KEYS
        and isinstance(reference["repo_name"], str)
        for reference in data
    ):
        logger.warning(
            f"Unexpected schema in sourcelinks file '{json_file}': "
            "expected a list of source links with a string 'repo_name'. "
        )
        return

    for reference in cast(list[dict[str, object]], data):
        # A known-good file is optional for standalone builds that include
        # documentation from external modules.  In that case, keep the link as
        # it was generated.
        if repo := resolve_repo(
            cast(str, reference["repo_name"]), known_good, local_module=local_module
        ):
            reference.update(repo.to_flat_dict())
        key = _reference_key(reference)
        if key not in seen:
            seen.add(key)
            merged.append(reference)


def main(argv: list[str] | None = None) -> int:
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
        help="Path to a 'known good' JSON file (provided by Bazel).",
    )
    _ = parser.add_argument(
        "--local-module",
        required=True,
        help="Root Bazel module that uses the current Git checkout",
    )
    _ = parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input JSON files to merge",
    )

    args = parser.parse_args(argv)

    merged: list[dict[str, object]] = []
    seen: set[str] = set()
    known_good = load_known_good(args.known_good) if args.known_good else None
    for json_file in args.files:
        if "known_good.json" not in str(json_file):
            _merge_sourcelinks_file(
                json_file, known_good, args.local_module, merged, seen
            )

    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(merged, file, indent=2, ensure_ascii=False)

    logger.info(f"Merged {len(args.files)} files into {len(merged)} total references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
