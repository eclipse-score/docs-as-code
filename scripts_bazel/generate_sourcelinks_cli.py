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
import logging
import sys
from pathlib import Path

from scripts_bazel.source_code_link_parser import extract_references_from_file
from src.helper_lib.needlinks import store_source_code_links_with_metadata_json
from src.helper_lib.repo_info import LOCAL_REPO, RepoInfo, split_external_path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


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
        "files",
        nargs="*",
        type=Path,
        help="Source files to scan for traceability tags",
    )

    args = parser.parse_args()

    all_need_references = []

    metadata_repo_name = LOCAL_REPO
    metadata_set = False
    for file_path in args.files:
        # Combo build: `external/<repo>+/<path>` => (<repo>, <path>)
        repo_name, clean_path = split_external_path(file_path)
        if "known_good.json" not in str(file_path) and not metadata_set:
            metadata_repo_name = repo_name
            metadata_set = True
        abs_file_path = file_path.resolve()
        assert abs_file_path.exists(), abs_file_path
        references = extract_references_from_file(
            abs_file_path.parent, Path(abs_file_path.name), clean_path
        )
        all_need_references.extend(references)
    store_source_code_links_with_metadata_json(
        file=args.output,
        metadata=RepoInfo(name=metadata_repo_name, hash="", url=""),
        needlist=all_need_references,
    )
    logger.info(
        f"Found {len(all_need_references)} need references in {len(args.files)} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
