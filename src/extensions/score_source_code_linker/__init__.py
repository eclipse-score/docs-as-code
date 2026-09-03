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
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import NeedsMutable, SphinxNeedsData
from sphinx_needs.logging import get_logger
from sphinx_needs.need_item import NeedItem

from src.extensions.score_source_code_linker.helpers import get_github_link
from src.extensions.score_source_code_linker.need_source_links import (
    group_by_need,
    load_source_code_links_combined_json,
    store_source_code_links_combined_json,
)
from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    load_source_code_links_json,
    load_source_code_links_with_metadata_json,
)
from src.extensions.score_source_code_linker.repo_source_links import (
    RepoInfo,
    group_needs_by_repo,
    load_repo_source_links_json,
    store_repo_source_links_json,
)
from src.extensions.score_source_code_linker.testcase_annotations import (
    annotate_testcase_results,
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
from src.helper_lib import find_ws_root

LOGGER = get_logger(__name__)
# Uncomment this to enable more verbose logging
# LOGGER.setLevel("DEBUG")


# re-qid: gd_req__req_attr_impl
#          ╭──────────────────────────────────────╮
#          │       JSON FILE RELATED FUNCS        │
#          ╰──────────────────────────────────────╯


def get_cache_filename(build_dir: Path, filename: str) -> Path:
    """
    Returns the path to the cache file for the source code linker.
    This is used to store the generated source code links.
    """
    return build_dir / filename


def build_and_save_combined_file(outdir: Path, app: Sphinx | None = None):
    """
    Reads the saved partial caches of codelink & testlink
    Builds the combined JSON cache & saves it
    """
    source_code_links_path = os.environ.get("SCORE_SOURCELINKS")
    if not source_code_links_path and app is not None:
        source_code_links_path = str(
            getattr(app.config, "score_sourcelinks_json", "") or ""
        ).strip()
    if source_code_links_path:
        source_code_links_json = Path(source_code_links_path)
        try:
            source_code_links = load_source_code_links_json(source_code_links_json)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "Pre-generated source-code links file does not exist: "
                f"{source_code_links_json}. Check SCORE_SOURCELINKS or "
                "score_sourcelinks_json."
            ) from exc
        except AssertionError:
            source_code_links = load_source_code_links_with_metadata_json(
                source_code_links_json
            )
    else:
        LOGGER.debug(
            "No pre-generated source-code links provided. Continuing without code links.",
            type="score_source_code_linker",
        )
        source_code_links = []
    test_cache = get_cache_filename(outdir, "score_xml_parser_cache.json")
    if test_cache.exists():
        test_code_links = load_test_xml_parsed_json(test_cache)
    else:
        LOGGER.debug(
            "No score_xml_parser_cache.json found. Continuing without test XML links.",
            type="score_source_code_linker",
        )
        test_code_links = []
    scl_list = group_by_need(source_code_links, test_code_links)
    store_source_code_links_combined_json(
        outdir / "score_scl_grouped_cache.json", scl_list
    )


#          ╭──────────────────────────────────────╮
#          │         ONE TIME SETUP FUNCS         │
#          ╰──────────────────────────────────────╯


