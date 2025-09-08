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
import os
import pkgutil
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from ruamel.yaml import YAML
from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.config import NeedType
from sphinx_needs.data import NeedsInfoType, NeedsView, SphinxNeedsData

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

    # External needs: run a focused, info-only check on optional_links patterns
    # so that optional link issues from imported needs are visible but do not
    # fail builds with -W.
    # _check_external_optional_link_patterns(app, log)

    # Graph-Based checks: These warnings require a graph of all other needs to
    # be checked.

    for check in [c for c in graph_checks if is_check_enabled(c)]:
        logger.debug(f"Running graph check {check} for all needs")
        check(app, needs_all_needs, log)

    if log.has_warnings:
        logger.warning("Some needs have issues. See the log for more information.")

    if log.has_infos:
        log.flush_new_checks()
        logger.info(
            "\n\nThese next warnings are displayed as info statements for now. "
            "They will become real warnings in the future. "
            "Please fix them as soon as possible.\n"
        )
        # TODO: exit code


def _remove_prefix(word: str, prefixes: list[str]) -> str:
    for prefix in prefixes or []:
        if isinstance(word, str) and word.startswith(prefix):
            return word.removeprefix(prefix)
    return word


def _get_need_type_for_need(app: Sphinx, need: NeedsInfoType):
    need_type = None
    for nt in app.config.needs_types:
        try:
            if nt["directive"] == need["type"]:
                need_type = nt
                break
        except Exception:
            continue
    return need_type


def _validate_external_need_opt_links(
    need: NeedsInfoType,
    opt_links: dict[str, str],
    allowed_prefixes: list[str],
    log: CheckLogger,
) -> None:
    for link_field, pattern in opt_links.items():
        raw_value: str | list[str] | None = need.get(link_field, None)
        if raw_value in [None, [], ""]:
            continue

        values: list[str | Any] = (
            raw_value if isinstance(raw_value, list) else [raw_value]
        )
        for value in values:
            v: str | Any
            if isinstance(value, str):
                v = _remove_prefix(value, allowed_prefixes)
            else:
                v = value

            try:
                if not isinstance(v, str) or not re.match(pattern, v):
                    log.warning_for_option(
                        need,
                        link_field,
                        f"does not follow pattern `{pattern}`.",
                        is_new_check=True,
                    )
            except TypeError:
                log.warning_for_option(
                    need,
                    link_field,
                    f"pattern `{pattern}` is not a valid regex pattern.",
                    is_new_check=True,
                )


def _check_external_optional_link_patterns(app: Sphinx, log: CheckLogger) -> None:
    """Validate optional link patterns on external needs and log as info-only.

    Mirrors the original inline logic from ``_run_checks`` without changing behavior.
    """
    needs_external_needs = (
        SphinxNeedsData(app.env).get_needs_view().filter_is_external(True)
    )

    for need in needs_external_needs.values():
        need_type = _get_need_type_for_need(app, need)
        if not need_type:
            continue

        opt_links = dict(need_type.get("opt_link", []))
        if not opt_links:
            continue

        allowed_prefixes = app.config.allowed_external_prefixes
        _validate_external_need_opt_links(need, opt_links, allowed_prefixes, log)


def convert_checks_to_dataclass(
    checks_dict: dict[str, dict[str, Any]],
) -> list[ProhibitedWordCheck]:
    return [
        ProhibitedWordCheck(
            name=check_name,
            option_check={k: v for k, v in check_config.items() if k != "types"},
            types=check_config.get("types", []),
        )
        for check_name, check_config in checks_dict.items()
    ]


def load_metamodel_data() -> dict[str, Any]:
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
        data = cast(dict[str, Any], yaml.load(f))

    # Access the custom validation block

    types_dict = cast(dict[str, Any], data.get("needs_types", {}))
    links_dict = cast(dict[str, Any], data.get("needs_extra_links", {}))
    graph_check_dict = cast(dict[str, Any], data.get("graph_checks", {}))
    global_base_options = cast(dict[str, Any], data.get("needs_types_base_options", {}))
    global_base_options_optional_opts = cast(
        dict[str, Any], global_base_options.get("optional_options", {})
    )

    # Get the stop_words and weak_words as separate lists
    proh_checks_dict = cast(
        dict[str, dict[str, Any]], data.get("prohibited_words_checks", {})
    )
    prohibited_words_checks = convert_checks_to_dataclass(proh_checks_dict)

    # Default options by sphinx, sphinx-needs or anything else we need to account for
    default_options_list = default_options()

    # Convert "types" from {directive_name: {...}, ...} to a list of dicts
    needs_types_list = []

    all_options: set[str] = set()
    for directive_name, directive_data in types_dict.items():
        directive_name = cast(str, directive_name)
        directive_data = cast(dict[str, Any], directive_data)
        # Build up a single "needs_types" item
        one_type: dict[str, Any] = {
            "directive": directive_name,
            "title": directive_data.get("title", ""),
            "prefix": directive_data.get("prefix", ""),
        }

        if "color" in directive_data:
            one_type["color"] = directive_data["color"]
        if "style" in directive_data:
            one_type["style"] = directive_data["style"]

        # Store mandatory_options and optional_options directly as a dict
        mandatory_options = cast(
            dict[str, Any], directive_data.get("mandatory_options", {})
        )
        one_type["mandatory_options"] = mandatory_options
        tags = cast(list[str], directive_data.get("tags", []))
        one_type["tags"] = tags
        parts = cast(int, directive_data.get("parts", 3))
        one_type["parts"] = parts

        optional_options = cast(
            dict[str, Any], directive_data.get("optional_options", {})
        )
        optional_options.update(global_base_options_optional_opts)
        one_type["opt_opt"] = optional_options

        all_options.update(list(mandatory_options.keys()))
        all_options.update(list(optional_options.keys()))

        # mandatory_links => "req_link"
        mand_links_yaml = cast(
            dict[str, Any], directive_data.get("mandatory_links", {})
        )
        if mand_links_yaml:
            one_type["req_link"] = [
                (cast(str, k), cast(Any, v)) for k, v in mand_links_yaml.items()
            ]

        # optional_links => "opt_link"
        opt_links_yaml = cast(dict[str, Any], directive_data.get("optional_links", {}))
        if opt_links_yaml:
            one_type["opt_link"] = [
                (cast(str, k), cast(Any, v)) for k, v in opt_links_yaml.items()
            ]

        needs_types_list.append(one_type)

    # Convert "links" dict -> list of {"option", "incoming", "outgoing"}
    needs_extra_links_list: list[dict[str, str]] = []
    for link_option, link_data in links_dict.items():
        link_option = cast(str, link_option)
        link_data = cast(dict[str, Any], link_data)
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
    needs_extra_options: list[str] = sorted(all_options - set(default_options_list))

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
