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
from typing import Any

# from src.extensions.score_source_code_linker.need_source_links import (
#     store_source_code_links_combined_json,
# )

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# [
# PosixPath('bazel-out/k8-fastbuild/bin/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_persistency+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_orchestrator+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_kyron+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_baselibs+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_baselibs_rust+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_logging+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_platform+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_process+/sourcelinks_json.json'),
# PosixPath('bazel-out/k8-fastbuild/bin/external/score_docs_as_code+/sourcelinks_json.json')
# ]


"""
if bazel-out/k8-fastbuild/bin/external/ in file_path => module is external 
otherwise it's local 
if local => module_name & hash == empty
if external => parse thing for module_name => look up known_good json for hash & url
"""


def parse_info_from_known_good(
    known_good_json: Path, module_name: str
) -> tuple[str, str]:
    print("===THIS IS MODULE NAME WE LOOK FOR===========")
    print(module_name)
    with open(known_good_json, "r") as f:
        kg_json = json.load(f)
    for category in kg_json["modules"].values():
        print("===THIS IS CATEGORY=========")
        print(category)
        if module_name in category:
            print("===THIS IS MODULE NAME INSIDe CATEGORY===========")
            print(module_name)
            m = category[module_name]
            return (m["hash"], m["repo"].removesuffix(".git"))
    raise KeyError(f"Module {module_name!r} not found in known_good_json.")


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
        default=None,
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
            # In the case that 'metadata[module_name]' is empty
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
