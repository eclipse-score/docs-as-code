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
import importlib
import json
import os
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ruamel.yaml import YAML
from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.config import NeedType
from sphinx_needs.data import NeedsInfoType, NeedsView, SphinxNeedsData

from src.helper_lib import (
    find_git_root,
    find_ws_root,
    get_current_git_hash,
    get_github_repo_info,
)

from .external_needs import connect_external_needs
from .log import CheckLogger

logger = logging.get_logger(__name__)

local_check_function = Callable[[Sphinx, NeedsInfoType, CheckLogger], None]
graph_check_function = Callable[[Sphinx, NeedsView, CheckLogger], None]

local_checks: list[local_check_function] = []
graph_checks: list[graph_check_function] = []


@dataclass
class ScoreNeedType(NeedType):
    tags: list[str]
    parts: int


@dataclass
class ProhibitedWordCheck:
    name: str
    option_check: dict[str, list[str]] = field(
        default_factory=dict
    )  # { Option: [Forbidden words]}
    types: list[str] = field(default_factory=list)


def parse_checks_filter(filter: str) -> list[str]:
    """
    Parses a comma-separated list of check names.
    Returns all names after trimming spaces and ensures
    each exists in local_checks or graph_checks.
    """
    if not filter:
        return []
    checks = [check.strip() for check in filter.split(",")]

    # Validate all checks exist in either local_checks or graph_checks
    all_check_names = {c.__name__ for c in local_checks} | {
        c.__name__ for c in graph_checks
    }
    for check in checks:
        assert check in all_check_names, (
            f"Check: '{check}' is not one of the defined local or graph checks"
        )

    return checks


def discover_checks():
    """
    Dynamically import all checks.
    They will self-register with the decorators below.
    """

    package_name = ".checks"  # load ./checks/*.py
    package = importlib.import_module(package_name, __package__)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        logger.debug(f"Importing check module: {module_name}")
        importlib.import_module(f"{package_name}.{module_name}", __package__)


def local_check(func: local_check_function):
    """Use this decorator to mark a function as a local check."""
    logger.debug(f"new local_check: {func}")
    local_checks.append(func)
    return func


def graph_check(func: graph_check_function):
    """Use this decorator to mark a function as a graph check."""
    logger.debug(f"new graph_check: {func}")
    graph_checks.append(func)
    return func


def _run_checks(app: Sphinx, exception: Exception | None) -> None:
    # Do not run checks if an exception occurred during build
    if exception:
        return

    # Filter out external needs, as checks are only intended to be run
    # on internal needs.
    needs_all_needs = SphinxNeedsData(app.env).get_needs_view()

    logger.debug(f"Running checks for {len(needs_all_needs)} needs")

    ws_root = os.environ.get("BUILD_WORKSPACE_DIRECTORY", None)
    cwd_or_ws_root = Path(ws_root) if ws_root else Path.cwd()
    prefix = str(Path(app.srcdir).relative_to(cwd_or_ws_root))

    log = CheckLogger(logger, prefix)

    checks_filter = parse_checks_filter(app.config.score_metamodel_checks)

    def is_check_enabled(check: local_check_function | graph_check_function):
        return not checks_filter or check.__name__ in checks_filter

    enabled_local_checks = [c for c in local_checks if is_check_enabled(c)]

    needs_local_needs = (
        SphinxNeedsData(app.env).get_needs_view().filter_is_external(False)
    )
    # Need-Local checks: checks which can be checked file-local, without a
    # graph of other needs.
    for need in needs_local_needs.values():
        for check in enabled_local_checks:
            logger.debug(f"Running local check {check} for need {need['id']}")
            check(app, need, log)

    # Graph-Based checks: These warnings require a graph of all other needs to
    # be checked.

    for check in [c for c in graph_checks if is_check_enabled(c)]:
        logger.debug(f"Running graph check {check} for all needs")
        check(app, needs_all_needs, log)

    if log.has_warnings:
        log.warning("Some needs have issues. See the log for more information.")

    if log.has_infos:
        log.info(
            "Some needs have issues related to the new checks. "
            "See the log for more information."
        )
        # TODO: exit code


def convert_checks_to_dataclass(checks_dict) -> list[ProhibitedWordCheck]:
    return [
        ProhibitedWordCheck(
            name=check_name,
            option_check={k: v for k, v in check_config.items() if k != "types"},
            types=check_config.get("types", []),
        )
        for check_name, check_config in checks_dict.items()
    ]


