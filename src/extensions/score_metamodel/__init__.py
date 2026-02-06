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
from collections.abc import Callable
from pathlib import Path

from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.data import NeedsView, SphinxNeedsData
from sphinx_needs.need_item import NeedItem

from src.extensions.score_metamodel.external_needs import connect_external_needs
from src.extensions.score_metamodel.log import CheckLogger

# Import and re-export some types and functions for easier access
from src.extensions.score_metamodel.metamodel_types import (
    ProhibitedWordCheck as ProhibitedWordCheck,
)
from src.extensions.score_metamodel.metamodel_types import (
    ScoreNeedType as ScoreNeedType,
)
from src.extensions.score_metamodel.sn_schemas import write_sn_schemas
from src.extensions.score_metamodel.yaml_parser import (
    default_options as default_options,
)
from src.extensions.score_metamodel.yaml_parser import (
    load_metamodel_data as load_metamodel_data,
)

logger = logging.get_logger(__name__)

local_check_function = Callable[[Sphinx, NeedItem, CheckLogger], None]
graph_check_function = Callable[[Sphinx, NeedsView, CheckLogger], None]

local_checks: list[local_check_function] = []
graph_checks: list[graph_check_function] = []


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
            f"Check: '{check}' is not one of the defined local or graph checks: "
            + ", ".join(all_check_names)
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

    # First of all postprocess the need links to convert
    # type names into actual need types.
    # This must be done before any checks are run.
    # And it must be done after config was hashed, otherwise
    # the config hash would include recusive linking between types.
    postprocess_need_links(app.config.needs_types)

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

    if log.warnings:
        logger.warning(
            f"{log.warnings} needs have issues. See the log for more information."
        )

    if log.infos:
        log.flush_new_checks()
        logger.info(
            f"\nThe {log.infos} warnings above are non fatal for now. "
            "They will become fatal in the future. "
            "Please fix them as soon as possible.\n"
        )


def _remove_prefix(word: str, prefixes: list[str]) -> str:
    for prefix in prefixes or []:
        if isinstance(word, str) and word.startswith(prefix):
            return word.removeprefix(prefix)
    return word


def _get_need_type_for_need(app: Sphinx, need: NeedItem) -> ScoreNeedType:
    for nt in app.config.needs_types:
        if nt["directive"] == need["type"]:
            return nt
    raise ValueError(f"Need type {need['type']} not found in needs_types")


def _resolve_linkable_types(
    link_name: str,
    link_value: str,
    current_need_type: ScoreNeedType,
    needs_types: list[ScoreNeedType],
) -> list[ScoreNeedType | str]:
    needs_types_dict = {nt["directive"]: nt for nt in needs_types}
    link_values = [v.strip() for v in link_value.split(",")]
    linkable_types: list[ScoreNeedType | str] = []
    for v in link_values:
        if v.startswith("^"):
            linkable_types.append(v)  # keep regex as-is
        else:
            target_need_type = needs_types_dict.get(v)
            if target_need_type is None:
                logger.error(
                    f"In metamodel.yaml: {current_need_type['directive']}, "
                    f"link '{link_name}' references unknown type '{v}'."
                )
            else:
                linkable_types.append(target_need_type)
    return linkable_types


def postprocess_need_links(needs_types_list: list[ScoreNeedType]):
    """Convert link option strings into lists of target need types.

    If a link value starts with '^' it is treated as a regex and left
    unchanged. Otherwise it is a comma-separated list of type names which
    are resolved to the corresponding ScoreNeedTypes.
    """
    for need_type in needs_types_list:
        try:
            link_dicts = (
                need_type["mandatory_links"],
                need_type["optional_links"],
            )
        except KeyError:
            # TODO: remove the Sphinx-Needs defaults from our metamodel
            # Example: {'directive': 'issue', 'title': 'Issue', 'prefix': 'IS_'}
            continue

        for link_dict in link_dicts:
            for link_name, link_value in link_dict.items():
                assert isinstance(link_value, str)  # so far all of them are strings

                link_dict[link_name] = _resolve_linkable_types(  # pyright: ignore[reportArgumentType]
                    link_name, link_value, need_type, needs_types_list
                )


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_config_value("external_needs_source", "", rebuild="env")
    app.config.needs_id_required = True
    app.config.needs_id_regex = "^[A-Za-z0-9_-]{6,}"

    # load metamodel.yaml via ruamel.yaml
    metamodel = load_metamodel_data()

    # Sphinx-Needs 6 requires extra options as dicts: {"name": ..., "schema": ...}
    # Options WITH a schema get JSON schema validation (value must be a string).
    # Options WITHOUT a schema are registered but not validated.
    # non_schema_options = {"source_code_link", "testlink", "codelink"}
    non_schema_options = {}  # currently empty → all options get schema validation
    extra_options_schema = [
        {"name": opt, "schema": {"type": "string"}}
        for opt in metamodel.needs_extra_options
        if opt not in non_schema_options
    ]
    extra_options_wo_schema = [
        {"name": opt}
        for opt in metamodel.needs_extra_options
        if opt in non_schema_options
    ]
    # extra_options = [{"name": opt} for opt in metamodel.needs_extra_options]
    extra_options = extra_options_schema + extra_options_wo_schema

    # Assign everything to Sphinx config
    app.config.needs_types = metamodel.needs_types
    app.config.needs_extra_links = metamodel.needs_extra_links
    app.config.needs_extra_options = extra_options
    app.config.graph_checks = metamodel.needs_graph_check
    app.config.prohibited_words_checks = metamodel.prohibited_words_checks

    # app.config.stop_words = metamodel["stop_words"]
    # app.config.weak_words = metamodel["weak_words"]
    # Ensure that 'needs.json' is always build.
    app.config.needs_build_json = True
    app.config.needs_reproducible_json = True
    app.config.needs_json_remove_defaults = True

    # Generate schemas.json from the metamodel and register it with sphinx-needs.
    # This enables sphinx-needs 6 schema validation: required fields, regex
    # patterns on option values, and (eventually) link target type checks.

    print("Trying to generate schemas from metamodel.yaml and register them with Sphinx-Needs.")

    write_sn_schemas(app, metamodel)

    print("Successfully generated schemas from metamodel.yaml and registered them with Sphinx-Needs.")

    # sphinx-collections runs on default prio 500.
    # We need to populate the sphinx-collections config before that happens.
    # --> 499
    _ = app.connect("config-inited", connect_external_needs, priority=499)

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
