# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

import json
import os
import sys
from pathlib import Path

from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    store_source_code_links_json,
)


def find_ws_root() -> Path:
    """Find the current MODULE.bazel file"""
    bwd = Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    assert bwd.exists(), f"BUILD_WORKSPACE_DIRECTORY {bwd} does not exist"
    assert bwd.is_dir(), f"BUILD_WORKSPACE_DIRECTORY {bwd} is not a directory"
    return bwd


def find_git_root() -> Path:
    git_root = Path(__file__).resolve()
    while not (git_root / ".git").exists():
        git_root = git_root.parent
        if git_root == Path("/"):
            sys.exit(
                "Could not find git root. Please run this script from the "
                "root of the repository."
            )
    return git_root


TAGS = [
    "# " + "req-traceability:",
    "# " + "req-Id:",
]


def _should_skip_file(file_path: Path) -> bool:
    """Check if a file should be skipped during scanning."""
    # TODO: consider using .gitignore
    return (
        file_path.is_dir()
        or file_path.name.startswith((".", "_"))
        or file_path.suffix in [".pyc", ".so", ".exe", ".bin"]
    )


def _extract_requirements_from_line(line: str, tag: str) -> list[str]:
    """Extract requirement IDs from a line containing a tag."""
    tag_index = line.find(tag)
    if tag_index == -1:
        return []

    after_tag = line[tag_index + len(tag) :].strip()
    # Split by comma or space to get multiple requirements
    return [req.strip() for req in after_tag.replace(",", " ").split() if req.strip()]


def _extract_requirements_from_file(git_root: Path, file_path: Path) -> list[NeedLink]:
    """Scan a single file for template strings and return findings."""
    findings: list[NeedLink] = []

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for tag in TAGS:
                    if tag in line:
                        requirements = _extract_requirements_from_line(line, tag)
                        for req in requirements:
                            findings.append(
                                NeedLink(
                                    file=file_path.relative_to(git_root),
                                    line=line_num,
                                    tag=tag,
                                    need=req,
                                    full_line=line.strip(),
                                )
                            )
    except (UnicodeDecodeError, PermissionError, OSError):
        # Skip files that can't be read as text
        pass

    return findings


def find_all_need_references(search_path: Path) -> list[NeedLink]:
    """
    Find all need references in all files in git root.
    Search for any appearance of TAGS and collect line numbers and referenced
    requirements.

    Returns:
        list[FileFindings]: List of FileFindings objects containing all findings
                           for each file that contains template strings.
    """
    start_time = os.times().elapsed

    all_need_references: list[NeedLink] = []

    # Use os.walk to have better control over directory traversal
    for root, dirs, files in os.walk(search_path):
        root_path = Path(root)

        # Skip directories that start with '.' or '_' by modifying dirs in-place
        # This prevents os.walk from descending into these directories
        dirs[:] = [d for d in dirs if not d.startswith((".", "_", "bazel-"))]

        for file in files:
            file_path = root_path / file

            if _should_skip_file(file_path):
                continue

            findings = _extract_requirements_from_file(search_path, file_path)
            all_need_references.extend(findings)

    elapsed_time = os.times().elapsed - start_time
    print(
        f"DEBUG: Found {len(all_need_references)} need references "
        f"in {elapsed_time:.2f} seconds"
    )

    return all_need_references


def generate_source_code_links_json(file: Path):
    """
    Generate a JSON file with all source code links for the needs.
    This is used to link the needs to the source code in the documentation.
    """
    needlinks = find_all_need_references(Path("."))

    store_source_code_links_json(file, needlinks)