def load_metamodel_data():
    """
    Load and process metamodel.yaml.

    Returns:
        dict: A dictionary with keys:
            - 'needs_types': A list of processed need types.
            - 'needs_extra_links': A list of extra link definitions.
            - 'needs_extra_options': A sorted list of all option keys.
    """
    yaml_path = Path(__file__).resolve().parent / "metamodel.yaml"

    yaml = YAML()
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.load(f)

    # Access the custom validation block

    types_dict = data.get("needs_types", {})
    links_dict = data.get("needs_extra_links", {})
    graph_check_dict = data.get("graph_checks", {})
    global_base_options = data.get("needs_types_base_options", {})
    global_base_options_optional_opts = global_base_options.get("optional_options", {})

    # Get the stop_words and weak_words as separate lists
    proh_checks_dict = data.get("prohibited_words_checks", {})
    prohibited_words_checks = convert_checks_to_dataclass(proh_checks_dict)

    # Default options by sphinx, sphinx-needs or anything else we need to account for
    default_options_list = default_options()

    # Convert "types" from {directive_name: {...}, ...} to a list of dicts
    needs_types_list = []

    all_options = set()
    for directive_name, directive_data in types_dict.items():
        # Build up a single "needs_types" item
        one_type = {
            "directive": directive_name,
            "title": directive_data.get("title", ""),
            "prefix": directive_data.get("prefix", ""),
        }

        if "color" in directive_data:
            one_type["color"] = directive_data["color"]
        if "style" in directive_data:
            one_type["style"] = directive_data["style"]

        # Store mandatory_options and optional_options directly as a dict
        mandatory_options = directive_data.get("mandatory_options", {})
        one_type["mandatory_options"] = mandatory_options
        tags = directive_data.get("tags", [])
        one_type["tags"] = tags
        parts = directive_data.get("parts", 3)
        one_type["parts"] = parts

        optional_options = directive_data.get("optional_options", {})
        optional_options.update(global_base_options_optional_opts)
        one_type["opt_opt"] = optional_options

        all_options.update(list(mandatory_options.keys()))
        all_options.update(list(optional_options.keys()))

        # mandatory_links => "req_link"
        mand_links_yaml = directive_data.get("mandatory_links", {})
        if mand_links_yaml:
            one_type["req_link"] = [(k, v) for k, v in mand_links_yaml.items()]

        # optional_links => "opt_link"
        opt_links_yaml = directive_data.get("optional_links", {})
        if opt_links_yaml:
            one_type["opt_link"] = [(k, v) for k, v in opt_links_yaml.items()]

        needs_types_list.append(one_type)

    # Convert "links" dict -> list of {"option", "incoming", "outgoing"}
    needs_extra_links_list = []
    for link_option, link_data in links_dict.items():
        needs_extra_links_list.append(
            {
                "option": link_option,
                "incoming": link_data.get("incoming", ""),
                "outgoing": link_data.get("outgoing", ""),
            }
        )

    # We have to remove all 'default options' from the extra options.
    # As otherwise sphinx errors, due to an option being registered twice.
    # They are still inside the extra options we extract to enable
    # constraint checking via regex
    needs_extra_options = sorted(all_options - set(default_options_list))

    return {
        "prohibited_words_checks": prohibited_words_checks,
        # "weak_words": weak_words_list,
        "needs_types": needs_types_list,
        "needs_extra_links": needs_extra_links_list,
        "needs_extra_options": needs_extra_options,
        "needs_graph_check": graph_check_dict,
    }


def default_options() -> list[str]:
    """
    Helper function to get a list of all default options defined by
    sphinx, sphinx-needs etc.
    """
    return [
        "target_id",
        "id",
        "status",
        "docname",
        "lineno",
        "type",
        "lineno_content",
        "doctype",
        "content",
        "type_name",
        "type_color",
        "type_style",
        "title",
        "full_title",
        "layout",
        "template",
        "id_parent",
        "id_complete",
        "external_css",
        "sections",
        "section_name",
        "type_prefix",
        "constraints_passed",
        "collapse",
        "hide",
        "delete",
        "jinja_content",
        "is_part",
        "is_need",
        "is_external",
        "is_modified",
        "modifications",
        "has_dead_links",
        "has_forbidden_dead_links",
        "tags",
        "arch",
        "parts",
    ]


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_config_value("external_needs_source", "", rebuild="env")
    app.add_config_value("allowed_external_prefixes", [], rebuild="env")
    app.config.needs_id_required = True
    app.config.needs_id_regex = "^[A-Za-z0-9_-]{6,}"

    # load metamodel.yaml via ruamel.yaml
    metamodel = load_metamodel_data()

    # Assign everything to Sphinx config
    app.config.needs_types = metamodel["needs_types"]
    app.config.needs_extra_links = metamodel["needs_extra_links"]
    app.config.needs_extra_options = metamodel["needs_extra_options"]
    app.config.graph_checks = metamodel["needs_graph_check"]
    app.config.prohibited_words_checks = metamodel["prohibited_words_checks"]

    # app.config.stop_words = metamodel["stop_words"]
    # app.config.weak_words = metamodel["weak_words"]
    # Ensure that 'needs.json' is always build.
    app.config.needs_build_json = True
    app.config.needs_reproducible_json = True
    app.config.needs_json_remove_defaults = True

    _ = app.connect("config-inited", connect_external_needs)

    discover_checks()

    app.add_config_value(
        "score_metamodel_checks",
        "",
        rebuild="env",
        description=(
            "Comma separated list of enabled checks. When empty, all checks are enabled"
        ),
    )

    _ = app.connect("build-finished", _run_checks)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
