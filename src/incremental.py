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
import hashlib
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import debugpy
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import (
    main as sphinx_autobuild_main,  # type: ignore[reportUnknownVariableType] # sphinx_autobuild doesn't provide complete type annotations
)

logger = logging.getLogger(__name__)

_MODULE_HASH_FILE = ".module_bazel_hash"


def get_env(name: str) -> str:
    val = os.environ.get(name, None)
    logger.debug(f"DEBUG: Env: {name} = {val}")
    if val is None:
        raise ValueError(f"Environment variable {name} is not set")
    return val


def _compute_hash(files: list[Path]) -> str:
    h = hashlib.sha256()
    for f in sorted(files, key=str):
        h.update(f.read_bytes())
    return h.hexdigest()


def clean_builddir_if_stale(build_dir: Path, sentinel_files: list[Path]) -> None:
    """Delete build_dir if the previous build had warnings or any sentinel file changed."""
    if not build_dir.exists():
        return

    warnings_txt = build_dir / "warnings.txt"
    has_warnings = warnings_txt.exists() and warnings_txt.stat().st_size > 0

    hash_file = build_dir / _MODULE_HASH_FILE
    hash_changed = (
        not hash_file.exists()
        or hash_file.read_text().strip() != _compute_hash(sentinel_files)
    )

    if has_warnings or hash_changed:
        print(
            "Previous build had warnings or the hash changed. Removing _build to ensure a clean build."
        )
        shutil.rmtree(build_dir)


def update_module_hash(build_dir: Path, sentinel_files: list[Path]) -> None:
    (build_dir / _MODULE_HASH_FILE).write_text(_compute_hash(sentinel_files))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Add debuging functionality
    parser.add_argument(
        "-dp", "--debug_port", help="port to listen to debugging client", default=5678
    )
    parser.add_argument(
        "--debug", help="Enable Debugging via debugpy", action="store_true"
    )
    parser.add_argument("--github_user", help=argparse.SUPPRESS)
    parser.add_argument("--github_repo", help=argparse.SUPPRESS)
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
        workspace += "/"
    else:
        workspace = ""

    build_dir = Path(workspace + "_build")
    sentinel_files = [
        Path(workspace + "MODULE.bazel"),
        Path(workspace + "MODULE.bazel.lock"),
        Path(workspace + "BUILD"),
    ]
    clean_builddir_if_stale(build_dir, sentinel_files)

    warning_file = Path(workspace + "_build/warnings.txt")

    base_arguments = [
        workspace + get_env("SOURCE_DIRECTORY"),
        workspace + "_build",
        "--warning-file",
        str(warning_file),
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        f"--define=external_needs_source={get_env('DATA')}",
    ]

    metamodel_yaml = os.environ.get("SCORE_METAMODEL_YAML", "")
    if metamodel_yaml:
        # Normalize to absolute path so it resolves correctly after Sphinx changes cwd
        if not os.path.isabs(metamodel_yaml):
            metamodel_yaml = workspace + metamodel_yaml
        metamodel_yaml = os.path.abspath(metamodel_yaml)
        base_arguments.append(f"--define=score_metamodel_yaml={metamodel_yaml}")

    github_user = os.getenv("GITHUB_REPOSITORY_OWNER")
    github_repo_env = os.getenv("GITHUB_REPOSITORY")
    github_repo = github_repo_env.split("/")[1] if github_repo_env else None

    if github_user and github_repo:
        base_arguments.append(f"-A=github_user={github_user}")
        base_arguments.append(f"-A=github_repo={github_repo}")
        base_arguments.append("-A=github_version=main")
        base_arguments.append(f"-A=doc_path={get_env('SOURCE_DIRECTORY')}")
    if os.getenv("KNOWN_GOOD_JSON"):
        base_arguments.append(f"--define=KNOWN_GOOD_JSON={get_env('KNOWN_GOOD_JSON')}")

    action = get_env("ACTION")
    if action == "live_preview":
        Path(workspace + "/_build/score_source_code_linker_cache.json").unlink(
            missing_ok=True
        )
        sphinx_autobuild_main(
            base_arguments
            + [
                # Note: bools need to be passed via '0' and '1' from the command line.
                "--define=skip_rescanning_via_source_code_linker=1",
                f"--port={args.port}",
            ]
        )
    else:
        if action == "incremental":
            builder = "html"
        elif action == "check":
            builder = "needs"
        elif action == "linkcheck":
            builder = "linkcheck"
        else:
            raise ValueError(f"Unknown action: {action}")

        base_arguments.extend(
            [
                "-b",
                builder,
            ]
        )

        start_time = time.perf_counter()
        exit_code = sphinx_main(base_arguments)
        end_time = time.perf_counter()
        print(f"docs ({action}) finished in {end_time - start_time:.1f} seconds")

        if exit_code == 0:
            update_module_hash(build_dir, sentinel_files)
        else:
            with warning_file.open("a", encoding="utf-8") as f:
                f.write("-" * 80 + "\n")
                f.write(f"Build failed with exit code {exit_code}\n")

        sys.exit(exit_code)
