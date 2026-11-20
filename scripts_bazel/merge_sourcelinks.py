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

from src.helper_lib.repo_info import RepoInfo, load_known_good, resolve_repo

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
    known_good: dict[str, Any] | None,
    resolved_repos: dict[str, RepoInfo | None],
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
    shared_repo_name = metadata["repo_name"]
    if not isinstance(shared_repo_name, str):
        logger.warning(
            f"Unexpected schema in sourcelinks file '{json_file}': "
            "expected metadata 'repo_name' to be a string. "
        )
        return

    for raw_reference in data[1:]:
        reference = cast(dict[str, object], raw_reference)
        repo_name = reference.get("repo_name") or shared_repo_name
        if not isinstance(repo_name, str):
            logger.warning(
                f"Unexpected schema in sourcelinks file '{json_file}': "
                "expected reference 'repo_name' to be a string. "
                f"Skipping reference {reference.get('file')}:{reference.get('line')}."
            )
            continue
        reference["repo_name"] = repo_name

        if repo_name not in resolved_repos:
            try:
                resolved_repos[repo_name] = resolve_repo(repo_name, known_good)
            except KeyError as error:
                logger.warning("Cannot resolve source-link metadata: %s", error.args[0])
                # Remember the failed lookup so subsequent links warn only once.
                resolved_repos[repo_name] = None
        if repo := resolved_repos[repo_name]:
            reference.update(repo.to_flat_dict())
        else:
            # Shared metadata only applies to links from that repository.
            shared = metadata if repo_name == shared_repo_name else {}
            reference["hash"] = reference.get("hash") or shared.get("hash", "")
            reference["url"] = reference.get("url") or shared.get("url", "")

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
        help="Path to the optional 'known good' JSON file provided by Bazel.",
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
    known_good = load_known_good(args.known_good) if args.known_good else None
    resolved_repos: dict[str, RepoInfo | None] = {}
    for json_file in args.files:
        if "known_good.json" not in str(json_file):
            _merge_sourcelinks_file(json_file, known_good, resolved_repos, merged, seen)

    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(merged, file, indent=2, ensure_ascii=False)

    logger.info(f"Merged {len(args.files)} files into {len(merged)} total references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
