# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""Parse source files for traceability tags used by the Bazel link generator."""

import logging
from pathlib import Path

from src.extensions.score_source_code_linker.needlinks import NeedLink

LOGGER = logging.getLogger(__name__)

TAGS = [
    "# " + "req-traceability:",
    "# " + "req-Id:",
    "// " + "req-traceability:",
    "// " + "req-Id:",
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


def extract_references_from_file(
    root: Path, file_path_name: Path, file_path: Path
) -> list[NeedLink]:
    """Scan a single file for traceability tags and return the findings.

    ``root / file_path_name`` identifies the file to read. ``file_path`` is
    the path that should be recorded in the generated source-link data, which
    may differ when the input file is located below Bazel's external prefix.
    """

    assert root.is_absolute(), "Root path must be absolute"
    assert not file_path_name.is_absolute(), "File path must be relative to the root"
    assert (root / file_path_name).exists(), (
        f"File {file_path_name} does not exist in root {root}."
    )

    findings: list[NeedLink] = []

    try:
        with open(root / file_path_name, encoding="utf-8", errors="ignore") as f:
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
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        # Skip files that can't be read as text
        LOGGER.debug(f"Error reading file to parse for linked needs: \n{e}")

    return findings
