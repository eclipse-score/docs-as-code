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
remains correct when files are added later. Explicit ``srcs`` have two
different runtime paths: the root bundle (the manifest entry with
``root_bundle=True``) stays in Sphinx's source tree and is restricted by
positive ``include_patterns``, while a mounted child bundle uses
``sphinx_mounts`` file-list mode at its declared mount location.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, cast

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging

from src.extensions.score_mounts._resolver import (
    BundleMetadata,
    MountsManifest,
    MountSpec,
    load_mounts_manifest,
    resolve_source_files,
    resolve_walk_dir,
)
from src.helper_lib import find_ws_root, get_runfiles_dir

logger = logging.getLogger(__name__)


class _MountAwareProject(Protocol):
    """The sphinx-mounts project fields used by the ownership adapter."""

    _mount_entry_docnames: Mapping[int, Sequence[str]]


def _set_runtime_attribute(target: object, name: str, value: object) -> None:
    """Store extension state on an object without requiring third-party stubs."""
    setattr(target, name, value)


def _read_manifest(config: Config):
    """Locate and load the mounts manifest, or return ``None`` when unset.

    ``mounts_manifest`` is set by the docs CLI via ``--define`` from Bazel's
    ``MOUNTS_MANIFEST`` env var. The CLI resolves the path for the active
    execution context before passing it to Sphinx.
    """
    raw = getattr(config, "mounts_manifest", "")
    if not raw or not raw.strip() or not isinstance(raw, str):
        return None

    return load_mounts_manifest(Path(raw))


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
        # TODO: Remove this data-mount path, including the root-bundle
        # distinction, once callers migrate generated documentation from
        # ``docs_bundle(data = [...])`` to ``docs_bundle(srcs = [...])``.
        # Data belonging to the root bundle, which owns Sphinx's source tree,
        # is already part of the Sphinx action inputs. Only rebased child data
        # has a documentation-tree mount.
        if spec.root_bundle:
            continue
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
        "toctree_index": spec.toctree_index,
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
        "toctree_index": spec.toctree_index,
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

    Explicit source bundles are deliberately omitted from directory ownership:
    ``docs_bundle(srcs = [...])`` owns a declared file list, not the directory
    containing those files, so it must not create a directory exclusion. A
    mounted child bundle uses ``sphinx_mounts`` file-list mode, while a primary
    bundle's explicit ``srcs`` are restricted through Sphinx's positive
    ``include_patterns`` selection. An explicitly mounted workspace file below
    a walked root remains a known limitation because exact-file exclusions are
    not derived here.
    """
    source_mounts: list[tuple[MountSpec, Path]] = []
    for spec in manifest.mounts:
        if not spec.src_root or spec.files or spec.root_bundle:
            continue
        walk_dir = resolve_walk_dir(manifest, spec, ws_root, runfiles_dir)
        if not walk_dir.is_dir():
            raise ValueError(
                "score_mounts: resolved mount dir does not exist: "
                f"{walk_dir} (mount_at={spec.mount_at})"
            )
        source_mounts.append((spec, walk_dir.resolve()))
    return source_mounts


def _configure_root_bundle_srcs_allowlist(
    app: Sphinx,
    config: Config,
    manifest: MountsManifest,
    ws_root: Path | None,
    runfiles_dir: Path | None,
) -> None:
    """Restrict the root bundle's explicit ``srcs`` to its declared documents.

    ``docs_bundle(srcs = [...])`` is a positive source selection. It must not
    be represented as a ``sphinx_mounts`` file-list mount: the root bundle
    already owns Sphinx's source tree, and a second mount would duplicate that
    ownership. ``include_patterns`` is evaluated by Sphinx before the read
    phase and keeps undeclared siblings out without depending on which files
    happen to be present as sandbox symlinks.
    """
    root_bundle_src_specs = [
        spec for spec in manifest.mounts if spec.root_bundle and spec.files
    ]
    if not root_bundle_src_specs:
        return
    if len(root_bundle_src_specs) > 1:
        raise ValueError(
            "score_mounts: composition manifest contains more than one root "
            "bundle with explicit ``srcs``"
        )

    sphinx_source_root = Path(app.srcdir)
    include_patterns: set[str] = set()
    for source_file in resolve_source_files(
        manifest, root_bundle_src_specs[0], ws_root, runfiles_dir
    ):
        try:
            relative = source_file.relative_to(sphinx_source_root)
        except ValueError as exc:
            raise ValueError(
                "score_mounts: explicit ``srcs`` source is outside the Sphinx "
                f"source directory: {source_file} "
                f"(source directory={sphinx_source_root})"
            ) from exc
        include_patterns.add(relative.as_posix())
    config.include_patterns = sorted(include_patterns)


def _docnames_by_mount_index(
    project: object,
    runtime_specs: Sequence[MountSpec | None],
) -> dict[int, tuple[str, ...]]:
    """Return the docnames produced by each configured runtime mount.

    The returned dictionary uses the mount's index in ``config.mounts`` as its
    key and contains the docnames that ``sphinx-mounts`` actually discovered
    for that mount. ``_set_document_bundles`` combines those indexes with the
    corresponding ``MountSpec`` objects to associate each mounted document
    with a bundle.

    ``score_mounts`` and ``sphinx_mounts`` are version-bound together, so the
    adapter's shape is part of their shared contract. Casting documents that
    contract for the type checker without re-validating every value keeps this
    bridge focused on translating bundle associations, rather than duplicating
    manifest validation in Python.
    """
    if not runtime_specs:
        return {}

    # The mapping is produced by the matching sphinx-mounts version and uses
    # the same indexes as the runtime mount list assembled below.
    mount_aware_project = cast(_MountAwareProject, project)
    raw_docnames = mount_aware_project._mount_entry_docnames  # pyright: ignore[reportPrivateUsage] - sphinx-mounts exposes this mapping on its project object
    return {index: tuple(docnames) for index, docnames in raw_docnames.items()}


def _set_document_bundles(app: Sphinx, env: object) -> None:
    """Record the bundle associated with each document in the current build."""
    # ``config-inited`` stores the manifest on the application because the
    # later ``env-updated`` event receives the environment, not the config.
    manifest: MountsManifest | None = getattr(app, "_score_mounts_manifest", None)
    if manifest is None:
        _set_runtime_attribute(env, "_score_document_bundles", {})
        return

    # Keep the manifest order next to the mount indexes reported by
    # sphinx-mounts. Data mounts have no associated bundle and are represented
    # by ``None`` in this parallel list.
    runtime_specs: tuple[MountSpec | None, ...] = getattr(
        app, "_score_mount_runtime_specs", ()
    )
    project = getattr(env, "project", None)
    docnames_by_mount = _docnames_by_mount_index(project, runtime_specs)
    document_bundles: dict[str, BundleMetadata] = {}
    mounted_docnames: set[str] = set()
    for index, docnames in docnames_by_mount.items():
        spec = runtime_specs[index]
        mounted_docnames.update(docnames)
        if spec is None or not spec.bundle.label:
            continue
        # A mounted document is associated with the bundle that supplied its
        # mount, not with the primary source tree where its file is staged.
        for docname in docnames:
            document_bundles[docname] = spec.bundle

    # Bazel emits one root source entry for a composition. Taking that entry
    # directly keeps this consumer aligned with the producer-owned contract.
    primary_bundle = next(
        (
            spec.bundle
            for spec in manifest.mounts
            if spec.root_bundle and spec.bundle.label and spec.src_root
        ),
        None,
    )
    if primary_bundle is not None:
        found_docs = cast("set[str]", getattr(env, "found_docs", set()))
        for docname in found_docs:
            # Sphinx's discovery set is the authoritative list for the primary
            # tree. Do not overwrite a bundle association already assigned to a
            # mounted bundle, including entries skipped during its walk.
            if docname not in mounted_docnames:
                document_bundles.setdefault(docname, primary_bundle)

    # Store only the final docname-to-bundle mapping on the environment so the
    # later matcher can consume it without re-reading paths or mounts.
    _set_runtime_attribute(env, "_score_document_bundles", document_bundles)


def get_document_bundles(app: Sphinx) -> dict[str, BundleMetadata]:
    """Return the bundle associated with each document in the active build."""
    # Return a copy because consumers should not be able to mutate Sphinx's
    # environment state while they inspect the document-to-bundle mapping.
    return dict(getattr(app.env, "_score_document_bundles", {}))


def _on_config_inited(app: Sphinx, config: Config) -> None:
    """Translate the Bazel manifest into ``sphinx_mounts`` runtime config.

    Runs on Sphinx's ``config-inited`` event (before ``sphinx_mounts``, see the
    priority in ``setup``). For each mount it resolves the directory
    ``sphinx_mounts`` should walk, excludes nested mount roots from containing
    walks, and writes the assembled list to ``config.mounts``. A missing or
    empty manifest is a no-op.
    """
    manifest = _read_manifest(config)
    # Keep the input and the runtime index mapping on the app for
    # ``env-updated``, which is where Sphinx exposes the documents it actually
    # discovered.
    _set_runtime_attribute(app, "_score_mounts_manifest", manifest)
    _set_runtime_attribute(app, "_score_mount_runtime_specs", ())
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
    _configure_root_bundle_srcs_allowlist(
        app,
        config,
        manifest,
        ws_root,
        runfiles_dir,
    )

    # ``source_mounts`` omits pure-data and explicit file-list entries. Explicit
    # ``srcs`` entries mounted below a primary source tree retain
    # file-list behavior; the root bundle's ``srcs`` are restricted through
    # ``include_patterns`` above.
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
    # This list mirrors ``config.mounts`` so an index from sphinx-mounts can be
    # translated back to the bundle that owns the resulting docnames.
    runtime_specs: list[MountSpec | None] = []
    for spec in manifest.mounts:
        if not spec.src_root or spec.root_bundle:
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
            runtime_specs.append(spec)
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
        runtime_specs.append(spec)

    config.mounts = runtime_mounts

    # Resolve data (e.g. genrule outputs in bazel-out).
    # Data paths are execroot-relative (e.g. bazel-out/.../bin/src/.../index.rst).
    # During bazel run: compute execroot from RUNFILES_DIR; during sandboxed build:
    # cwd IS the execroot.
    # Only the parent directories of resolved files are added to mounts.
    data_mounts = _resolve_data_mounts(manifest, ws_root, runfiles_dir)
    for walk_dir_str, spec in data_mounts.items():
        config.mounts.append(_make_mount_entry(Path(walk_dir_str), spec))
        runtime_specs.append(None)
    logger.info("score_mounts: added %d data mount(s)", len(data_mounts))

    # Prevent sphinx_mounts._on_load_toml from overwriting our config with a
    # possibly-stale docs/ubproject.toml entry.
    config.mounts_from_toml = None

    logger.info("score_mounts: registered %d mount(s)", len(runtime_mounts))
    _set_runtime_attribute(app, "_score_mount_runtime_specs", tuple(runtime_specs))


def setup(app: Sphinx) -> dict[str, object]:
    """Sphinx extension entry point: register the config value and event hook.

    ``mounts_manifest`` carries the Bazel-resolved manifest path. The
    ``config-inited`` handler is connected at priority 300 (< 400) so it runs
    before ``sphinx_mounts._on_load_toml`` and can override the mount config the
    latter would otherwise load from ``ubproject.toml``.
    """
    app.add_config_value("mounts_manifest", default="", rebuild="env", types=(str,))
    app.connect("config-inited", _on_config_inited, priority=300)
    # The document-to-bundle mapping is calculated after Sphinx has completed
    # discovery so it contains only documents that really entered the environment.
    app.connect("env-updated", _set_document_bundles, priority=500)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
