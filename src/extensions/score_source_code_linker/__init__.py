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

"""In this file the actual sphinx extension is defined. It will read pre-generated
source code links from a JSON file and add them to the needs.
"""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import cast

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import NeedsInfoType, NeedsMutable, SphinxNeedsData
from sphinx_needs.logging import get_logger

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_git_root,
    find_ws_root,
    generate_source_code_links_json,
)
from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    load_source_code_links_json,
)
from src.extensions.score_source_code_linker.parse_source_files_OLD import (
    get_github_base_url,
)

LOGGER = get_logger(__name__)
LOGGER.setLevel("DEBUG")


def get_cache_filename(build_dir: Path) -> Path:
    """
    Returns the path to the cache file for the source code linker.
    This is used to store the generated source code links.
    """
    return build_dir / "score_source_code_linker_cache.json"


def setup_once(app: Sphinx):
    print(f"DEBUG: Workspace root is {find_ws_root()}")
    print(f"DEBUG: Current working directory is {Path('.')} = {Path('.').resolve()}")
    print(f"DEBUG: Git root is {find_git_root()}")

    # Run only for local files!
    # ws_root is not set when running on external repositories (dependencies).
    if not find_ws_root():
        return

    # Extension: score_source_code_linker
    app.add_config_value(
        "skip_rescanning_via_source_code_linker",
        False,
        rebuild="env",
        types=bool,
        description="Skip rescanning source code files via the source code linker.",
    )

    # Define need_string_links here to not have it in conf.py
    app.config.needs_string_links = {
        "source_code_linker": {
            "regex": r"(?P<url>.+)<>(?P<name>.+)",
            "link_url": "{{url}}",
            "link_name": "{{name}}",
            "options": ["source_code_link"],
        },
    }

    cache_json = get_cache_filename(Path(app.outdir))

    if (
        not cache_json.exists()
        or not app.config.skip_rescanning_via_source_code_linker
    ):
        LOGGER.debug(
            "INFO: Generating source code links JSON file.",
            type="score_source_code_linker",
        )

        generate_source_code_links_json(find_ws_root(), cache_json)

    app.connect("env-updated", inject_links_into_needs)


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Esbonio will execute setup() on every iteration.
    # setup_once will only be called once.
    if "skip_rescanning_via_source_code_linker" not in app.config:
        setup_once(app)

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
def inject_links_into_needs(app: Sphinx, env: BuildEnvironment) -> None:
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
    needs_copy = deepcopy(needs) # TODO: why do we create a copy?

    source_code_links = load_source_code_links_json(
        get_cache_filename(app.outdir)
    )

    # group source_code_links by need
    source_code_links_by_need: dict[str, list[NeedLink]] = defaultdict(list)
    for needlink in source_code_links:
        source_code_links_by_need[needlink.need].append(needlink)

    # For some reason the prefix 'sphinx_needs internally' is CAPSLOCKED.
    # So we have to make sure we uppercase the prefixes
    prefixes = [x["id_prefix"].upper() for x in app.config.needs_external_needs]
    github_base_url = get_github_base_url() + "/blob/"
    for needlink in source_code_links:
        need = find_need(needs_copy, needlink.need, prefixes)
        if need is None:
            # TODO: print github annotations as in https://github.com/eclipse-score/bazel_registry/blob/7423b9996a45dd0a9ec868e06a970330ee71cf4f/tools/verify_semver_compatibility_level.py#L126-L129
            LOGGER.warning(
                f"{needlink.file}:{needlink.line}: Could not find {needlink.need}",
                type="score_source_code_linker",
            )
        else:
            if "source_code_link" not in need:
                need["source_code_link"] = []  # type: ignore
            cast(dict[str, list[str]], need)["source_code_link"].append(
                # TODO: fix github link
                f"{github_base_url}{needlink.file}/{needlink.line}"
            )

            # NOTE: Removing & adding the need is important to make sure
            # the needs gets 're-evaluated'.
            Needs_Data.remove_need(need["id"])
            Needs_Data.add_need(need)
