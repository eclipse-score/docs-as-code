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

from src.extensions.score_source_code_linker.helpers import parse_info_from_known_good

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


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
        required=True,
        help="Path to a required 'known good' JSON file (provided by Bazel).",
    )
    _ = parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input JSON files to merge",
    )

    args = parser.parse_args()
    all_files = [x for x in args.files if "known_good.json" not in str(x)]

    merged = []
    for json_file in all_files:
        with open(json_file) as f:
            data = json.load(f)
            # If the file is empty e.g. '[]' there is nothing to parse, we continue
            if not data:
                continue
            metadata = data[0]
            if not isinstance(metadata, dict) or "repo_name" not in metadata:
                logger.warning(
                    f"Unexpected schema in sourcelinks file '{json_file}': "
                    "expected first element to be a metadata dict "
                    "with a 'repo_name' key. "
                )
                # As we can't deal with bad JSON structure we just skip it
                continue
            if metadata["repo_name"] and metadata["repo_name"] != "local_repo":
                hash, repo = parse_info_from_known_good(
                    known_good_json=args.known_good, repo_name=metadata["repo_name"]
                )
                metadata["hash"] = hash
                metadata["url"] = repo
            # In the case that 'metadata[repo_name]' is 'local_module'
            # hash & url are already existing and empty inside of 'metadata'
            # Therefore all 3 keys will be written to needlinks in each branch

            for d in data[1:]:
                d.update(metadata)
            assert isinstance(data, list), repr(data)
            merged.extend(data[1:])
    with open(args.output, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info(f"Merged {len(args.files)} files into {len(merged)} total references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
