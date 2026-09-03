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

All mount roots originate from Bazel; this extension resolves them for the
active execution context and derives structural directory exclusions. It:

* sets ``config.mounts`` so ``sphinx_mounts`` can build the documentation;
``score_sync_toml`` reads the resulting ``config.mounts`` directly to write the
generated ``ubproject.toml``.

For directory mounts, the source-ownership invariant is that every document is
discovered exactly once: the primary Sphinx source tree owns files outside mounted
roots, and a directory mount owns its root except for nested directory mounts. The
exclusions below encode those boundaries as directory patterns so the ownership
remains correct when files are added later. Explicit file-list mounts remain in
file-list mode; they are intended for generated sources outside the primary source
tree, and nested workspace ``srcs`` are a known limitation of this logic.
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
    resolve_source_files,
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
    - for generated bundle sources or data, the mount root may be the sandbox copy of a
      ``bazel-out`` directory, for example
      ``.../sandbox/.../execroot/_main/bazel-out/.../docs/generated``;
      generated files below it can resolve to the action execroot spelling,
      for example
      ``~/.cache/bazel/.../execroot/_main/bazel-out/.../docs/generated/index.rst``.
    - for in-tree (same-workspace) source bundles, the mount root directory
      exists in the sandbox but the individual source files are symlinks back
      to the original workspace, for example
      ``.../sandbox/.../execroot/_main/score/socom/docs/index.rst``
      ``→ /home/user/workspace/score/socom/docs/index.rst``.

    This applies to all bundle types: external repositories, generated bundle
    sources or data, and in-tree (same-workspace) source bundles. Resolve one mounted
    source file first and walk back by its bundle-relative suffix to get the
    canonical root.

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
    for source_file in walk_dir.rglob("*"):
        if not source_file.is_file() or source_file.suffix not in {".md", ".rst"}:
            continue
        relative_path = source_file.relative_to(walk_dir)
        return source_file.resolve().parents[len(relative_path.parts) - 1]
    return walk_dir.resolve()


def _make_mount_entry(
    walk_dir: Path,
    spec: MountSpec,
    exclude: tuple[str, ...] = (),
) -> dict[str, object]:
    """Build a ``sphinx_mounts`` directory entry.

    ``exclude`` contains paths relative to ``walk_dir``. ``sphinx_mounts`` applies
    those patterns during its recursive walk, so an empty tuple means this mount
    owns the whole directory and a pattern such as ``components/**`` delegates
    that subtree to a nested mount.
    """
    return {
        "dir": str(_canonical_mount_dir(walk_dir, spec)),
        "mount_at": spec.mount_at,
        "attach_to": spec.attach_to,
        "entry_doc": spec.entry_doc,
        "exclude": list(exclude),
    }


def _make_file_mount_entry(
    source_files: list[Path], spec: MountSpec
) -> dict[str, object]:
    """Build a file-list mount entry from the original source files."""
    return {
        "files": [str(source_file) for source_file in source_files],
        "mount_at": spec.mount_at,
        "attach_to": spec.attach_to,
        "entry_doc": spec.entry_doc,
    }


def _configured_source_suffixes(config: Config) -> tuple[str, ...]:
    """Return the source suffixes configured for the current Sphinx build."""
    configured = config.source_suffix
    # Sphinx accepts either a sequence of suffixes or a mapping from suffixes
    # to parser names; both forms expose the suffixes during iteration.
    if isinstance(configured, str):
        return (configured,)
    return tuple(configured)


def _nested_mount_pattern(parent_dir: Path, child_dir: Path) -> str | None:
    """Map a strict physical descendant to a recursive relative glob.

    Mount directories have already been resolved before this helper is called, so
    the comparison is about the directories Sphinx will physically walk rather
    than their Bazel or manifest spellings. Equal and unrelated directories do
    not create an ownership boundary and therefore return ``None``.
    """
    try:
        relative_dir = child_dir.relative_to(parent_dir)
    except ValueError:
        return None
    if not relative_dir.parts:
        return None
    return f"{relative_dir.as_posix()}/**"


