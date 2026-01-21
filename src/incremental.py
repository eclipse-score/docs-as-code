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
import logging
import os
import sys
import time
from pathlib import Path

import debugpy
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import (
    main as sphinx_autobuild_main,  # type: ignore[reportUnknownVariableType] # sphinx_autobuild doesn't provide complete type annotations
)

logger = logging.getLogger(__name__)


def get_env(name: str) -> str:
    val = os.environ.get(name, None)
    logger.debug(f"DEBUG: Env: {name} = {val}")
    if val is None:
        raise ValueError(f"Environment variable {name} is not set")
    return val


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Add debuging functionality
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
        workspace += "/"
    else:
        workspace = ""

    base_arguments = [
        workspace + get_env("SOURCE_DIRECTORY"),
        workspace + "_build",
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        f"--define=external_needs_source={get_env('DATA')}",
    ]

    # configure sphinx build with GitHub user and repo from CLI
    if args.github_user and args.github_repo:
        base_arguments.append(f"-A=github_user={args.github_user}")
        base_arguments.append(f"-A=github_repo={args.github_repo}")
        base_arguments.append("-A=github_version=main")
        base_arguments.append(f"-A=doc_path={get_env('SOURCE_DIRECTORY')}")

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
        duration = end_time - start_time
        print(f"docs ({action}) finished in {duration:.1f} seconds")

        sys.exit(exit_code)
