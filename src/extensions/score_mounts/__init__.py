# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

"""Bridge extension: translate the MOUNTS env-var supplied by docs.bzl into
``config.mounts`` consumed by ``sphinx_mounts``, and into a TOML fragment
merged into the generated ``ubproject.toml`` by ``needs_config_writer``.

Sibling of ``score_metamodel.external_needs`` — same transport (Bazel env
var of label-shaped JSON), same runfiles resolver, same TOML serializer."""

from __future__ import annotations

import os
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging

from src.extensions.score_mounts._emit import (
    hook_into_needs_config_writer,
    write_bundle_tomls,
    write_fragment,
)
from src.extensions.score_mounts._resolver import (
    label_to_bazel_bin_path,
    parse_mounts_source,
    resolve_mount_dir,
)
from src.helper_lib import find_ws_root

logger = logging.getLogger(__name__)


def _on_config_inited(app: Sphinx, config: Config) -> None:
    raw = getattr(config, "mounts_source", "") or os.environ.get("MOUNTS", "")
    specs = parse_mounts_source(raw)
    if not specs:
        return

    # Compute confdir for portable path relativisation.  find_ws_root() returns
    # None inside a Bazel sandbox (bazel build), so fall back to Path.cwd().
    ws_root = find_ws_root() or Path.cwd()
    confdir = Path(app.confdir)

    # In-memory: absolute runfile paths so sphinx-mounts can walk the
    # directory during this build.
    runtime_mounts: list[dict[str, object]] = []
    # On-disk: confdir-relative bazel-bin paths so the merged
    # ubproject.toml stays portable for IDE consumers.
    portable_mounts: list[dict[str, object]] = []

    for spec in specs:
        abs_dir = resolve_mount_dir(spec)
        if not abs_dir.is_dir():
            logger.warning(
                "score_mounts: resolved mount dir does not exist: %s (label=%s)",
                abs_dir,
                spec.label,
            )
        common = {
            "mount_at": spec.mount_at,
            "attach_to": spec.attach_to,
            "entry_doc": spec.entry_doc,
        }
        runtime_mounts.append({"dir": str(abs_dir), **common})

        # Portable path: when src_root is set the bundle has an in-repo
        # source location and the IDE should jump to those originals, not
        # to the bazel-bin copy. Without src_root (e.g. external bundles)
        # fall back to the bazel-bin path so the IDE at least sees the
        # built artifact.
        if spec.src_root:
            portable_target = ws_root / spec.src_root.lstrip("/")
        else:
            portable_target = ws_root / label_to_bazel_bin_path(spec.label)
        try:
            portable_dir = os.path.relpath(portable_target, confdir)
        except ValueError:
            # On Windows, relpath may fail across drives; fall back to
            # the workspace-root-relative form.
            portable_dir = (
                spec.src_root.lstrip("/")
                if spec.src_root
                else label_to_bazel_bin_path(spec.label)
            )
        portable_mounts.append({"dir": portable_dir, **common})

    config.mounts = runtime_mounts
    # Prevent sphinx_mounts._on_load_toml from overwriting our config with a
    # possibly-stale docs/ubproject.toml entry.
    config.mounts_from_toml = None

    fragment_path = write_fragment(portable_mounts)
    hook_into_needs_config_writer(config, fragment_path)

    logger.info("score_mounts: registered %d mount(s)", len(runtime_mounts))


def _on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    """Generate per-bundle ubproject.toml after needs_config_writer has
    written the host's ubproject.toml. Only fires when running under
    bazel run (workspace dir available). Silently skips bundles without
    src_root."""
    if exception is not None:
        return  # don't pollute a failing build

    ws_root = find_ws_root()
    if ws_root is None:
        # Sandbox build — no workspace to write into. The next
        # `bazel run //:docs_check` will regenerate.
        return

    raw = getattr(app.config, "mounts_source", "") or os.environ.get("MOUNTS", "")
    specs = parse_mounts_source(raw)
    src_roots = [
        ws_root / spec.src_root
        for spec in specs
        if spec.src_root
    ]
    if not src_roots:
        return

    host_toml = ws_root / "docs" / "ubproject.toml"
    if not host_toml.is_file():
        logger.warning(
            "score_mounts: host ubproject.toml not found at %s, "
            "skipping bundle TOML generation. Run `bazel run //:docs_check` "
            "to regenerate.",
            host_toml,
        )
        return

    try:
        written = write_bundle_tomls(host_toml, src_roots)
    except RuntimeError as exc:
        logger.warning("score_mounts: %s", exc)
        return

    for path in written:
        logger.info("score_mounts: wrote bundle TOML at %s", path)


def setup(app: Sphinx) -> dict[str, object]:
    app.add_config_value("mounts_source", default="", rebuild="env", types=(str,))
    # Priority must be < 400 so we run before sphinx_mounts._on_load_toml.
    app.connect("config-inited", _on_config_inited, priority=300)
    app.connect("build-finished", _on_build_finished, priority=900)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
