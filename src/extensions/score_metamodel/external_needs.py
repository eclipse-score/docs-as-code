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
from typing import cast

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging
from sphinx_needs.logging import log_warning
from sphinx_needs.needsfile import NeedsList

from src.helper_lib import get_runfiles_dir
from src.helper_lib.external_needs import (
    ExternalNeedsSource as ExternalNeedsSource,
    external_needs_runfiles_path,
    external_needs_source_path as _external_needs_source_path,
    parse_bazel_external_need,
    parse_external_needs_labels,
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
        # Core configuration can register a value before this exporter hook
        # runs. Keep that registration (and any CLI override attached to it)
        # instead of trying to add the same Sphinx setting twice.
        if p not in config:
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
    """Get inventory labels from Bazel-provided config or query Bazel locally.

    The documented Sphinx target passes a JSON list of Bazel labels through
    ``external_needs_source``. Direct editor invocations have no such action
    environment, so they query ``//:docs`` and parse its data dependencies.
    Both paths produce the same structured sources for runfiles resolution.
    """
    if external_needs_source:
        try:
            raw_labels: object = json.loads(external_needs_source)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse external needs sources from "
                f"external_needs_source {external_needs_source}: {e}"
            )
            raise SystemExit(1) from e
        if not isinstance(raw_labels, list):
            raise ValueError(
                "External needs configuration must contain Bazel label strings."
            )
        labels: list[str] = []
        for label in cast(list[object], raw_labels):
            if not isinstance(label, str):
                raise ValueError(
                    "External needs configuration must contain Bazel label strings."
                )
            labels.append(label)
        return parse_external_needs_labels(labels)
    else:
        # This is the path taken for anything that doesn't
        # run via `bazel`  e.g. esbonio or other direct executions
        return parse_external_needs_sources_from_bazel_query()  # pyright: ignore[reportAny]


def _external_needs_base_url(
    source: ExternalNeedsSource,
    needs_json_data: dict[str, object],
) -> str:
    """Return the same canonical base URL used when registering this inventory."""
    if source.target.endswith(".__internal__.needs_local"):
        project_url = needs_json_data.get("project_url", "")
        if not isinstance(project_url, str):
            project_url = ""
        project_url = project_url.rstrip("/")
        if not project_url:
            # Standalone bundles have no published root URL, but Sphinx-Needs
            # still requires a base URL. This reserved host is never a real link.
            project_url = "https://score-needs.invalid"
        return project_url + "/main"  # for now always "main"

    if source.target == "needs_json_file":
        # Preserve the legacy file target's behavior when project_url is absent.
        project_url = needs_json_data.get("project_url", "")
    else:
        project_url = needs_json_data["project_url"]
    return cast(str, project_url) + "/main"  # for now always "main"


def _external_needs_source_label(source: ExternalNeedsSource) -> str:
    """Format the Bazel source label for a useful duplicate-ID diagnostic."""
    repository = f"@{source.bazel_module}" if source.bazel_module else ""
    return f"{repository}//{source.path_to_target}:{source.target}"


def _current_version_needs(
    needs_json_data: dict[str, object],
) -> dict[str, object] | None:
    """Return the Need inventory selected by a needs.json file's current version."""
    current_version = needs_json_data.get("current_version")
    versions = needs_json_data.get("versions")
    if not isinstance(current_version, str) or not isinstance(versions, dict):
        return None

    version_data = cast(dict[str, object], versions).get(current_version)
    if not isinstance(version_data, dict):
        return None
    needs = cast(dict[str, object], version_data).get("needs")
    if not isinstance(needs, dict):
        return None
    return cast(dict[str, object], needs)


