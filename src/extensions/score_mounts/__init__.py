# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

"""
Bridge extension: consume the mounts manifest authored by Bazel rules and feed it to
``sphinx_mounts``.

All mount paths originate from Bazel; this extension performs no path computation. It:

* sets ``config.mounts`` so ``sphinx_mounts`` can build the documentation;
``score_sync_toml`` reads the resulting ``config.mounts`` directly to write the
generated ``ubproject.toml``.
"""

from __future__ import annotations

import os
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging

from src.extensions.score_mounts._resolver import (
    MountsManifest,
    MountSpec,
    load_mounts_manifest,
)
from src.helper_lib import find_ws_root, get_runfiles_dir

logger = logging.getLogger(__name__)


def _read_manifest(config: Config):
    """Locate and load the mounts manifest, or return ``None`` when unset.

    The manifest path is passed by Bazel either via the ``mounts_manifest`` config
    value or the ``MOUNTS`` env var. Its interpretation depends on the build
    context: under ``bazel run`` it is a runfiles-relative path
    (``$(rlocationpath)``) resolved against the runfiles dir; in a sandbox build
    it is relative to the exec root (``$(location)``). Resolving the path here
    keeps that context branch out of the pure ``_resolver`` module.
    """
    raw = getattr(config, "mounts_manifest", None) or os.environ.get(
        "MOUNTS_MANIFEST", None
    )
    if not raw or not raw.strip() or not isinstance(raw, str):
        return None

    # ``bazel run`` passes an rlocation-relative path; ``sphinx_docs`` in a
    # sandbox passes its execroot-relative ``$(location)`` path directly.
    manifest_path = get_runfiles_dir() / raw if find_ws_root() else Path(raw)

    return load_mounts_manifest(manifest_path)


def _resolve_walk_dir(
    manifest: MountsManifest, spec: MountSpec, ws_root: Path | None
) -> Path:
    """Resolve one mount consistently for runfiles and sandboxed builds."""
    if spec.external and ws_root is not None:
        return manifest.runtime_dir(spec)
    if ws_root is not None:
        return ws_root / spec.src_root
    return Path(os.path.abspath(spec.src_root))


def _on_config_inited(app: Sphinx, config: Config) -> None:
    """Translate the Bazel manifest into ``sphinx_mounts`` runtime config.

    Runs on Sphinx's ``config-inited`` event (before ``sphinx_mounts``, see the
    priority in ``setup``). For each mount it resolves the directory
    ``sphinx_mounts`` should walk and writes the assembled list to
    ``config.mounts``. A missing or empty manifest is a no-op.
    """
    manifest = _read_manifest(config)
    if manifest is None or not manifest.mounts:
        return

    # In every context sphinx_mounts walks the bundle's original files (no copy is
    # made); only where those files are staged differs:
    #   * external bundle: use its runfiles-relative location under ``bazel run``
    #     and its execroot-relative location in a sandboxed Bazel build.
    #   * in-tree bundle under `bazel run`: use the live workspace source
    #     (ws_root/src_root) -- editable, best for live preview / jump-to-def.
    #   * in-tree bundle in a sandbox build: the bundle's source files are staged
    #     as inputs at their exec-root-relative path. The manifest lives under
    #     bazel-out/ and is NOT colocated with them, so src_root is resolved
    #     against the exec root (the sphinx action's cwd), not the manifest.
    ws_root = find_ws_root()

    runtime_mounts: list[dict[str, object]] = []
    for spec in manifest.mounts:
        walk_dir = _resolve_walk_dir(manifest, spec, ws_root)
        if not walk_dir.is_dir():
            raise ValueError(
                "score_mounts: resolved mount dir does not exist: "
                f"{walk_dir} (mount_at={spec.mount_at})"
            )

        runtime_mounts.append(
            {
                "dir": str(walk_dir),
                "mount_at": spec.mount_at,
                "attach_to": spec.attach_to,
                "entry_doc": spec.entry_doc,
            }
        )

    config.mounts = runtime_mounts
    # Prevent sphinx_mounts._on_load_toml from overwriting our config with a
    # possibly-stale docs/ubproject.toml entry.
    config.mounts_from_toml = None

    logger.info("score_mounts: registered %d mount(s)", len(runtime_mounts))


def setup(app: Sphinx) -> dict[str, object]:
    """Sphinx extension entry point: register the config value and event hook.

    ``mounts_manifest`` carries the Bazel-resolved manifest path. The
    ``config-inited`` handler is connected at priority 300 (< 400) so it runs
    before ``sphinx_mounts._on_load_toml`` and can override the mount config the
    latter would otherwise load from ``ubproject.toml``.
    """
    app.add_config_value("mounts_manifest", default="", rebuild="env", types=(str,))
    app.connect("config-inited", _on_config_inited, priority=300)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
