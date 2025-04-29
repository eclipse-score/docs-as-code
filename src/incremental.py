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
import itertools
import os
import sys
import json
from pathlib import Path
from typing import Any

import debugpy

from python.runfiles import Runfiles
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import main as sphinx_autobuild_main

logger = logging.getLogger(__name__)

logger.debug("DEBUG: CWD: ", os.getcwd())
logger.debug("DEBUG: SOURCE_DIRECTORY: ", os.getenv("SOURCE_DIRECTORY"))
logger.debug("DEBUG: RUNFILES_DIR: ", os.getenv("RUNFILES_DIR"))


def get_env(name: str) -> str:
    val = os.environ.get(name, None)
    logger.debug(f"DEBUG: Env: {name} = {val}")
    if val is None:
        raise ValueError(f"Environment variable {name} is not set")
    return val


def transform_env_str_to_dict(external_needs_source: str) -> list[dict[str, str]]:
    """
    Transforms the 'string' we get from 'docs.bzl' back into something we can parse easliy inside sphinx/python
    !! HACK: This truly isn't great !!
    """
    l_dict = []
    x = [
        x.split(",")
        for x in external_needs_source.replace("]", "")
        .replace("[", "")
        .replace("{", "")
        .split("}")
    ]
    for d in x:
        b = [a.split(":", 1) for a in d if len(d) > 1]
        l = {a[0]: a[1] for a in b}
        if l:
            l_dict.append(l)
    return l_dict


if __name__ == "__main__":
    # Add debuging functionality
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-dp", "--debug_port", help="port to listen to debugging client", default=5678
    )
    parser.add_argument(
        "--debug", help="Enable Debugging via debugpy", action="store_true"
    )
    args = parser.parse_args()
    if args.debug:
        debugpy.listen(("0.0.0.0", args.debug_port))
        logger.info("Waiting for client to connect on port: " + str(args.debug_port))
        debugpy.wait_for_client()

    workspace = os.getenv("BUILD_WORKSPACE_DIRECTORY")
    if workspace:
        os.chdir(workspace)

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
        f"--define=external_needs_source={json.dumps(transform_env_str_to_dict(get_env('EXTERNAL_NEEDS_INFO')))}",
    ]
    action = get_env("ACTION")
    if action == "live_preview":
        sphinx_autobuild_main(
            base_arguments + ["--define=disable_source_code_linker=True"]
        )
    else:
        sphinx_main(base_arguments)
