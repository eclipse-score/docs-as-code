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

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    _extract_references_from_file,  # pyright: ignore[reportPrivateUsage] TODO: move it out of the extension and into this script
)
from src.extensions.score_source_code_linker.needlinks import (
    MetaData,
    store_source_code_links_with_metadata_json,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def parse_module_name_from_path(path: Path) -> str:
    """
    Parse out the Module-Name from the filename gotten
    /home/user/.cache/bazel/aksj37981712/external/score_docs_as_code+/src/tests/testfile.py
    => score_docs_as_code
    """

    # COMBO BUILD
    # If external is in the filepath that gets parsed =>
    # file is in an external module => combo build
    # Example Path:
    #   PosixPath('external/score_docs_as_code+/src/helper_lib/test_helper_lib.py'

    if str(path).startswith("external/"):
        # This allows for files / folders etc. to have `external` in their name too.
        module_raw = str(path).removeprefix("external/")
        filepath_split = str(module_raw).split("/", maxsplit=1)
        return str(filepath_split[0].removesuffix("+"))
    return "local_module"


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
    metadata: MetaData = {
        "module_name": "",
        "hash": "",
        "url": "",
    }
    metadata_set = False
    for file_path in args.files:
        if "known_good.json" not in str(file_path) and not metadata_set:
            metadata["module_name"] = parse_module_name_from_path(file_path)
            metadata_set = True
        abs_file_path = file_path.resolve()
        assert abs_file_path.exists(), abs_file_path
        references = _extract_references_from_file(
            abs_file_path.parent, Path(abs_file_path.name), file_path
        )
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
