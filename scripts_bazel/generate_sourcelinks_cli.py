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
    store_source_code_links_json,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate source code links JSON from source files"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output JSON file path",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Source files to scan for traceability tags",
    )

    args = parser.parse_args()

    all_need_references = []
    for file_path in args.files:
        abs_file_path = file_path.resolve()
        assert abs_file_path.exists(), abs_file_path
        references = _extract_references_from_file(
            abs_file_path.parent, Path(abs_file_path.name)
        )
        all_need_references.extend(references)

    store_source_code_links_json(args.output, all_need_references)
    logger.info(
        f"Found {len(all_need_references)} need references in {len(args.files)} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
