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
CLI tool to generate source code links JSON from source files.
This is used by the Bazel sourcelinks_json rule to create a JSON file
with all source code links for documentation needs.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    _extract_references_from_file,  # pyright: ignore[reportPrivateUsage] TODO: move it out of the extension and into this script
)
from src.extensions.score_source_code_linker.helpers import parse_repo_name_from_path
from src.extensions.score_source_code_linker.needlinks import (
    DefaultMetaData,
    store_source_code_links_with_metadata_json,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def clean_external_prefix(path: Path) -> Path:
    """
    As it can be in combo builds that the path is:
    `external/score_docs_as_code+/....` or similar
    We have to remove this prefix from the file
    before we pass it to the extract function. Otherwise we have
    this prefix inside the `file` attribute leading to wrong links
    """
    if not str(path).startswith("external/"):
        return path
    # This allows for files / folders etc. to have `external` in their name too.
    path_raw = str(path).removeprefix("external/")
    filepath_split = str(path_raw).split("/", maxsplit=1)
    return Path("".join(filepath_split[1:]))


def _load_target_map(path: Path | None) -> dict[str, list[tuple[str, str]]]:
    """Return the direct ``code_targets`` owning each scanned source file."""
    if path is None:
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    target_map: dict[str, list[tuple[str, str]]] = {}
    for entry in entries:
        target_map.setdefault(entry["file"], []).append(
            (entry["bazel_target"], entry["bazel_type"])
        )
    return target_map


def main():
    parser = argparse.ArgumentParser(
        description="Generate source code links JSON from source files"
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output JSON file path",
    )
    _ = parser.add_argument(
        "--target-map",
        type=Path,
        help="JSON mapping source paths to their Bazel target labels and rule kinds",
    )
    _ = parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Source files to scan for traceability tags",
    )

    args = parser.parse_args()

    all_need_references = []
    target_map = _load_target_map(args.target_map)

    metadata = DefaultMetaData()
    metadata_set = False
    for file_path in args.files:
        if "known_good.json" not in str(file_path) and not metadata_set:
            metadata["repo_name"] = parse_repo_name_from_path(file_path)
            metadata_set = True
        abs_file_path = file_path.resolve()
        assert abs_file_path.exists(), abs_file_path
        clean_path = clean_external_prefix(file_path)
        references = _extract_references_from_file(
            abs_file_path.parent, Path(abs_file_path.name), clean_path
        )
        target_data = target_map.get(str(file_path), [])
        for reference in references:
            reference.bazel_target = ", ".join(target for target, _ in target_data)
            reference.bazel_type = ", ".join(kind for _, kind in target_data)
        all_need_references.extend(references)
    store_source_code_links_with_metadata_json(
        file=args.output, metadata=metadata, needlist=all_need_references
    )
    logger.info(
        f"Found {len(all_need_references)} need references in {len(args.files)} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