def setup_source_code_linker(app: Sphinx):
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

    # Define need_string_links here to not have them in conf.py. Test links
    # carry the result as an additional field in their serialized value.
    app.config.needs_string_links.setdefault(
        "source_code_linker_pure",
        {
            "regex": r"(?P<url>.+)<>(?P<name>.+)",
            "link_url": "{{url}}",
            "link_name": "{{name}}",
            "options": ["source_code_link"],
        },
    )
    app.config.needs_string_links.setdefault(
        "test_code_linker",
        {
            "regex": r"(?P<url>.+)<>(?P<name>.+)<>(?P<result>.+)",
            "link_url": "{{url}}",
            "link_name": "{{name}} ({{result}})",
            "options": ["testlink"],
        },
    )


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
        test_folder = ws_root / "tests-report"
        if not (bazel_testlogs.exists() or test_folder.exists()):
            LOGGER.info(f"{'=' * 80}", type="score_source_code_linker")
            LOGGER.info(
                f"{'=' * 32}SCORE XML PARSER{'=' * 32}", type="score_source_code_linker"
            )
            LOGGER.info(
                "'bazel-testlogs' and 'tests-report' both were not found. If test data should be parsed,"
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
    # Registering the final combine linker to Sphinx
    # priority is set to make sure it is called in the right order.
    # Needs to be called after xml parsing & codelink & combined_linker
    app.connect("env-updated", setup_combined_linker, priority=510)


def setup_combined_linker(app: Sphinx, _: BuildEnvironment):
    grouped_cache = get_cache_filename(app.outdir, "score_scl_grouped_cache.json")
    grouped_cache_exists = grouped_cache.exists()
    # TODO this cache should be done via Bazel
    if (
        not grouped_cache_exists
        or not app.config.skip_rescanning_via_source_code_linker
    ):
        LOGGER.debug(
            "Did not find combined json 'score_scl_grouped_cache.json' in _build."
            "Generating new one"
        )
        build_and_save_combined_file(app.outdir, app)


def register_repo_linker(app: Sphinx):
    # Registering the combined linker to Sphinx
    # priority is set to make sure it is called in the right order.
    # Needs to be called after xml parsing & codelink
    app.connect("env-updated", setup_repo_linker, priority=520)


def build_and_save_repo_scl_file(outdir: Path):
    scl_links = load_source_code_links_combined_json(
        get_cache_filename(outdir, "score_scl_grouped_cache.json")
    )
    mcl_links = group_needs_by_repo(scl_links)
    store_repo_source_links_json(
        outdir / "score_repo_grouped_scl_cache.json", mcl_links
    )


def setup_repo_linker(app: Sphinx, _: BuildEnvironment):
    grouped_cache = get_cache_filename(app.outdir, "score_repo_grouped_scl_cache.json")
    grouped_cache_exists = grouped_cache.exists()
    # TODO this cache should be done via Bazel
    if (
        not grouped_cache_exists
        or not app.config.skip_rescanning_via_source_code_linker
    ):
        LOGGER.debug(
            "Did not find combined json 'score_module_grouped_scl_cache.json' "
            "in _build. Generating new one"
        )
        build_and_save_repo_scl_file(app.outdir)


def setup_once(app: Sphinx):
    # might be the only way to solve this?
    if "skip_rescanning_via_source_code_linker" in app.config:
        return
    # Register & Run (if needed) parsing & saving of JSON caches
    # Note: This extension now runs on both internal and external needs_json invocations.
    # Both modes aggregate links from local sources and external dependencies, enabling
    # unified traceability reporting in integration repositories. Impact on external needs
    # invocations is minimal since they typically don't have local test logs or source code.
    setup_source_code_linker(app)
    register_test_code_linker(app)
    register_combined_linker(app)
    register_repo_linker(app)

    # Priority=515 to ensure it's called after the test linker & combined connection
    app.connect("env-updated", inject_links_into_needs, priority=525)

    # sphinx-needs resolves NeedIncoming and need metadata links on the same event.
    # Run after those resolvers so the GitHub references are available to annotate.
    app.connect("doctree-resolved", annotate_testcase_results, priority=800)


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Esbonio will execute setup() on every iteration.
    # setup_once will only be called once.

    # Config values for source code linking and testcase metadata integration
    app.add_config_value(
        "KNOWN_GOOD_JSON",
        default="",
        rebuild="env",
        types=str,
        description="Path to pre-generated source code links JSON (optional fallback)",
    )
    app.add_config_value(
        "score_sourcelinks_json",
        default="",
        rebuild="env",
        types=str,
        description="Path to pre-generated source code links JSON from Bazel via SCORE_SOURCELINKS env var",
    )
    app.add_config_value(
        "score_source_code_linker_plain_links",
        default=False,
        rebuild="env",
        types=bool,
        description="If True, render links as plain text without GitHub URLs (useful for Bazel sandbox builds)",
    )
    app.add_config_value(
        "testcase_source_dirs",
        default="",
        rebuild="env",
        types=str,
        description=(
            "str(list) of repo-relative directory paths. When set, the test-code-linker "
            "only builds testcase needs for testcases whose source file lives under one of "
            "these directories. Empty means no filtering (scan the whole workspace)."
        ),
    )
    setup_once(app)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _extract_version_from_id(id: str) -> tuple[str, int | None]:
    """Extract base ID and version number from a potentially versioned need ID.

    Examples:
        "req_id" => ("req_id", None)
        "req_id[version==2]" => ("req_id", 2)
    """
    import re

    match = re.search(r"\[version==(\d+)\]", id)
    if match:
        return re.sub(r"\[version==[^\]]+\]", "", id), int(match.group(1))
    return id, None


def find_need(all_needs: NeedsMutable, id: str) -> NeedItem | None:
    """
    Finds a need by ID in the needs collection.
    Strips version suffixes for lookup and warns if test links to older version.
    """
    base_id, test_version = _extract_version_from_id(id)
    need = all_needs.get(base_id)

    # Check version compatibility if version was specified
    # req-Id: tool_req__docs_common_attr_suspicious
    if need is not None and test_version is not None:
        need_version = need.get("version")
        if need_version is not None and int(need_version) > test_version:
            LOGGER.warning(
                f"Test links to outdated version: '{id}' references "
                f"version {test_version}, but need '{base_id}' is version {need_version}. "
                f"Update test to reference version {need_version}.",
                type="score_source_code_linker",
            )

    return need


def _log_existing_links(needs: NeedsMutable) -> None:
    """Emit debug logs for needs that already contain source/test links."""
    if not LOGGER.isEnabledFor(10):
        return

    for need_id, need in needs.items():
        if need.get("source_code_link"):
            LOGGER.debug(
                f"?? Need {need_id} already has source_code_link: "
                f"{need.get('source_code_link')}"
            )
        if need.get("testlink"):
            LOGGER.debug(
                f"?? Need {need_id} already has testlink: {need.get('testlink')}"
            )


def _render_code_link(plain_links: bool, metadata: RepoInfo, link: NeedLink) -> str:
    if plain_links:
        # Bazel sandbox builds have no git metadata, so we can't construct a real GitHub URL.
        return (
            "https://github.com/placeholder/placeholder/blob/unknown/"
            f"{link.file}#L{link.line}<>{link.file}:{link.line}"
        )
    try:
        base = get_github_link(metadata, link)
    except AssertionError:
        LOGGER.info(
            "Falling back to local code-link format (no git remote available): "
            f"{link.file}:{link.line}",
            type="score_source_code_linker",
        )
        return f"{link.file}:{link.line}"
    return f"{base}<>{link.file}:{link.line}"


def _render_test_link(
    plain_links: bool,
    metadata: RepoInfo,
    link: DataForTestLink,
) -> str:
    if plain_links:
        return str(link.name)
    try:
        base = get_github_link(metadata, link)
    except AssertionError:
        LOGGER.info(
            "Falling back to local test-link format (no git remote available): "
            f"{link.name}",
            type="score_source_code_linker",
        )
        return str(link.name)
    return f"{base}<>{link.name}<>{link.result}"


def _warn_missing_need(source_code_links: object) -> None:
    links = cast(Any, source_code_links).links
    need_id = cast(Any, source_code_links).need

    for code_link in links.CodeLinks:
        LOGGER.warning(
            f"{code_link.file}:{code_link.line}: Could not find {need_id} "
            "in documentation [CODE LINK]",
            type="score_source_code_linker",
        )
    for test_link in links.TestLinks:
        LOGGER.warning(
            f"{test_link.file}:{test_link.line}: Could not find {need_id} "
            "in documentation [TEST LINK]",
            type="score_source_code_linker",
        )


def _apply_links_to_need(
    needs_data: SphinxNeedsData,
    need: NeedItem,
    source_code_links: object,
    metadata: RepoInfo,
    plain_links: bool,
) -> None:
    links = cast(Any, source_code_links).links
    need_as_dict = cast(dict[str, object], need)
    need_as_dict["source_code_link"] = ", ".join(
        _render_code_link(plain_links, metadata, code_link)
        for code_link in links.CodeLinks
    )
    need_as_dict["testlink"] = ", ".join(
        _render_test_link(plain_links, metadata, test_link)
        for test_link in links.TestLinks
    )

    # NOTE: Removing & adding the need is important to make sure
    # the needs gets 're-evaluated'.
    needs_data.remove_need(need["id"])
    needs_data.add_need(need)


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
    needs_data = SphinxNeedsData(env)
    needs = needs_data.get_needs_mutable()
    needs_copy = deepcopy(
        needs
    )  # TODO: why do we create a copy? Can we also needs_copy = needs[:]? copy(needs)?

    _log_existing_links(needs)

    scl_by_module = load_repo_source_links_json(
        get_cache_filename(app.outdir, "score_repo_grouped_scl_cache.json")
    )
    plain_links = bool(
        getattr(app.config, "score_source_code_linker_plain_links", False)
    )

    for module_grouped_needs in scl_by_module:
        for source_code_links in module_grouped_needs.needs:
            need = find_need(needs_copy, source_code_links.need)
            if need is None:
                # TODO: print github annotations as in https://github.com/eclipse-score/bazel_registry/blob/7423b9996a45dd0a9ec868e06a970330ee71cf4f/tools/verify_semver_compatibility_level.py#L126-L129
                _warn_missing_need(source_code_links)
                continue

            _apply_links_to_need(
                needs_data=needs_data,
                need=need,
                source_code_links=source_code_links,
                metadata=module_grouped_needs.repo,
                plain_links=plain_links,
            )


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
