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
import subprocess
#from python.runfiles import Runfiles

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    _extract_references_from_file,  # pyright: ignore[reportPrivateUsage] TODO: move it out of the extension and into this script
)
from src.extensions.score_source_code_linker.needlinks import (
    store_source_code_links_json,
)
from src.helper_lib import find_git_root, find_ws_root, get_runfiles_dir

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def parse_filename(filepath: Path) -> tuple[Path, str, str, str]:
    """
    Parse out the Module-Name from the filename gotten
    /home/user/.cache/bazel/aksj37981712/external/score_docs_as_code+/src/tests/testfile.py
    => score_docs_as_code
    """
    # We only want '/score_docs_as_code+/....'
    runfiles_dir = get_runfiles_dir()
    # print("==============RUNFILES===========")
    # print(runfiles_dir)
    # print("=== RUNFILES SPLIT 1 ====")
    # print(str(runfiles_dir).split("external", maxsplit=1))
    # print("============PASSED IN FILEPATH============")
    # print(filepath)
    # print("============================")
    # All things needed for combo_builds:
    # prefix  (bazel cache dir etc.)
    # module_name 
    # file_name 
    # file_path 

    # COMBO BUILD
    # If external is in the filepath that gets parsed => file is in an external module => combo build
    if "external" in str(filepath):
        
        bazel_path = str(runfiles_dir.resolve()).split("/sandbox", maxsplit=1)
        prefix = Path(bazel_path[0]) / "external"
        filepath_split = str(filepath).removeprefix("external/").split("/", maxsplit=1)
        module_name = str(filepath_split[0].removesuffix("+"))
        path_file_split = filepath_split[1].rsplit("/", maxsplit=1)
        file_path = path_file_split[0]
        file_name = path_file_split[1]
    # LOCAL BUILD
    else:
        # We have a non combo build and the file is local to this repo => can use the git root to find the root 
        prefix = find_git_root()
        module_name = ""
        path_file_split = str(filepath)[1].rsplit("/", maxsplit=1)
        file_path = path_file_split[0]
        file_name = path_file_split[1]

    assert prefix is not None
    assert module_name is not None
    assert file_path is not None
    assert file_name is not None 

    return prefix, module_name, file_path, file_name


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

    # bazel_out_dir = subprocesrun(["bazel", "info", "output_base"], capture_output=True, check=True)
    # print("==== bazel_out_dir ====")
    # print(bazel_out_dir)

    # This way makes it easier to read the logic
    known_good_file_path = None
    all_files = args.files

    # For ref-integration or any integration that explicitly inputs 'known_good' jsons.
    #print("all_files: ", all_files)
    #print(all_files
    for raw_file_path in all_files:
        assert raw_file_path.exists(), raw_file_path
        prefix, module_name, file_path, file_name = parse_filename(raw_file_path)
        # ('external/score_docs_as_code+/src/extensions/score_sync_toml/shared.toml'
        references = _extract_references_from_file(
            prefix=prefix,
            file_name=file_name,
            file_path=Path(file_path),
            module_name=module_name,
        )
        print("==============")
        # print(module_name, file_path, file_name)
        print(references)
        print("==============")
        all_need_references.extend(references)

    store_source_code_links_json(args.output, all_need_references)
    logger.info(
        f"Found {len(all_need_references)} need references in {len(args.files)} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
