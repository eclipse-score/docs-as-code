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

import os
import sys
from pathlib import Path
from pprint import pprint

from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    store_source_code_links_json,
)


def find_ws_root() -> Path | None:
    """Find the current MODULE.bazel file"""
    ws_dir = os.environ.get("BUILD_WORKSPACE_DIRECTORY", None)
    return Path(ws_dir) if ws_dir else None


def find_git_root(start_path: str | Path = "") -> Path | None:
    """Find the git root directory starting from the given path or __file__."""
    if start_path == "":
        start_path = __file__

    git_root = Path(start_path).resolve()
    esbonio_search = False
    while not (git_root / ".git").exists():
        git_root = git_root.parent
        if git_root == Path("/"):
            # fallback to cwd when building with python -m sphinx docs _build -T
            if esbonio_search:
                return None
            git_root = Path.cwd().resolve()
            esbonio_search = True
    return git_root


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


def _extract_references_from_file(root: Path, file_path: Path) -> list[NeedLink]:
    """Scan a single file for template strings and return findings."""
    assert root.is_absolute(), "Root path must be absolute"
    assert not file_path.is_absolute(), "File path must be relative to the root"
    # assert file_path.is_relative_to(root), f"File path ({file_path}) must be relative to the root ({root})"
    assert (root / file_path).exists(), (
        f"File {file_path} does not exist in root {root}."
    )

    findings: list[NeedLink] = []

    try:
        with open(root / file_path, encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for tag, req in _extract_references_from_line(line):
                    findings.append(
                        NeedLink(
                            file=file_path,
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


def iterate_files_recursively(search_path: Path):
    def _should_skip_file(file_path: Path) -> bool:
        """Check if a file should be skipped during scanning."""
        # TODO: consider using .gitignore
        return (
            file_path.is_dir()
            or file_path.name.startswith((".", "_"))
            or file_path.suffix in [".pyc", ".so", ".exe", ".bin"]
        )

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
    start_time = os.times().elapsed

    all_need_references: list[NeedLink] = []

    # Use os.walk to have better control over directory traversal
    for file in iterate_files_recursively(search_path):
        references = _extract_references_from_file(search_path, file)
        all_need_references.extend(references)

    elapsed_time = os.times().elapsed - start_time
    print(
        f"DEBUG: Found {len(all_need_references)} need references "
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


# incremental_latest:
# DEBUG: Workspace root is /home/lla2hi/score/docs-as-code
# DEBUG: Current working directory is /home/lla2hi/.cache/bazel/_bazel_lla2hi/e35bb7c4cc72b99eb76653ab839f4f8e/execroot/_main/bazel-out/k8-fastbuild/bin/docs/incremental_latest.runfiles/_main
# DEBUG: Git root is /home/lla2hi/score/docs-as-code

# incremental_release: (-> bazel build sandbox of process repository)
# DEBUG: Workspace root is None
# DEBUG: Current working directory is /home/lla2hi/.cache/bazel/_bazel_lla2hi/e35bb7c4cc72b99eb76653ab839f4f8e/sandbox/linux-sandbox/25/execroot/_main (-> process repo!!)
#    rst files are in .../bazel-out/k8-fastbuild/bin/external/score_process~/process/_docs_needs_latest/score_process~/*
# DEBUG: Git root is /home/lla2hi/score/docs-as-code

# docs_latest:
# DEBUG: Workspace root is None
# DEBUG: Current working directory is /home/lla2hi/.cache/bazel/_bazel_lla2hi/e35bb7c4cc72b99eb76653ab839f4f8e/sandbox/linux-sandbox/26/execroot/_main
# DEBUG: Git root is /home/lla2hi/score/docs-as-code

# TODO docu:
# docs:docs has no source code links
# external repositories have no source code links (to their code)
