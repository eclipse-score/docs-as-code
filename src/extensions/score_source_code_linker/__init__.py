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

"""
In this file the actual sphinx extension is defined. It will read pre-generated
source code links from a JSON file and add them to the needs.
"""

# req-Id: tool_req__docs_test_link_testcase
# req-Id: tool_req__docs_dd_link_source_code_link
# This whole directory implements the above mentioned tool requirements

import os
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import cast

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import NeedsMutable, SphinxNeedsData
from sphinx_needs.logging import get_logger
from sphinx_needs.need_item import NeedItem

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    generate_source_code_links_json,
)
from src.extensions.score_source_code_linker.need_source_links import (
    NeedSourceLinks,
    SourceCodeLinks,
    load_source_code_links_combined_json,
    store_source_code_links_combined_json,
)
from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    load_source_code_links_json,
)
from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
    load_data_of_test_case_json,
    load_test_xml_parsed_json,
)
from src.extensions.score_source_code_linker.xml_parser import (
    construct_and_add_need,
    run_xml_parser,
)
from src.helper_lib import (
    find_git_root,
    find_ws_root,
)
from src.helper_lib.additional_functions import get_github_link

LOGGER = get_logger(__name__)
# Uncomment this to enable more verbose logging
# LOGGER.setLevel("DEBUG")


# re-qid: gd_req__req_attr_impl
#          ╭──────────────────────────────────────╮
#          │       JSON FILE RELATED FUNCS        │
#          ╰──────────────────────────────────────╯


def group_by_need(
    source_code_links: list[NeedLink],
    test_case_links: list[DataForTestLink] | None = None,
) -> list[SourceCodeLinks]:
    """
    Groups the given need links and test case links by their need ID.
    Returns a nested dictionary structure with 'CodeLink' and 'TestLink' categories.
    Example output:


      {
        "need": "<need_id>",
        "links": {
          "CodeLinks": [NeedLink, NeedLink, ...],
          "TestLinks": [testlink, testlink, ...]
        }
      }
    """
    # TODO: I wonder if there is a more efficent way to do this
    grouped_by_need: dict[str, NeedSourceLinks] = defaultdict(
        lambda: NeedSourceLinks(TestLinks=[], CodeLinks=[])
    )

    # Group source code links
    for needlink in source_code_links:
        grouped_by_need[needlink.need].CodeLinks.append(needlink)

    # Group test case links
    if test_case_links is not None:
        for testlink in test_case_links:
            grouped_by_need[testlink.need].TestLinks.append(testlink)

    # Build final list of SourceCodeLinks
    result: list[SourceCodeLinks] = [
        SourceCodeLinks(
            need=need,
            links=NeedSourceLinks(
                CodeLinks=need_links.CodeLinks,
                TestLinks=need_links.TestLinks,
            ),
        )
        for need, need_links in grouped_by_need.items()
    ]

    return result


def get_cache_filename(build_dir: Path, filename: str) -> Path:
    """
    Returns the path to the cache file for the source code linker.
    This is used to store the generated source code links.
    """
    return build_dir / filename


def build_and_save_combined_file(outdir: Path):
    """
    Reads the saved partial caches of codelink & testlink
    Builds the combined JSON cache & saves it
    """
    source_code_links_json = os.environ.get("SCORE_SOURCELINKS")
    if not source_code_links_json:
        # Fallback to the obsolete way of doing source code links,
        # just in case someone is not using the docs(sourcelinks=...) attribute.
        # TODO: Remove this once backwards compatibility is not needed anymore.
        source_code_links_json = get_cache_filename(
            outdir, "score_source_code_linker_cache.json"
        )
    else:
        source_code_links_json = Path(source_code_links_json)

    source_code_links = load_source_code_links_json(source_code_links_json)
    test_code_links = load_test_xml_parsed_json(
        get_cache_filename(outdir, "score_xml_parser_cache.json")
    )

    store_source_code_links_combined_json(
        outdir / "score_scl_grouped_cache.json",
        group_by_need(source_code_links, test_code_links),
    )


#          ╭──────────────────────────────────────╮
#          │         ONE TIME SETUP FUNCS         │
#          ╰──────────────────────────────────────╯


