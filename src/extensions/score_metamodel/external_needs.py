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
    # True for a same-repo mount (`//pkg:needs_json`), whose runfiles live under
    # `_main/…`. False for a cross-module mount (`@repo//…:needs_json`), whose
    # runfiles live under `{bazel_module}+/…`.
    is_local: bool = False


def _parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
    is_cross_module = s.startswith("@")
    is_local = s.startswith("//")
    if not is_cross_module and not is_local:
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
    repo = repo.lstrip("@")  # empty for same-repo `//pkg:needs_json`

    if target in ("needs_json", "needs_json_file", "docs_sources") or target.endswith(
        "_needs_upward"
    ):
        return ExternalNeedsSource(
            bazel_module=repo,
            path_to_target=path_to_target,
            target=target,
            is_local=is_local,
        )
    # Unknown data target. Probably not a needs.json file.
    return None


def _runfiles_module_dir(e: ExternalNeedsSource) -> str:
    """Runfiles top-level directory holding this source's package tree.

    Same-repo mounts are staged under `_main/…`; cross-module mounts under the
    module's bzlmod canonical name `{bazel_module}+/…`.
    """
    return "_main" if e.is_local else f"{e.bazel_module}+"


def parse_external_needs_sources_from_DATA(v: str) -> list[ExternalNeedsSource]:
    if v in ["[]", ""]:
        return []

    logger.debug(f"Parsing external needs sources: {v}")

    try:
        data = json.loads(v)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse external needs sources from DATA {v}: {e}")
        raise SystemExit(1) from e

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


def extend_needs_json_exporter(config: Config, params: list[str]) -> None:
    """
    This will add each param to app.config as a config value.
    Then it will overwrite the needs.json exporter to include these values.
    """

    for p in params:
        # Most callers register values during extension setup, before Sphinx
        # reads conf.py.  Keep this helper usable for callers that do not, but
        # do not try to register an already-known value at config-inited.
        if not hasattr(config, p):
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


def _external_needs_base_url(config: Config, needs_json_data: dict[str, object]) -> str:
    """Return the consuming documentation project's base URL for imported Needs."""
    consumer_project_url = getattr(config, "project_url", "")
    project_url = consumer_project_url or needs_json_data.get("project_url", "")
    if not isinstance(project_url, str) or not project_url:
        return ""
    return project_url.rstrip("/") + "/main"


def get_external_needs_source(external_needs_source: str) -> list[ExternalNeedsSource]:
    if external_needs_source:
        # Path taken for all invocations via `bazel`
        return parse_external_needs_sources_from_DATA(external_needs_source)
    else:
        # This is the path taken for anything that doesn't
        # run via `bazel`  e.g. esbonio or other direct executions
        return parse_external_needs_sources_from_bazel_query()  # pyright: ignore[reportAny]


def add_external_needs_json(e: ExternalNeedsSource, config: Config):
    json_file_raw = (
        Path(_runfiles_module_dir(e))
        / e.path_to_target
        / e.target
        / "_build/needs/needs.json"
    )

    r = get_runfiles_dir()
    json_file = r / json_file_raw
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
            "base_url": _external_needs_base_url(config, needs_json_data),
            "json_path": json_file,
        }
    )


def add_external_docs_sources(e: ExternalNeedsSource, config: Config):
    # Note that bazel does NOT write the files under e.target!
    # The runfiles layout mirrors the original git layout: same-repo mounts live
    # under `_main/…`, cross-module mounts under `{e.bazel_module}+/…`
    # (see _runfiles_module_dir).
    r = get_runfiles_dir()
    if "ide_support.runfiles" in str(r):
        logger.error("Combo builds are currently only supported with Bazel.")
        return
    docs_source_path = Path(r) / _runfiles_module_dir(e) / e.path_to_target

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
    # A host docs() config owns the canonical URL. Bundle-local Needs exports
    # do not need to carry one because they can be imported by different hosts.
    if getattr(config, "project_url", ""):
        extend_needs_json_exporter(config, ["project_url"])

    # Local external needs from DATA (e.g. :needs_json or :docs_sources)
    external_needs = get_external_needs_source(app.config.external_needs_source)

    # this sets the default value - required for the needs-config-writer
    # setting 'needscfg_exclude_defaults = True' to see the diff
    config.needs_external_needs = []

    for e in external_needs:
        if e.target == "needs_json":
            add_external_needs_json(e, app.config)
        elif e.target == "needs_json_file" or e.target.endswith("_needs_upward"):
            _add_needs_json_file(e, app.config)
        elif e.target == "docs_sources":
            add_external_docs_sources(e, app.config)
        else:
            raise ValueError(
                f"Internal Error. Unknown external needs target: {e.target}"
            )


def _add_needs_json_file(ext_needs: ExternalNeedsSource, config: Config) -> None:
    """Resolve a needs export target from runfiles and register it."""
    r = get_runfiles_dir()
    module_dir = Path(_runfiles_module_dir(ext_needs))
    json_file_candidates = [
        r / module_dir / ext_needs.path_to_target / "needs.json",
    ]
    # Named docs_bundle exports use a target-specific output directory because one
    # Bazel package may contain several bundles. Keep the historical flat path
    # above for normal needs_json_file targets and try the namespaced layout
    # used by bundle-local exports as a fallback.
    if ext_needs.target != "needs_json_file":
        json_file_candidates.append(
            r / module_dir / ext_needs.path_to_target / ext_needs.target / "needs.json"
        )

    json_file = next(
        (candidate for candidate in json_file_candidates if candidate.is_file()),
        json_file_candidates[0],
    )
    logger.debug(f"External needs_json_file: {json_file}")
    try:
        needs_json_data = json.loads(
            json_file.read_text(encoding="utf-8")  # pyright: ignore[reportAny]
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
            "base_url": _external_needs_base_url(config, needs_json_data),
            "json_path": json_file,
        }
    )
