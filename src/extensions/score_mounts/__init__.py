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
    resolve_walk_dir,
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


def _resolve_data_mounts(
    manifest: MountsManifest,
    ws_root: Path | None,
    runfiles_dir: Path | None,
) -> dict[str, MountSpec]:
    """Resolve data file mounts from the manifest.

    Data paths are execroot-relative (e.g. bazel-out/.../bin/src/.../index.rst).
    Returns resolved mount dicts keyed by directory.
    """
    data_mounts: dict[str, MountSpec] = {}
    for spec in manifest.mounts:
        for data_file in spec.data:
            if ws_root is not None and runfiles_dir is not None:
                runfiles_str = str(runfiles_dir)
                if "/bazel-out/" in runfiles_str:
                    # Execroot = runfiles path before the first /bazel-out/ occurrence
                    # e.g. runfiles=execroot/_main/bazel-out/... => execroot=execroot/_main
                    walk_file = Path(runfiles_str.split("/bazel-out/")[0]) / data_file
                else:
                    walk_file = (
                        ws_root
                        / "bazel-bin"
                        / data_file.removeprefix("bazel-out/k8-fastbuild/bin/")
                    )
            else:
                walk_file = Path.cwd() / data_file
            if not walk_file.is_file():
                raise ValueError(
                    "score_mounts: resolved data file does not exist: "
                    f"{walk_file} (mount_at={spec.mount_at})"
                )
            walk_dir = walk_file.parent
            if str(walk_dir) not in data_mounts:
                data_mounts[str(walk_dir)] = spec
    return data_mounts


def _canonical_mount_dir(walk_dir: Path, spec: MountSpec) -> Path:
    """Resolve a mount root through Bazel's sandboxed symlinks.

    ``sphinx-mounts`` checks whether assets referenced by a mounted document
    stay below the mount root. It resolves both paths before comparing them.
    That is normally exactly what we want, but Bazel can give the mount root
    and the files below it different physical spellings in a sandbox:

    - for external repositories, the repository directory exists in the action
      sandbox, for example
      ``.../sandbox/.../execroot/_main/external/score_process_description+/process``;
      files inside that directory can be symlinks to Bazel's repository
      cache, for example
      ``~/.cache/bazel/.../external/score_process_description+/process/index.rst``.
    - for generated data bundles, the mount root may be the sandbox copy of a
      ``bazel-out`` directory, for example
      ``.../sandbox/.../execroot/_main/bazel-out/.../docs/generated``;
      generated files below it can resolve to the action execroot spelling,
      for example
      ``~/.cache/bazel/.../execroot/_main/bazel-out/.../docs/generated/index.rst``.

    Resolving only ``walk_dir`` therefore keeps the sandbox spelling, while
    resolving a referenced image/include from Sphinx follows the file symlink.
    The paths then look unrelated even though they describe the same Bazel
    bundle.

    To make the confinement check compare like with like, resolve one mounted
    source file first and then walk back by its bundle-relative suffix. Example:

    ``walk_dir``:
      ``.../sandbox/.../external/score_process_description+/process``
    ``source_file``:
      ``.../sandbox/.../external/score_process_description+/process/index.rst``
    ``source_file.resolve()``:
      ``~/.cache/bazel/.../external/score_process_description+/process/index.rst``

    Since ``index.rst`` is one path component below ``walk_dir``, its parent is
    the canonical mount root. For ``subdir/page.rst`` we walk back two
    components, yielding the same canonical root.
    """
    if not spec.external and not spec.data:
        return walk_dir.resolve()

    # Bazel materializes the mount directory structure in the sandbox but may
    # symlink the individual files either to the external repository cache or to
    # the action execroot's bazel-out tree. A mounted documentation source gives
    # us the same canonical spelling that Sphinx will later see for dependency
    # files. Walking back by the source file's path relative to the mount
    # reconstructs the canonical mount root:
    #
    #   source_file = walk_dir / "subdir/page.rst"
    #   relative_path.parts = ("subdir", "page.rst")
    #   source_file.resolve().parents[1] == canonical walk_dir
    for source_file in walk_dir.rglob("*"):
        if not source_file.is_file() or source_file.suffix not in {".md", ".rst"}:
            continue
        relative_path = source_file.relative_to(walk_dir)
        return source_file.resolve().parents[len(relative_path.parts) - 1]
    return walk_dir.resolve()


def _make_mount_entry(walk_dir: Path, spec: MountSpec) -> dict[str, object]:
    """Build a mount entry dict from a canonical directory and spec."""
    return {
        "dir": str(_canonical_mount_dir(walk_dir, spec)),
        "mount_at": spec.mount_at,
        "attach_to": spec.attach_to,
        "entry_doc": spec.entry_doc,
    }


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

    ws_root = find_ws_root()
    runfiles_dir = get_runfiles_dir() if ws_root is not None else None

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

    # Pure-data bundles have empty src_root; skip directory walk.
    runtime_mounts: list[dict[str, object]] = []
    for spec in manifest.mounts:
        if not spec.src_root:
            continue
        walk_dir = resolve_walk_dir(manifest, spec, ws_root, runfiles_dir)
        if not walk_dir.is_dir():
            raise ValueError(
                "score_mounts: resolved mount dir does not exist: "
                f"{walk_dir} (mount_at={spec.mount_at})"
            )
        runtime_mounts.append(_make_mount_entry(walk_dir, spec))

    config.mounts = runtime_mounts

    # Resolve data (e.g. genrule outputs in bazel-out).
    # Data paths are execroot-relative (e.g. bazel-out/.../bin/src/.../index.rst).
    # During bazel run: compute execroot from RUNFILES_DIR; during sandboxed build:
    # cwd IS the execroot.
    # Only the parent directories of resolved files are added to mounts.
    data_mounts = _resolve_data_mounts(manifest, ws_root, runfiles_dir)
    for walk_dir_str, spec in data_mounts.items():
        config.mounts.append(_make_mount_entry(Path(walk_dir_str), spec))
    logger.info("score_mounts: added %d data mount(s)", len(data_mounts))

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
