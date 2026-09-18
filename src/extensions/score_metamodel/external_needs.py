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
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging
from sphinx_needs.needsfile import NeedsList

from src.helper_lib import get_runfiles_dir
from src.helper_lib.external_needs import (
    ExternalNeedsSource as ExternalNeedsSource,
    external_needs_runfiles_path,
    external_needs_source_path as _external_needs_source_path,
    parse_bazel_external_need,
    parse_external_needs_source_config as _parse_external_needs_source_config,
)

logger = logging.getLogger(__name__)

_external_needs_runfiles_path = external_needs_runfiles_path
_parse_bazel_external_need = parse_bazel_external_need


def _runfiles_dir(config: Config) -> Path:
    """Use the CLI-provided runfiles root, with a direct-invocation fallback."""
    raw = getattr(config, "runfiles_dir", "")
    if isinstance(raw, str) and raw.strip():
        return Path(raw)
    return get_runfiles_dir()


def parse_external_needs_sources_from_bazel_query() -> list[ExternalNeedsSource]:
    """
    This function detects if the Sphinx app is running without Bazel and sets the
    `external_needs_source` config value accordingly.

    When running with Bazel, we pass the `external_needs_source` config value
    from the bazel config.
    """
    try:
        logger.debug(
            "Detected execution without Bazel. Fetching external needs config..."
        )
        # Currently dependencies are stored in the top level BUILD file.
        # We could parse it or query bazel.
        # Parsing would be MUCH faster, but querying bazel would be more robust.
        p = subprocess.run(
            ["bazel", "query", "labels(data, //:docs)"],
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


def extend_needs_json_exporter(
    config: Config,
    params: list[str],
    *,
    log_missing: bool = True,
    export_values: dict[str, str] | None = None,
) -> None:
    """
    This will add each param to app.config as a config value.
    Then it will overwrite the needs.json exporter to include these values.
    """

    for p in params:
        # Note: we are currently addinig these values to config after config-inited.
        # This is wrong. But good enough.
        config.add(p, default="", rebuild="env", types=(), description="")

        if log_missing and not getattr(config, p):
            logger.error(
                f"Config value '{p}' is not set. "
                + "Please set it in your Sphinx config."
            )

    # Patch json exporter to include our custom fields
    # Note: yeah, NeedsList is the json exporter!
    orig_function = NeedsList._finalise  # pyright: ignore[reportPrivateUsage]

    def temp(self: NeedsList):
        for p in params:
            if export_values is not None and p in export_values:
                self.needs_list[p] = export_values[p]
            else:
                self.needs_list[p] = getattr(config, p)  # pyright: ignore[reportUnknownMemberType]

        orig_function(self)

    NeedsList._finalise = temp  # pyright: ignore[reportPrivateUsage]


def get_external_needs_source(external_needs_source: str) -> list[ExternalNeedsSource]:
    if external_needs_source:
        # The CLI supplies resolved descriptors for Bazel invocations.
        try:
            return _parse_external_needs_source_config(external_needs_source)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse external needs sources from "
                f"external_needs_source {external_needs_source}: {e}"
            )
            raise SystemExit(1) from e
    else:
        # This is the path taken for anything that doesn't
        # run via `bazel`  e.g. esbonio or other direct executions
        return parse_external_needs_sources_from_bazel_query()  # pyright: ignore[reportAny]


def add_external_needs_json(
    e: ExternalNeedsSource, config: Config, runfiles_dir: Path | None
):
    json_file = _external_needs_source_path(runfiles_dir, e)
    logger.debug(f"External needs.json: {json_file}")
    try:
        needs_json_data = json.loads(Path(json_file).read_text(encoding="utf-8"))  # pyright: ignore[reportAny]
    except FileNotFoundError:
        logger.error(
            "Could not find external needs JSON file at %s from target %s.",
            json_file,
            e.target,
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
    e: ExternalNeedsSource, config: Config, runfiles_dir: Path | None
):
    # Note that bazel does NOT write the files under e.target!
    # The runfiles layout mirrors the original git layout: same-repo mounts live
    # under `_main/…`, cross-module mounts under `{e.bazel_module}+/…`
    # (see _runfiles_module_dir).
    docs_source_path = _external_needs_source_path(runfiles_dir, e)

    # A cross-module root mount keeps its module name as the collection key
    # (unchanged). Sub-package / same-repo mounts disambiguate via the path.
    key = "/".join(c for c in (e.bazel_module, e.path_to_target) if c) or "_main"

    if "collections" not in config:
        config.collections = {}
    config.collections[key] = {
        "driver": "symlink",
        "source": str(docs_source_path),
        "target": key,
    }

    logger.info(f"Added external docs source: {docs_source_path} -> {key}")


def connect_external_needs(app: Sphinx, config: Config):
    # Local bundle exports intentionally omit the host URL from their JSON so
    # the inventory remains reusable by whichever documentation site consumes
    # it. Keep the configuration value available to Sphinx itself, and retain
    # the existing missing-value diagnostic for normal host builds.
    bundle_export = bool(config.score_bundle_needs_export)
    extend_needs_json_exporter(
        config,
        ["project_url"],
        log_missing=not bundle_export,
        export_values={"project_url": ""} if bundle_export else None,
    )

    # External needs descriptors supplied by the documentation CLI.
    external_needs = get_external_needs_source(app.config.external_needs_source)

    # this sets the default value - required for the needs-config-writer
    # setting 'needscfg_exclude_defaults = True' to see the diff
    config.needs_external_needs = []

    if external_needs:
        runfiles_dir = (
            _runfiles_dir(app.config)
            if any(source.resolved_path is None for source in external_needs)
            else None
        )
        for e in external_needs:
            if e.target == "needs_json":
                add_external_needs_json(e, app.config, runfiles_dir)
            elif e.target == "needs_json_file":
                _add_needs_json_file(e, app.config, runfiles_dir)
            elif e.target == "docs_sources":
                add_external_docs_sources(e, app.config, runfiles_dir)
            else:
                raise ValueError(
                    f"Internal Error. Unknown external needs target: {e.target}"
                )


def _add_needs_json_file(
    ext_needs: ExternalNeedsSource, config: Config, runfiles_dir: Path | None
) -> None:
    """Resolve a needs_json_file target from runfiles and register it."""
    json_file = _external_needs_source_path(runfiles_dir, ext_needs)
    logger.debug(f"External needs_json_file: {json_file}")
    try:
        needs_json_data = json.loads(
            Path(json_file).read_text(encoding="utf-8")  # pyright: ignore[reportAny]
        )
    except FileNotFoundError:
        logger.error(
            "Could not find external needs JSON file at %s from target %s.",
            json_file,
            ext_needs.target,
        )
        return
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse external needs JSON file {json_file}: {exc}")
        return
    config.needs_external_needs.append(
        {  # pyright: ignore[reportUnknownMemberType]
            "base_url": needs_json_data.get("project_url", "") + "/main",
            "json_path": json_file,
        }
    )
