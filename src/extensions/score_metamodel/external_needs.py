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
    """Return the base URL passed to Sphinx-Needs for this inventory."""
    if source.target == "needs_json":
        # A `needs_json` producer always exports its project URL.
        project_url = cast(str, needs_json_data["project_url"])
    elif source.target == "needs_json_file":
        # A standalone inventory file may not have a project URL.
        project_url = cast(str, needs_json_data.get("project_url", ""))
    elif source.target.endswith(".__internal__.needs_local"):
        # A standalone docs_bundle may not have a published project URL. Sphinx-Needs
        # still requires a base URL to load its Needs as external context, so use a
        # reserved host when the exported value is absent or empty. Root-associated
        # bundles use their exported project URL here.
        project_url = cast(str, needs_json_data.get("project_url", ""))
        project_url = project_url.rstrip("/") or "https://score-needs.invalid"
    else:
        raise ValueError(f"Unsupported external needs target: {source.target}")

    # Keep the same URL construction as the regular loaders. Sphinx-Needs uses
    # this URL when deciding whether an external Need should be replaced.
    return project_url + "/main"  # for now always "main"


def _external_needs_source_label(source: ExternalNeedsSource) -> str:
    """Format a Bazel label for duplicate-ID warnings."""
    repository = f"@{source.bazel_module}" if source.bazel_module else ""
    return f"{repository}//{source.path_to_target}:{source.target}"


def _read_need_json_identities(
    source: ExternalNeedsSource,
    runfiles_dir: Path,
) -> list[tuple[str, str]]:
    """Read each current-version Need's (base URL, ID) identity pair.

    The Sphinx-Needs build creates these inventories, so this preflight follows
    its generated JSON structure instead of trying to validate the full file.
    Unreadable JSON is left to the normal loader. If readable JSON has an
    unexpected shape, warn and let that loader report the format error.
    """
    json_file = _external_needs_source_path(runfiles_dir, source)
    try:
        raw_data: object = json.loads(Path(json_file).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    try:
        needs_json_data = cast(dict[str, object], raw_data)
        current_version = cast(str, needs_json_data["current_version"])
        versions = cast(dict[str, object], needs_json_data["versions"])
        version = cast(dict[str, object], versions[current_version])
        needs = cast(dict[str, object], version["needs"])
        base_url = _external_needs_base_url(source, needs_json_data)
        need_identities: list[tuple[str, str]] = []
        for need_data in needs.values():
            need_id = cast(dict[str, object], need_data)["id"]
            if not isinstance(need_id, str):
                raise TypeError("Need ID must be a string")
            need_identities.append((base_url, need_id))
    except (AttributeError, KeyError, TypeError):
        source_label = _external_needs_source_label(source)
        log_warning(
            logger,
            f"Could not inspect external Needs inventory {source_label} for duplicate IDs "
            "because its JSON does not match the generated needs.json structure. "
            "The duplicate-ID preflight was skipped; the regular external-Needs "
            "loader will handle the file.",
            "load_external_need",
            location=None,
        )
        return []

    return need_identities


# Work around https://github.com/useblocks/sphinx-needs/issues/2003: importing
# separate inventories with the same base URL can silently replace duplicate IDs.
def _warn_for_duplicate_external_need_ids(
    sources: list[ExternalNeedsSource],
    runfiles_dir: Path,
) -> None:
    """Warn before same-URL inventories can silently replace matching Needs.

    Sphinx-Needs checks whether the new source's base URL appears in an
    existing external Need's URL. Shared base URLs satisfy that check, so
    Sphinx-Needs deletes the earlier Need before its normal duplicate-ID
    check. Scan the source files first to report the overlap before replacement.
    """
    first_source_by_base_url_and_id: dict[tuple[str, str], str] = {}
    for source in sources:
        need_identities = _read_need_json_identities(source, runfiles_dir)
        if not need_identities:
            continue
        source_label = _external_needs_source_label(source)

        for base_url, need_id in need_identities:
            key = (base_url, need_id)
            if key not in first_source_by_base_url_and_id:
                first_source_by_base_url_and_id[key] = source_label
                continue

            first_source = first_source_by_base_url_and_id[key]
            log_warning(
                logger,
                f"External need ID {need_id!r} is present in both {first_source} "
                f"and {source_label}. Both inventories use base URL {base_url!r}, "
                "so Sphinx-Needs would otherwise replace the earlier need "
                "without reporting the duplicate. To fix this, give one of "
                "the Needs a different ID.",
                "load_external_need",
                location=None,
            )


def add_external_needs_json(
    e: ExternalNeedsSource, config: Config, runfiles_dir: Path | None
):
    json_file = _external_needs_source_path(runfiles_dir, e)
    logger.debug(f"External needs.json: {json_file}")
    try:
        needs_json_data = cast(
            dict[str, object],
            json.loads(Path(json_file).read_text(encoding="utf-8")),
        )
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
            "base_url": _external_needs_base_url(
                e,
                needs_json_data,
            ),
            "json_path": json_file,
        }
    )


