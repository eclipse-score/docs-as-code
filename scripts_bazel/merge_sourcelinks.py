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



"""
if bazel-out/k8-fastbuild/bin/external/ in file_path => module is external
otherwise it's local
if local => module_name & hash == empty
if external => parse thing for module_name => look up known_good json for hash & url
"""



def add_needid_to_metaneed_mapping(mapping: dict[str, dict[str, str]], metadata: dict[str, str], needid: str):
    mapping
    pass

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
        help="Optional path to a 'known good' JSON file (provided by Bazel).",
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
    needs_metadata_mapping = {}
    for json_file in all_files:
        with open(json_file) as f:
            data = json.load(f)
            metadata = data[0]
            if metadata["module_name"] and metadata["module_name"] != "local_module":
                hash, repo = parse_info_from_known_good(
                    known_good_json=args.known_good, module_name=metadata["module_name"]
                )
                metadata["hash"] = hash
                metadata["url"] = repo
            # In the case that 'metadata[module_name]' is 'local_module'
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
