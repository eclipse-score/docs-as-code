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
from copy import deepcopy
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import NeedsMutable, SphinxNeedsData, NeedsInfoType
from sphinx_needs.logging import get_logger

from src.extensions.score_source_code_linker.parse_source_files import (
    get_github_base_url,
)

LOGGER = get_logger(__name__)
LOGGER.setLevel("DEBUG")


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Extension: score_source_code_linker
    # TODO: can we detect live_preview & esbonio here? Until then we have a flag:
    app.add_config_value("disable_source_code_linker", False, rebuild="env", types=bool)
    app.add_config_value(
        "score_source_code_linker_file_overwrite", "", rebuild="env", types=str
    )

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


def find_need(
    all_needs: NeedsMutable, id: str, prefixes: list[str]
) -> NeedsInfoType | None:
    """
    Checks all possible external 'prefixes' for an ID
    So that the linker can add the link to the correct NeedsInfoType object.
    """
    if id in all_needs:
        return all_needs[id]

    # Try all possible prefixes
    for prefix in prefixes:
        prefixed_id = f"{prefix}{id}"
        if prefixed_id in all_needs:
            return all_needs[prefixed_id]

    return None


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
    p5 = Path(__file__).parents[5]

    if str(p5).endswith("src"):
        LOGGER.debug("DEBUG: WE ARE IN THE IF")
        path = str(p5.parent / Path(app.confdir).name / "score_source_code_parser.json")
    else:
        LOGGER.debug("DEBUG: WE ARE IN THE ELSE")
        path = str(p5 / "score_source_code_parser.json")

    if app.config.score_source_code_linker_file_overwrite:
        path = app.config.score_source_code_linker_file_overwrite

    # For some reason the prefix 'sphinx_needs internally' is CAPSLOCKED.
    # So we have to make sure we uppercase the prefixes
    prefixes = [x["id_prefix"].upper() for x in app.config.needs_external_needs]
    github_base_url = get_github_base_url() + "/blob/"
    try:
        with open(path) as f:
            gh_json = json.load(f)
        for id, link in gh_json.items():
            id = id.strip()
            need = find_need(needs_copy, id, prefixes)
            if need is None:
                # NOTE: manipulating link to remove git-hash,
                # making the output file location more readable
                files = [x.replace(github_base_url, "").split("/", 1)[-1] for x in link]
                LOGGER.warning(
                    f"Could not find {id} in the needs id's. "
                    + f"Found in file(s): {files}",
                    type="score_source_code_linker",
                )
                continue

            # NOTE: Removing & adding the need is important to make sure
            # the needs gets 're-evaluated'.
            Needs_Data.remove_need(need["id"])
            need["source_code_link"] = ",".join(link)
            Needs_Data.add_need(need)
    except Exception as e:
        LOGGER.warning(
            f"An unexpected error occurred while adding source_code_links to needs."
            + f"Error: {e}",
            type="score_source_code_linker",
        )
        LOGGER.warning(
            f"Reading file: {path} right now", type="score_source_code_linker"
        )
