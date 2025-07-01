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

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import debugpy
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import main as sphinx_autobuild_main

logger = logging.getLogger(__name__)

logger.debug("DEBUG: CWD: ", os.getcwd())
logger.debug("DEBUG: SOURCE_DIRECTORY: ", os.getenv("SOURCE_DIRECTORY"))
logger.debug("DEBUG: RUNFILES_DIR: ", os.getenv("RUNFILES_DIR"))

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
    "# req-traceability:",
    "# req-Id:",
]


@dataclass
class NeedLink:
    """Represents a single template string finding in a file."""
    file: Path
    line_number: int
    tag: str
    requirements: list[str]
    full_line: str

def _should_skip_file(file_path: Path) -> bool:
    """Check if a file should be skipped during scanning."""
    # TODO: consider using .gitignore
    return (file_path.is_dir() or
            file_path.name.startswith(('.', '_')) or
            file_path.suffix in ['.pyc', '.so', '.exe', '.bin'])


def _extract_requirements_from_line(line: str, tag: str) -> list[str]:
    """Extract requirement IDs from a line containing a tag."""
    tag_index = line.find(tag)
    if tag_index == -1:
        return []

    after_tag = line[tag_index + len(tag):].strip()
    # Split by comma or space to get multiple requirements
    return [
        req.strip()
        for req in after_tag.replace(',', ' ').split()
        if req.strip()
    ]


def _extract_requirements_from_file(git_root: Path, file_path: Path) -> list[NeedLink]:
    """Scan a single file for template strings and return findings."""
    findings: list[NeedLink] = []

    try:
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for tag in TAGS:
                    if tag in line:
                        requirements = _extract_requirements_from_line(line, tag)
                        findings.append(NeedLink(
                            file=file_path.relative_to(git_root),
                            line_number=line_num,
                            tag=tag,
                            requirements=requirements,
                            full_line=line.strip()
                        ))
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
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_', 'bazel-'))]

        for file in files:
            file_path = root_path / file

            if _should_skip_file(file_path):
                continue

            findings = _extract_requirements_from_file(search_path, file_path)
            all_need_references.extend(findings)

    elapsed_time = os.times().elapsed - start_time
    print(f"DEBUG: Found {len(all_need_references)} need references in {elapsed_time:.2f} seconds")

    return all_need_references




def get_env(name: str) -> str:
    val = os.environ.get(name, None)
    logger.debug(f"DEBUG: Env: {name} = {val}")
    if val is None:
        raise ValueError(f"Environment variable {name} is not set")
    return val

if __name__ == "__main__":
    # Add debuging functionality
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-dp", "--debug_port", help="port to listen to debugging client", default=5678
    )
    parser.add_argument(
        "--debug", help="Enable Debugging via debugpy", action="store_true"
    )
    # optional GitHub user forwarded from the Bazel CLI
    parser.add_argument(
        "--github_user",
        help="GitHub username to embed in the Sphinx build",
    )
    parser.add_argument(
        "--github_repo",
        help="GitHub repository to embed in the Sphinx build",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to use for the live_preview ACTION. Default is 8000. "
        "Use 0 for auto detection of a free port.",
        default=8000,
    )

    args = parser.parse_args()
    if args.debug:
        debugpy.listen(("0.0.0.0", args.debug_port))
        logger.info("Waiting for client to connect on port: " + str(args.debug_port))
        debugpy.wait_for_client()

    workspace = os.getenv("BUILD_WORKSPACE_DIRECTORY")
    if workspace:
        os.chdir(workspace)

    need_references = find_all_need_references(Path("."))
    build_dir = Path(get_env("BUILD_DIRECTORY"))

    # Convert NeedLink objects to dictionaries using asdict
    need_references_dict = [asdict(ref) for ref in need_references]

    # Convert Path objects to strings for JSON serialization
    for ref_dict in need_references_dict:
        ref_dict["file"] = str(ref_dict["file"])

    with open(build_dir / "NEED_REFERENCES_FILE.json", "w") as f:
        json.dump(
            need_references_dict,
            f,
            indent=2,
            ensure_ascii=False,
        )

    base_arguments = [
        get_env("SOURCE_DIRECTORY"),
        get_env("BUILD_DIRECTORY"),
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        "--conf-dir",
        get_env("CONF_DIRECTORY"),
        f"--define=external_needs_source={get_env('EXTERNAL_NEEDS_INFO')}",
    ]

    # configure sphinx build with GitHub user and repo from CLI
    if args.github_user and args.github_repo:
        base_arguments.append(f"-A=github_user={args.github_user}")
        base_arguments.append(f"-A=github_repo={args.github_repo}")
        base_arguments.append("-A=github_version=main")
        base_arguments.append("-A=doc_path=docs")

    action = get_env("ACTION")
    if action == "live_preview":
        sphinx_autobuild_main(
            # Note: bools need to be passed via '0' and '1' from the command line.
            base_arguments
            + [
                "--define=disable_source_code_linker=1",
                f"--port={args.port}",
            ]
        )
    else:
        sphinx_main(base_arguments)