def setup_source_code_linker(app: Sphinx, ws_root: Path):
    """
    Setting up source_code_linker with all needed options.
    Allows us to only have this run once during live_preview & esbonio
    """
    app.add_config_value(
        "skip_rescanning_via_source_code_linker",
        False,
        rebuild="env",
        types=bool,
        description="Skip rescanning source code files via the source code linker.",
    )

    # Define need_string_links here to not have it in conf.py
    # source_code_link and testlinks have the same schema
    app.config.needs_string_links = {
        "source_code_linker": {
            "regex": r"(?P<url>.+)<>(?P<name>.+)",
            "link_url": "{{url}}",
            "link_name": "{{name}}",
            "options": ["source_code_link", "testlink"],
        },
    }

    score_sourcelinks_json = os.environ.get("SCORE_SOURCELINKS")
    if score_sourcelinks_json:
        # No need to generate the JSON file if this env var is set
        # because it points to an existing file with the needed data.
        return

    scl_cache_json = get_cache_filename(
        app.outdir, "score_source_code_linker_cache.json"
    )

    if (
        not scl_cache_json.exists()
        or not app.config.skip_rescanning_via_source_code_linker
    ):
        LOGGER.debug(
            "INFO: Generating source code links JSON file.",
            type="score_source_code_linker",
        )

        generate_source_code_links_json(ws_root, scl_cache_json)


def register_test_code_linker(app: Sphinx):
    # Connects function to sphinx to ensure correct execution order
    # priority is set to make sure it is called in the right order.
    # Before the combining action
    app.connect("env-updated", setup_test_code_linker, priority=505)


def setup_test_code_linker(app: Sphinx, env: BuildEnvironment):
    # TODO instead of implementing our own caching here, we should rely on Bazel
    tl_cache_json = get_cache_filename(app.outdir, "score_xml_parser_cache.json")
    if (
        not tl_cache_json.exists()
        or not app.config.skip_rescanning_via_source_code_linker
    ):
        ws_root = find_ws_root()
        if not ws_root:
            return
        LOGGER.debug(
            "INFO: Generating score_xml_parser JSON file.",
            type="score_source_code_linker",
        )
        # sanity check if extension is enabled
        bazel_testlogs = ws_root / "bazel-testlogs"
        if not bazel_testlogs.exists():
            LOGGER.info(f"{'=' * 80}", type="score_source_code_linker")
            LOGGER.info(
                f"{'=' * 32}SCORE XML PARSER{'=' * 32}", type="score_source_code_linker"
            )
            LOGGER.info(
                "'bazel-testlogs' was not found. If test data should be parsed,"
                + "please run tests before building the documentation",
                type="score_source_code_linker",
            )
            LOGGER.info(f"{'=' * 80}", type="score_source_code_linker")
            return

        run_xml_parser(app, env)
        return
    tcn_cache = get_cache_filename(app.outdir, "score_testcaseneeds_cache.json")
    assert tcn_cache.exists(), (
        f"TestCaseNeed Cache file does not exist.Checked Path: {tcn_cache}"
    )
    # TODO: Make this more efficent, idk how though.
    test_case_needs = load_data_of_test_case_json(tcn_cache)
    for tcn in test_case_needs:
        construct_and_add_need(app, tcn)


def register_combined_linker(app: Sphinx):
    # Registering the combined linker to Sphinx
    # priority is set to make sure it is called in the right order.
    # Needs to be called after xml parsing & codelink
    app.connect("env-updated", setup_combined_linker, priority=507)


def setup_combined_linker(app: Sphinx, _: BuildEnvironment):
    grouped_cache = get_cache_filename(app.outdir, "score_scl_grouped_cache.json")
    gruped_cache_exists = grouped_cache.exists()
    # TODO this cache should be done via Bazel
    if not gruped_cache_exists or not app.config.skip_rescanning_via_source_code_linker:
        LOGGER.debug(
            "Did not find combined json 'score_scl_grouped_cache.json' in _build."
            "Generating new one"
        )
        build_and_save_combined_file(app.outdir)


