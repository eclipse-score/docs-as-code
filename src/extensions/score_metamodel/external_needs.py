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
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging
from sphinx_needs.needsfile import NeedsList

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

    if path_to_target == "" and target == "needs_json":
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


def parse_external_needs_sources_from_bazel_query() -> list[ExternalNeedsSource]:
    """
    This function detects if the Sphinx app is running without Bazel and sets the
    `external_needs_source` config value accordingly.

    When running with Bazel, we pass the `external_needs_source` config value
    from the bazel config.
    """

    logger.debug("Detected execution without Bazel. Fetching external needs config...")
    # Currently dependencies are stored in the top level BUILD file.
    # We could parse it or query bazel.
    # Parsing would be MUCH faster, but querying bazel would be more robust.
    p = subprocess.run(
        ["bazel", "query", "labels(data, //:docs)"],
        check=True,
        capture_output=True,
        text=True,
    )
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


def connect_external_needs(app: Sphinx, config: Config):
    extend_needs_json_exporter(config, ["project_url", "project_prefix"])

    bazel = app.config.external_needs_source or os.getenv("RUNFILES_DIR")

    if bazel:
        external_needs = parse_external_needs_sources_from_DATA(
            app.config.external_needs_source
        )  # pyright: ignore[reportAny]
    else:
        external_needs = parse_external_needs_sources_from_bazel_query()  # pyright: ignore[reportAny]

    for e in external_needs:
        assert not e.path_to_target  # path_to_target is always empty
        json_file = f"{e.bazel_module}+/{e.target}/_build/needs/needs.json"
        if r := os.getenv("RUNFILES_DIR"):
            logger.debug("Using runfiles to determine external needs JSON file.")
            fixed_json_file = Path(r) / json_file
        else:
            logger.debug(
                "Running outside bazel. "
                "Determining git root for external needs JSON file."
            )
            git_root = Path.cwd().resolve()
            while not (git_root / ".git").exists():
                git_root = git_root.parent
                if git_root == Path("/"):
                    sys.exit("Could not find git root.")
            logger.debug(f"Git root found: {git_root}")
            fixed_json_file = (
                git_root / "bazel-bin" / "ide_support.runfiles" / json_file
            )

        logger.debug(f"Fixed JSON file path: {json_file} -> {fixed_json_file}")
        json_file = fixed_json_file

        try:
            needs_json_data = json.loads(Path(json_file).read_text(encoding="utf-8"))  # pyright: ignore[reportAny]
        except FileNotFoundError:
            logger.error(
                f"Could not find external needs JSON file at {json_file}. "
                + "Something went terribly wrong. "
                + "Try running `bazel clean --async && rm -rf _build`."
            )
            continue

        assert isinstance(app.config.needs_external_needs, list)  # pyright: ignore[reportUnknownMemberType]
        app.config.needs_external_needs.append(  # pyright: ignore[reportUnknownMemberType]
            {
                "id_prefix": needs_json_data["project_prefix"],
                "base_url": needs_json_data["project_url"]
                + "/main",  # for now always "main"
                "json_path": json_file,
            }
        )
        # Making the prefixes uppercase here to match sphinx_needs,
        # as it does this internally too.
        assert isinstance(app.config.allowed_external_prefixes, list)  # pyright: ignore[reportAny]
        app.config.allowed_external_prefixes.append(  # pyright: ignore[reportUnknownMemberType]
            needs_json_data["project_prefix"].upper()  # pyright: ignore[reportAny]
        )
