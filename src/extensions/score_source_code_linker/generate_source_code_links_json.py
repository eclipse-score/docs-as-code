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
This file is used by incremental.py to generate a JSON file with all source code links
for the needs. It's split this way, so that the live_preview action does not need to
parse everything on every run.
"""

import os
from pathlib import Path

from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    store_source_code_links_json,
)

from src.helper_lib import get_runfiles_dir, parse_filename

from sphinx_needs.logging import get_logger
LOGGER = get_logger(__name__)

TAGS = [
    "# " + "req-traceability:",
    "# " + "req-Id:",
]


def _extract_references_from_line(line: str):
    """Extract requirement IDs from a line containing a tag."""

    for tag in TAGS:
        tag_index = line.find(tag)
        if tag_index >= 0:
            line_after_tag = line[tag_index + len(tag) :].strip()
            # Split by comma or space to get multiple requirements
            for req in line_after_tag.replace(",", " ").split():
                yield tag, req.strip()


def _extract_references_from_file(
    prefix: Path, file_name: str, file_path: Path, module_name: str
) -> list[NeedLink]:
    """Scan a single file for template strings and return findings."""
    # assert root.is_absolute(), f"Root path must be absolute. {root} is not"
    #assert not file_path.is_absolute(), "File path must be relative to the root"
    # assert file_path.is_relative_to(root), (
    #     f"File path ({file_path}) must be relative to the root ({root})"
    # )
    # assert (root / file_path).exists(), (
    #     f"File {file_path} does not exist in root {root}."
    # )
    findings: list[NeedLink] = []
    if module_name:
        module_name_full = str(module_name) + "+"
        complete_file = prefix / module_name_full / file_path / file_name
    else:
        complete_file = prefix / file_path / file_name
    assert complete_file is not None
    try:
        with open(complete_file, encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for tag, req in _extract_references_from_line(line):
                    findings.append(
                        NeedLink(
                            file=file_name,
                            path=file_path,
                            module=module_name if module_name is not None else "",
                            line=line_num,
                            tag=tag,
                            need=req,
                            full_line=line.strip(),
                        )
                    )
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        # Skip files that can't be read as text
        LOGGER.debug(f"Error reading file to parse for linked needs: \n{e}")
        pass

    return findings


def iterate_files_recursively(search_path: Path):
    def _should_skip_file(file_path: Path) -> bool:
        """Check if a file should be skipped during scanning."""
        # TODO: consider using .gitignore
        if file_path.is_dir():
            return True
        if file_path.suffix in [".pyc", ".so", ".exe", ".bin"]:
            return True  # skip binaries
        if file_path.suffix in [".rst", ".md"]:
            return True  # skip documentation
        return file_path.name.startswith((".", "_"))

    for root, dirs, files in os.walk(search_path):
        root_path = Path(root)

        # Skip directories that start with '.' or '_' by modifying dirs in-place
        # This prevents os.walk from descending into these directories
        dirs[:] = [d for d in dirs if not d.startswith((".", "_", "bazel-"))]

        for file in files:
            f = root_path / file
            if not _should_skip_file(f):
                yield f.relative_to(search_path)


def find_all_need_references(search_path: Path) -> list[NeedLink]:
    """
    Find all need references in all files in git root.
    Search for any appearance of TAGS and collect line numbers and referenced
    requirements.

    Returns:
        list[FileFindings]: List of FileFindings objects containing all findings
                           for each file that contains template strings.
    """
    runfiles_dir = get_runfiles_dir()
    start_time = os.times().elapsed

    all_need_references: list[NeedLink] = []

    # Use os.walk to have better control over directory traversal
    for file in iterate_files_recursively(search_path):
        prefix, module_name, file_path, file_name = parse_filename(file, runfiles_dir)
        references = _extract_references_from_file(
            prefix, file_name, Path(file_path), module_name
        )
        all_need_references.extend(references)

    elapsed_time = os.times().elapsed - start_time
    LOGGER.debug(
        f"Found {len(all_need_references)} need references "
        f"in {elapsed_time:.2f} seconds"
    )

    return all_need_references


def generate_source_code_links_json(search_path: Path, file: Path):
    """
    Generate a JSON file with all source code links for the needs.
    This is used to link the needs to the source code in the documentation.
    """
    needlinks = find_all_need_references(search_path)
    store_source_code_links_json(file, needlinks)