def setup_once(app: Sphinx):
    # might be the only way to solve this?
    if "skip_rescanning_via_source_code_linker" in app.config:
        return
    LOGGER.debug(f"DEBUG: Workspace root is {find_ws_root()}")
    LOGGER.debug(
        f"DEBUG: Current working directory is {Path('.')} = {Path('.').resolve()}"
    )
    LOGGER.debug(f"DEBUG: Git root is {find_git_root()}")

    # Run only for local files!
    # ws_root is not set when running on external repositories (dependencies).
    ws_root = find_ws_root()
    if not ws_root:
        return

    # When BUILD_WORKSPACE_DIRECTORY is set, we are inside a git repository.
    assert find_git_root()

    # Register & Run (if needed) parsing & saving of JSON caches
    setup_source_code_linker(app, ws_root)
    register_test_code_linker(app)
    register_combined_linker(app)

    # Priorty=510 to ensure it's called after the test code linker & combined connection
    app.connect("env-updated", inject_links_into_needs, priority=510)


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Esbonio will execute setup() on every iteration.
    # setup_once will only be called once.
    setup_once(app)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def find_need(all_needs: NeedsMutable, id: str) -> NeedItem | None:
    """
    Finds a need by ID in the needs collection.
    """
    return all_needs.get(id)


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
    ws_root = find_ws_root()
    assert ws_root

    Needs_Data = SphinxNeedsData(env)
    needs = Needs_Data.get_needs_mutable()
    needs_copy = deepcopy(
        needs
    )  # TODO: why do we create a copy? Can we also needs_copy = needs[:]? copy(needs)?

    # Enabled automatically for DEBUGGING
    if LOGGER.getEffectiveLevel() >= 10:
        for id, need in needs.items():
            if need.get("source_code_link"):
                LOGGER.debug(
                    f"?? Need {id} already has source_code_link: "
                    f"{need.get('source_code_link')}"
                )
            if need.get("testlink"):
                LOGGER.debug(
                    f"?? Need {id} already has testlink: {need.get('testlink')}"
                )

    source_code_links_by_need = load_source_code_links_combined_json(
        get_cache_filename(app.outdir, "score_scl_grouped_cache.json")
    )

    for source_code_links in source_code_links_by_need:
        need = find_need(needs_copy, source_code_links.need)
        if need is None:
            # TODO: print github annotations as in https://github.com/eclipse-score/bazel_registry/blob/7423b9996a45dd0a9ec868e06a970330ee71cf4f/tools/verify_semver_compatibility_level.py#L126-L129
            for n in source_code_links.links.CodeLinks:
                LOGGER.warning(
                    f"{n.file}:{n.line}: Could not find {source_code_links.need} "
                    "in documentation [CODE LINK]",
                    type="score_source_code_linker",
                )
            for n in source_code_links.links.TestLinks:
                LOGGER.warning(
                    f"{n.file}:{n.line}: Could not find {source_code_links.need} "
                    "in documentation [TEST LINK]",
                    type="score_source_code_linker",
                )
            continue

        need_as_dict = cast(dict[str, object], need)

        modified_need = False
        if source_code_links.links.CodeLinks:
            modified_need = True
            need_as_dict["source_code_link"] = ", ".join(
                f"{get_github_link(n)}<>{n.file}:{n.line}"
                for n in source_code_links.links.CodeLinks
            )
        if source_code_links.links.TestLinks:
            modified_need = True
            need_as_dict["testlink"] = ", ".join(
                f"{get_github_link(n)}<>{n.name}" for n in source_code_links.links.TestLinks
            )

        if modified_need:
            # NOTE: Removing & adding the need is important to make sure
            # the needs gets 're-evaluated'.
            Needs_Data.remove_need(need["id"])
            Needs_Data.add_need(need)


#          ╭──────────────────────────────────────╮
#          │ WARNING: This somehow screws up the  │
#          │       integration test? What??       │
#          │        Commented out for now         │
#          ╰──────────────────────────────────────╯

# source_code_link of affected needs was overwritten.
# Make sure it's empty in all others!
# for need in needs.values():
#     if need["id"] not in source_code_links_by_need:
#         need["source_code_link"] = ""  # type: ignore
#         need["testlink"] = ""  # type: ignore
