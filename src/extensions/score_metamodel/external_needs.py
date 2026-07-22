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
import subprocess
from dataclasses import dataclass
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging
from sphinx_needs.needsfile import NeedsList

from src.helper_lib import get_runfiles_dir

logger = logging.getLogger(__name__)


@dataclass
class ExternalNeedsSource:
    bazel_module: str
    path_to_target: str
    target: str


def _parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
    if not s.startswith("@"):
        # Local need, not external needs
        return None

    if "//" not in s or ":" not in s:
        raise ValueError(
            f"Unsuported external data dependency: '{s}'. Must contain '//' & ':'"
        )
    repo_and_path, target = s.split(
        ":", 1
    )  # @score_process//:needs_json => [@score_process//, needs_json]
    repo, path_to_target = repo_and_path.split("//", 1)
    repo = repo.lstrip("@")

    # The producer's docs() macro may have used a custom `name`, in which case its targets
    # are prefixed (e.g. 'foo_needs_json', 'foo_docs_sources') instead of the default,
    # unprefixed 'needs_json' / 'docs_sources'. Match both.
    is_needs_json = target == "needs_json" or target.endswith("_needs_json")
    is_docs_sources = target == "docs_sources" or target.endswith("_docs_sources")
    if path_to_target == "" and (is_needs_json or is_docs_sources):
        return ExternalNeedsSource(
            bazel_module=repo, path_to_target=path_to_target, target=target
        )
    # Unknown data target. Probably not a needs.json file.
    return None


def parse_external_needs_sources_from_DATA(v: str) -> list[ExternalNeedsSource]:
    if v in ["[]", ""]:
        return []

    logger.debug(f"Parsing external needs sources: {v}")

    data = json.loads(v)

    res = [res for el in data if (res := _parse_bazel_external_need(el))]
    logger.debug(f"Parsed external needs sources: {res}")
    return res


def parse_external_needs_sources_from_bazel_query(
    docs_target_name: str = "docs",
) -> list[ExternalNeedsSource]:
    """
    This function detects if the Sphinx app is running without Bazel and sets the
    `external_needs_source` config value accordingly.

    When running with Bazel, we pass the `external_needs_source` config value
    from the bazel config.

    Args:
        docs_target_name: The `name` the local repo's docs() Bazel macro invocation uses
            (see docs.bzl). Defaults to "docs", the macro's own default. Repos using a
            custom name must set `docs_target_name` in their conf.py to match, so this
            queries the right local target.
    """
    try:
        logger.debug(
            "Detected execution without Bazel. Fetching external needs config..."
        )
        # Currently dependencies are stored in the top level BUILD file.
        # We could parse it or query bazel.
        # Parsing would be MUCH faster, but querying bazel would be more robust.
        p = subprocess.run(
            ["bazel", "query", f"labels(data, //:{docs_target_name})"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(
            "Bazel query failed or Bazel not found. "
            "Falling back to empty external needs. (%s)",
            e,
        )
        return []

    res = [
        res
        for line in p.stdout.splitlines()
        if line.strip()
        if (res := _parse_bazel_external_need(line))
    ]
    logger.debug(f"Parsed external needs sources: {res}")
    return res


def extend_needs_json_exporter(config: Config, params: list[str]) -> None:
    """
    This will add each param to app.config as a config value.
    Then it will overwrite the needs.json exporter to include these values.
    """

    for p in params:
        # Note: we are currently addinig these values to config after config-inited.
        # This is wrong. But good enough.
        config.add(p, default="", rebuild="env", types=(), description="")

        if not getattr(config, p):
            logger.error(
                f"Config value '{p}' is not set. "
                + "Please set it in your Sphinx config."
            )

    # Patch json exporter to include our custom fields
    # Note: yeah, NeedsList is the json exporter!
    orig_function = NeedsList._finalise  # pyright: ignore[reportPrivateUsage]

    def temp(self: NeedsList):
        for p in params:
            self.needs_list[p] = getattr(config, p)  # pyright: ignore[reportUnknownMemberType]

        orig_function(self)

    NeedsList._finalise = temp  # pyright: ignore[reportPrivateUsage]


def get_external_needs_source(
    external_needs_source: str, docs_target_name: str = "docs"
) -> list[ExternalNeedsSource]:
    if external_needs_source:
        # Path taken for all invocations via `bazel`
        external_needs = parse_external_needs_sources_from_DATA(external_needs_source)
    else:
        # This is the path taken for anything that doesn't
        # run via `bazel`  e.g. esbonio or other direct executions
        external_needs = parse_external_needs_sources_from_bazel_query(docs_target_name)  # pyright: ignore[reportAny]
    return external_needs


def add_external_needs_json(
    e: ExternalNeedsSource, config: Config, docs_target_name: str = "docs"
):
    json_file_raw = f"{e.bazel_module}+/{e.target}/_build/needs/needs.json"
    r = get_runfiles_dir(docs_target_name)
    json_file = r / json_file_raw
    logger.debug(f"External needs.json: {json_file}")
    try:
        needs_json_data = json.loads(Path(json_file).read_text(encoding="utf-8"))  # pyright: ignore[reportAny]
    except FileNotFoundError:
        logger.error(
            f"Could not find external needs JSON file at {json_file}. "
            + "Something went terribly wrong. "
            + "Try running `bazel clean --async && rm -rf _build`."
        )
        # Attempt to continue, exit code will be non-zero after a logged error anyway.
        return
    assert isinstance(config.needs_external_needs, list)  # pyright: ignore[reportUnknownMemberType]
    config.needs_external_needs.append(  # pyright: ignore[reportUnknownMemberType]
        {
            "base_url": needs_json_data["project_url"]
            + "/main",  # for now always "main"
            "json_path": json_file,
        }
    )


def add_external_docs_sources(
    e: ExternalNeedsSource, config: Config, docs_target_name: str = "docs"
):
    # Note that bazel does NOT write the files under e.target!
    # {e.bazel_module}+ matches the original git layout!
    r = get_runfiles_dir(docs_target_name)
    ide_support_name = (
        "ide_support"
        if docs_target_name == "docs"
        else docs_target_name + "_ide_support"
    )
    if f"{ide_support_name}.runfiles" in str(r):
        logger.error("Combo builds are currently only supported with Bazel.")
        return
    docs_source_path = Path(r) / f"{e.bazel_module}+"

    if "collections" not in config:
        config.collections = {}
    config.collections[e.bazel_module] = {
        "driver": "symlink",
        "source": str(docs_source_path),
        "target": e.bazel_module,
    }

    logger.info(f"Added external docs source: {docs_source_path} -> {e.bazel_module}")


def connect_external_needs(app: Sphinx, config: Config):
    extend_needs_json_exporter(config, ["project_url"])

    docs_target_name = app.config.docs_target_name
    external_needs = get_external_needs_source(
        app.config.external_needs_source, docs_target_name
    )

    # this sets the default value - required for the needs-config-writer
    # setting 'needscfg_exclude_defaults = True' to see the diff
    config.needs_external_needs = []

    for e in external_needs:
        assert not e.path_to_target  # path_to_target is always empty

        if e.target == "needs_json" or e.target.endswith("_needs_json"):
            add_external_needs_json(e, app.config, docs_target_name)
        elif e.target == "docs_sources" or e.target.endswith("_docs_sources"):
            add_external_docs_sources(e, app.config, docs_target_name)
        else:
            raise ValueError(
                f"Internal Error. Unknown external needs target: {e.target}"
            )