def _mount_exclusions(
    source_dir: Path,
    source_mounts: list[tuple[MountSpec, Path]],
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """Return primary and per-mount exclusions in one pairwise traversal.

    The primary source walk must exclude every directory mount below
    ``source_dir``. Each directory mount must also exclude every nested directory
    mount from its own walk. Computing both sets here avoids rescanning the full
    mount list once for every parent mount. The two directions of each pair are
    checked because either directory may be the descendant.
    """
    primary_patterns: set[str] = set()
    nested_patterns = [set[str]() for _ in source_mounts]

    for parent_index, (_, parent_dir) in enumerate(source_mounts):
        primary_pattern = _nested_mount_pattern(source_dir, parent_dir)
        if primary_pattern is not None:
            primary_patterns.add(primary_pattern)

        for child_index in range(parent_index + 1, len(source_mounts)):
            _, child_dir = source_mounts[child_index]

            child_pattern = _nested_mount_pattern(parent_dir, child_dir)
            if child_pattern is not None:
                nested_patterns[parent_index].add(child_pattern)

            parent_pattern = _nested_mount_pattern(child_dir, parent_dir)
            if parent_pattern is not None:
                nested_patterns[child_index].add(parent_pattern)

    return (
        tuple(sorted(primary_patterns)),
        tuple(tuple(sorted(patterns)) for patterns in nested_patterns),
    )


def _exclude_mounted_primary_sources(
    config: Config,
    exclusions: tuple[str, ...],
) -> None:
    """Hide mounted bundle roots from Sphinx's primary source discovery.

    The exclusion is based on directory ownership rather than the manifest's
    current file list. This keeps newly created files visible to live preview
    while ensuring a source file is discovered by either the host tree or its
    owning bundle mount, never both.
    """
    if exclusions:
        # Preserve project-configured exclusions and append only the bundle roots
        # that are physically inside the primary source tree.
        config.exclude_patterns = [*config.exclude_patterns, *exclusions]


def _resolve_source_mounts(
    manifest: MountsManifest,
    ws_root: Path | None,
    runfiles_dir: Path | None,
) -> list[tuple[MountSpec, Path]]:
    """Resolve and validate the directory mounts used for ownership checks.

    Explicit source bundles are deliberately omitted: ``docs_bundle(srcs = [...])``
    owns a declared file list, not the directory containing those files, so it
    must remain in ``sphinx_mounts`` file-list mode and must not create a directory
    exclusion. ``srcs`` is intended for generated sources outside the primary
    source tree; an explicitly mounted workspace file below a walked root remains
    a known limitation because exact-file exclusions are not derived here.
    """
    source_mounts: list[tuple[MountSpec, Path]] = []
    for spec in manifest.mounts:
        if not spec.src_root or spec.files:
            continue
        walk_dir = resolve_walk_dir(manifest, spec, ws_root, runfiles_dir)
        if not walk_dir.is_dir():
            raise ValueError(
                "score_mounts: resolved mount dir does not exist: "
                f"{walk_dir} (mount_at={spec.mount_at})"
            )
        source_mounts.append((spec, walk_dir.resolve()))
    return source_mounts


def _on_config_inited(app: Sphinx, config: Config) -> None:
    """Translate the Bazel manifest into ``sphinx_mounts`` runtime config.

    Runs on Sphinx's ``config-inited`` event (before ``sphinx_mounts``, see the
    priority in ``setup``). For each mount it resolves the directory
    ``sphinx_mounts`` should walk, excludes nested mount roots from containing
    walks, and writes the assembled list to ``config.mounts``. A missing or
    empty manifest is a no-op.
    """
    manifest = _read_manifest(config)
    if manifest is None or not manifest.mounts:
        return

    ws_root = find_ws_root()
    runfiles_dir = get_runfiles_dir() if ws_root is not None else None

    # In every context sphinx_mounts reads the bundle's original files (no copy
    # is made); directory mounts are walked while explicit source mounts use
    # their declared file list. Only where those files are staged differs:
    #   * external bundle: use its runfiles-relative location under ``bazel run``
    #     and its execroot-relative location in a sandboxed Bazel build.
    #   * in-tree bundle under `bazel run`: use the live workspace source
    #     (ws_root/src_root) -- editable, best for live preview / jump-to-def.
    #   * in-tree bundle in a sandbox build: the bundle's source files are staged
    #     as inputs at their exec-root-relative path. The manifest lives under
    #     bazel-out/ and is NOT colocated with them, so src_root is resolved
    #     against the exec root (the sphinx action's cwd), not the manifest.

    # Directory mounts need to be resolved as a group before runtime entries are
    # assembled. Only then can their physical roots be compared for nesting and
    # can both Sphinx's primary walk and each parent mount be given exclusions.
    source_mounts = _resolve_source_mounts(manifest, ws_root, runfiles_dir)
    primary_exclusions, nested_exclusions = _mount_exclusions(
        Path(app.srcdir).resolve(), source_mounts
    )
    _exclude_mounted_primary_sources(config, primary_exclusions)

    # ``source_mounts`` omits pure-data and explicit file-list entries. Explicit
    # ``srcs`` entries intentionally retain their existing file-list behavior;
    # generated sources are expected to live outside the primary source tree.
    # Map the remaining specs back to their prevalidated paths by object identity
    # so the following loop can preserve manifest declaration order. ``MountSpec``
    # contains lists and is therefore not usable as a dictionary key, despite its
    # frozen dataclass declaration.
    source_mounts_by_id = {
        id(spec): (index, walk_dir)
        for index, (spec, walk_dir) in enumerate(source_mounts)
    }

    # Pure-data bundles have empty src_root; skip directory walk.
    runtime_mounts: list[dict[str, object]] = []
    for spec in manifest.mounts:
        if not spec.src_root:
            continue
        if spec.files:
            # Explicit source bundles use sphinx-mounts' file-list mode so the
            # original files are read directly without discovering siblings.
            source_files = resolve_source_files(manifest, spec, ws_root, runfiles_dir)
            source_suffixes = _configured_source_suffixes(config)
            document_files = [
                source_file
                for source_file in source_files
                if any(source_file.name.endswith(suffix) for suffix in source_suffixes)
            ]
            if not document_files:
                # An explicit bundle may contain only companion assets. Such
                # assets remain available at their original paths, but there
                # is no Sphinx document to register for this mount.
                continue
            # Companion assets stay in the original source directory and are
            # resolved relative to the explicitly mounted document.
            runtime_mounts.append(_make_file_mount_entry(document_files, spec))
            continue

        # This directory was validated during the ownership pass above. Reuse its
        # resolved spelling so the exclusion patterns and the runtime mount refer
        # to exactly the same physical root.
        index, walk_dir = source_mounts_by_id[id(spec)]
        runtime_mounts.append(
            _make_mount_entry(
                walk_dir,
                spec,
                nested_exclusions[index],
            )
        )

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