def _add_bundle_local_needs_json(
    e: ExternalNeedsSource, config: Config, runfiles_dir: Path | None
) -> None:
    """Load a private bundle-local inventory and register it as external context."""
    json_file = _external_needs_source_path(runfiles_dir, e)
    logger.debug(f"External local Needs JSON: {json_file}")
    try:
        needs_json_data = cast(
            dict[str, object],
            json.loads(Path(json_file).read_text(encoding="utf-8")),
        )
    except FileNotFoundError:
        logger.error(
            "Could not find external needs JSON file at %s from target %s.",
            json_file,
            e.target,
        )
        return

    assert isinstance(config.needs_external_needs, list)  # pyright: ignore[reportUnknownMemberType]
    config.needs_external_needs.append(  # pyright: ignore[reportUnknownMemberType]
        {
            "base_url": _external_needs_base_url(e, needs_json_data),
            "json_path": json_file,
        }
    )


def connect_external_needs(app: Sphinx, config: Config):
    # Export each bundle's resolved project URL. The Bazel bundle provider
    # supplies the package-relative value, so inventories from different
    # bundles retain stable links to their own documentation roots.
    bundle_export = bool(config.score_bundle_needs_export)
    extend_needs_json_exporter(
        config,
        ["project_url"],
        log_missing=not bundle_export,
    )

    # External needs labels supplied by the documentation CLI.
    external_needs = get_external_needs_source(app.config.external_needs_source)

    # this sets the default value - required for the needs-config-writer
    # setting 'needscfg_exclude_defaults = True' to see the diff
    config.needs_external_needs = []

    if external_needs:
        runfiles_dir = _runfiles_dir(app.config)
        # Inspect the files before registering them: Sphinx-Needs may replace
        # matching Needs as it loads a later source with the same base URL.
        _warn_for_duplicate_external_need_ids(external_needs, runfiles_dir)
        for e in external_needs:
            if e.target == "needs_json":
                add_external_needs_json(e, app.config, runfiles_dir)
            elif e.target == "needs_json_file":
                _add_needs_json_file(e, app.config, runfiles_dir)
            elif e.target.endswith(".__internal__.needs_local"):
                # The Bazel macro resolved a public docs target to its local
                # owner inventory. Load it as external context so links resolve
                # without copying those Needs into this project's own export.
                _add_bundle_local_needs_json(e, app.config, runfiles_dir)
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
        needs_json_data = cast(
            dict[str, object],
            json.loads(
                Path(json_file).read_text(encoding="utf-8")  # pyright: ignore[reportAny]
            ),
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
            "base_url": _external_needs_base_url(
                ext_needs,
                needs_json_data,
            ),
            "json_path": json_file,
        }
    )
