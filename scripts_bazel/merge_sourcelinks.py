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

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple sourcelinks JSON files into one"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output merged JSON file path",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input JSON files to merge",
    )

    args = parser.parse_args()

    merged = []
    for json_file in args.files:
        with open(json_file) as f:
            data = json.load(f)
            assert isinstance(data, list), repr(data)
            merged.extend(data)

    with open(args.output, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info(f"Merged {len(args.files)} files into {len(merged)} total references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
