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
import json
import os
from copy import deepcopy
from pathlib import Path
from pprint import pprint

from src.extensions.score_source_code_linker.parse_source_files import GITHUB_BASE_URL
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.logging import get_logger

LOGGER = get_logger(__name__)
LOGGER.setLevel("DEBUG")


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Extension: score_source_code_linker
    app.add_config_value("disable_source_code_linker", False, rebuild="env")
    app.add_config_value("score_source_code_linker_file_overwrite", "", rebuild="env")
    # TODO: can we detect live_preview & esbonio here? Until then we have a flag:

    # Define need_string_links here to not have it in conf.py
    app.config.needs_string_links = {
        "source_code_linker": {
            "regex": r"(?P<value>[^,]+)",
            "link_url": "{{value}}",
            "link_name": "Source Code Link",
            "options": ["source_code_link"],
        },
    }
    if app.config.disable_source_code_linker:
        LOGGER.info(
            "INFO: Disabled source code linker. Not loading extension.",
            type="score_source_code_linker",
        )
    else:
        LOGGER.debug(
            "INFO: Loading source code linker...", type="score_source_code_linker"
        )
        app.connect("env-updated", add_source_link)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


# re-qid: gd_req__req__attr_impl
def add_source_link(app: Sphinx, env: BuildEnvironment) -> None:
    """
    'Main' function that facilitates the running of all other functions
    in correct order.
    This function is also 'connected' to the message Sphinx emits,
    therefore the one that's called directly.
    Args:
        env: Buildenvironment, this is filled automatically
        app: Sphinx app application, this is filled automatically
    """

    Needs_Data = SphinxNeedsData(env)
    needs = Needs_Data.get_needs_mutable()
    needs_copy = deepcopy(needs)
    # bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles/_main/process-docs/score_source_code_parser.json
    # bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles/_main/tooling/extensions/score_source_code_linker/__init__.py
    # bazel-out/k8-fastbuild/bin/process-docs/score_source_code_parser.json
    # /home/vscode/.cache/bazel/_bazel_vscode/6084288f00f33db17acb4220ce8f1999/execroot/_main/bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles/score_source_code_parser.json
    #

    ## -> build:

    # bazel-out/k8-opt-exec-ST-d57f47055a04/bin/tooling/sphinx_build.runfiles/_main/tooling/extensions/score_source_code_linker/__init__.py

    # Tried with build
    # bazel-out/k8-fastbuild/bin/process-docs/_docs/_sources/process-docs/score_source_code_parser.json

    # SEARCHING:
    # bazel-out/k8-opt-exec-ST-d57f47055a04/bin/process-docs/score_source_code_parser.json
    p5 = Path(__file__).parents[5]

    # bazel-out/k8-opt-exec-ST-d57f47055a04/bin/tooling
    # LOGGER.info("DEBUG: ============= CONF DIR===========")
    # LOGGER.info(f"DEBUG: {Path(app.confdir).name}")
    # LOGGER.info("DEBUG: =============================")
    if str(p5).endswith("src"):
        LOGGER.info("DEBUG: WE ARE IN THE IF")
        path = str(p5.parent / Path(app.confdir).name / "score_source_code_parser.json")
    else:
        LOGGER.info("DEBUG: WE ARE IN THE ELSE")
        path = str(p5 / "score_source_code_parser.json")
    # LOGGER.info("DEBUG============= FILE PATH OF JSON (where we search)===========")
    # LOGGER.info(f"DEBUG: {path}")
    # LOGGER.info("DEBUG: =============================")
    if app.config.score_source_code_linker_file_overwrite:
        path = app.config.score_source_code_linker_file_overwrite
    # json_paths = [str(Path(__file__).parent.parent.parent.parent.parent.parent/"score_source_code_parser.json")]
    # json_paths = [app.config.source_code_linker_file]

    try:
        with open(path) as f:
            gh_json = json.load(f)
        for id, link in gh_json.items():
            id = id.strip()
            try:
                # NOTE: Removing & adding the need is important to make sure
                # the needs gets 're-evaluated'.
                need = needs_copy[id]  # NeedsInfoType
                Needs_Data.remove_need(need["id"])
                need["source_code_link"] = ",".join(link)
                Needs_Data.add_need(need)
            except KeyError:
                # NOTE: manipulating link to remove git-hash,
                # making the output file location more readable
                files = [x.replace(GITHUB_BASE_URL, "").split("/", 1)[-1] for x in link]
                LOGGER.warning(
                    f"Could not find {id} in the needs id's. "
                    + f"Found in file(s): {files}",
                    type="score_source_code_linker",
                )
    except Exception as e:
        LOGGER.warning(
            f"An unexpected error occurred while adding source_code_links to needs."
            + f"Error: {e}",
            type="score_source_code_linker",
        )
        LOGGER.warning(
            f"Reading file: {path} right now", type="score_source_code_linker"
        )