def _read_inventory_for_duplicate_check(
    source: ExternalNeedsSource, runfiles_dir: Path
) -> tuple[str, dict[str, object]] | None:
    """Read one valid inventory's canonical URL and current Need-ID map.

    Invalid or unavailable inventory files are left to the regular Sphinx-Needs
    loader, which owns their established error messages.
    """
    json_file = _external_needs_source_path(runfiles_dir, source)
    try:
        raw_data: object = json.loads(Path(json_file).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(raw_data, dict):
        return None

    needs_json_data = cast(dict[str, object], raw_data)
    needs = _current_version_needs(needs_json_data)
    if needs is None:
        return None
    try:
        base_url = _external_needs_base_url(source, needs_json_data)
    except (KeyError, TypeError):
        return None
    return base_url, needs


def _warn_for_duplicate_external_need_ids(
    sources: list[ExternalNeedsSource], runfiles_dir: Path
) -> None:
    """Warn about same-URL ID collisions before Sphinx-Needs replaces a source.

    Sphinx-Needs uses ``base_url`` to decide whether an external need was loaded
    from the same inventory before checking for duplicate IDs. If two inventories
    share a base URL, it removes the earlier record as a reload and never reaches
    its normal duplicate-ID warning. Compare those inventories first so the
    collision remains visible while their links keep the real project URL.
    """
    first_source_by_base_url_and_id: dict[tuple[str, str], str] = {}
    for source in sources:
        inventory = _read_inventory_for_duplicate_check(source, runfiles_dir)
        if inventory is None:
            continue
        base_url, needs = inventory

        source_label = _external_needs_source_label(source)
        for need_id in needs:
            key = (base_url, need_id)
            if key not in first_source_by_base_url_and_id:
                first_source_by_base_url_and_id[key] = source_label
                continue

            first_source = first_source_by_base_url_and_id[key]
            log_warning(
                logger,
                f"External need ID {need_id!r} is present in both {first_source} "
                f"and {source_label}. Both inventories use base URL {base_url!r}, "
                "so Sphinx-Needs would otherwise replace the earlier need without "
                "reporting the duplicate.",
                "load_external_need",
                location=None,
            )


def add_external_needs_json(
    e: ExternalNeedsSource,
    config: Config,
    runfiles_dir: Path | None,
):
    """Register a Bazel-produced JSON inventory with Sphinx-Needs.

    Public ``needs_json`` inventories and private bundle exports both keep
    their canonical project URL so imported links resolve to the published site.
    """
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
    base_url = _external_needs_base_url(
        e,
        cast(dict[str, object], needs_json_data),
    )
    config.needs_external_needs.append(  # pyright: ignore[reportUnknownMemberType]
        {"base_url": base_url, "json_path": json_file}
    )


def connect_external_needs(app: Sphinx, config: Config):
    """Connect Bazel inventory labels to Sphinx-Needs' external source list."""
    # Export each bundle's resolved project URL. The Bazel bundle provider
    # supplies the package-relative value, so inventories from different
    # bundles retain stable links to their own documentation roots.
    bundle_export = bool(config.score_bundle_needs_export)
    # Internal bundle exports can be built without a root docs configuration,
    # which means project_url may legitimately be empty. Public needs_json
    # exports retain the existing required-project-URL diagnostic.
    extend_needs_json_exporter(
        config,
        ["project_url"],
        log_missing=not bundle_export,
    )

    # The CLI transports Bazel labels rather than filesystem paths. Resolve
    # each label against runfiles here, where both the repository name and the
    # package/target layout are available.
    external_needs = get_external_needs_source(app.config.external_needs_source)

    # this sets the default value - required for the needs-config-writer
    # setting 'needscfg_exclude_defaults = True' to see the diff
    config.needs_external_needs = []

    if external_needs:
        runfiles_dir = _runfiles_dir(app.config)
        # Sphinx-Needs silently replaces an earlier record when the same Need
        # ID arrives from an inventory with the same base URL. Check inventory
        # keys before registering sources so this collision is reported while
        # keeping base_url available for constructing correct published links.
        _warn_for_duplicate_external_need_ids(external_needs, runfiles_dir)
        for e in external_needs:
            if e.target == "needs_json":
                # Keep the public project inventory's established URL scheme.
                add_external_needs_json(e, app.config, runfiles_dir)
            elif e.target == "needs_json_file":
                _add_needs_json_file(e, app.config, runfiles_dir)
            elif e.target.endswith(".__internal__.needs_local"):
                # Private bundle exports are validation context for another
                # bundle. Keep their canonical URL for imported links; the
                # preflight above reports duplicate IDs hidden by shared URLs.
                add_external_needs_json(e, app.config, runfiles_dir)
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
            "base_url": _external_needs_base_url(ext_needs, needs_json_data),
            "json_path": json_file,
        }
    )
