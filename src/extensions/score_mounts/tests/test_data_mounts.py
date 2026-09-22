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
"""Tests for ``_resolve_data_mounts`` in the ``score_mounts`` extension."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from sphinx.application import Sphinx
from sphinx.config import Config

from src.extensions.score_mounts import (
    _configure_root_bundle_srcs_allowlist,  # pyright: ignore[reportPrivateUsage]
    _make_mount_entry,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    _resolve_data_mounts,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    _resolve_source_mounts,  # pyright: ignore[reportPrivateUsage] - white-box unit test
    _set_document_bundles,  # pyright: ignore[reportPrivateUsage]
)
from src.extensions.score_mounts._resolver import (
    BundleMetadata,
    MountsManifest,
    MountSpec,
)


def test_missing_data_file_raises(tmp_path: Path) -> None:
    """A manifest with an unavailable data file must fail fast."""
    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="",
                runtime_path="",
                mount_at="missing",
                data=["bazel-out/k8-fastbuild/bin/nonexistent.rst"],
            )
        ]
    )

    with pytest.raises(ValueError, match="resolved data file does not exist"):
        _resolve_data_mounts(manifest, tmp_path, tmp_path)


def test_existing_data_file_resolved(tmp_path: Path) -> None:
    """An existing data file resolves to its parent directory."""
    data_file = tmp_path / "bazel-bin" / "file.rst"
    data_file.parent.mkdir(parents=True)
    data_file.write_text("..", encoding="utf-8")

    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="",
                runtime_path="",
                mount_at="exists",
                data=["bazel-out/k8-fastbuild/bin/file.rst"],
            )
        ]
    )

    mounts = _resolve_data_mounts(manifest, tmp_path, tmp_path / "runfiles")

    assert str(tmp_path / "bazel-bin") in mounts


def test_root_bundle_srcs_are_a_positive_allowlist(tmp_path: Path) -> None:
    """Explicit ``srcs`` remain discoverable without undeclared siblings."""
    source_root = tmp_path / "docs"
    source_root.mkdir()
    selected = source_root / "selected.rst"
    sibling = source_root / "sibling.rst"
    selected.write_text("Selected", encoding="utf-8")
    sibling.write_text("Sibling", encoding="utf-8")
    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="docs",
                runtime_path="docs",
                mount_at="",
                files=["selected.rst"],
                root_bundle=True,
                bundle=BundleMetadata(
                    label="//:bundle",
                    name="bundle",
                ),
            )
        ]
    )
    app = SimpleNamespace(srcdir=str(source_root))
    config = SimpleNamespace(include_patterns=["**"])

    _configure_root_bundle_srcs_allowlist(
        cast(Sphinx, app),
        cast(Config, config),
        manifest,
        tmp_path,
        None,
    )

    assert config.include_patterns == ["selected.rst"]


def test_root_bundle_data_is_not_mounted_but_child_data_is(
    tmp_path: Path,
) -> None:
    """Only rebased child data creates a runtime data mount."""
    root_data = tmp_path / "bazel-bin" / "root.txt"
    child_data = tmp_path / "bazel-bin" / "child" / "child.txt"
    root_data.parent.mkdir(parents=True)
    child_data.parent.mkdir()
    root_data.write_text("root", encoding="utf-8")
    child_data.write_text("child", encoding="utf-8")
    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="",
                runtime_path="",
                mount_at="",
                data=["bazel-out/k8-fastbuild/bin/root.txt"],
                root_bundle=True,
            ),
            MountSpec(
                src_root="",
                runtime_path="",
                mount_at="child",
                data=["bazel-out/k8-fastbuild/bin/child/child.txt"],
                root_bundle=False,
            ),
        ]
    )

    mounts = _resolve_data_mounts(manifest, tmp_path, tmp_path / "runfiles")

    assert str(root_data.parent) not in mounts
    assert mounts[str(child_data.parent)] is manifest.mounts[1]


def test_data_mount_documents_do_not_get_a_bundle() -> None:
    """Mounted data documents stay unassociated instead of inheriting the root bundle."""
    primary = BundleMetadata(
        label="//:root",
        name="root",
    )
    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="",
                runtime_path="",
                mount_at="generated",
                root_bundle=False,
                bundle=BundleMetadata(
                    label="//:data",
                    name="data",
                ),
            ),
            MountSpec(
                src_root="docs",
                runtime_path="docs",
                mount_at="",
                root_bundle=True,
                bundle=primary,
            ),
        ]
    )
    env = SimpleNamespace(
        project=SimpleNamespace(_mount_entry_docnames={0: ["generated/page"]}),
        found_docs={"generated/page", "index"},
    )
    app = SimpleNamespace(
        env=env,
        _score_mounts_manifest=manifest,
        _score_mount_runtime_specs=(None,),
    )

    _set_document_bundles(cast(Sphinx, app), env)

    document_bundles = env._score_document_bundles
    assert "generated/page" not in document_bundles
    assert document_bundles["index"] == primary


def test_mounted_documents_get_their_declaring_bundle() -> None:
    """Mounted docnames use the bundle metadata attached to their mount."""
    primary = BundleMetadata(label="//:root", name="root")
    child = BundleMetadata(label="//:child", name="child")
    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="docs",
                runtime_path="docs",
                mount_at="",
                root_bundle=True,
                bundle=primary,
            ),
            MountSpec(
                src_root="child/docs",
                runtime_path="child/docs",
                mount_at="child",
                root_bundle=False,
                bundle=child,
            ),
        ]
    )
    env = SimpleNamespace(
        project=SimpleNamespace(_mount_entry_docnames={0: ["child/page"]}),
        found_docs={"child/page", "index"},
    )
    app = SimpleNamespace(
        env=env,
        _score_mounts_manifest=manifest,
        _score_mount_runtime_specs=(manifest.mounts[1],),
    )

    _set_document_bundles(cast(Sphinx, app), env)

    document_bundles = env._score_document_bundles
    assert document_bundles["child/page"] == child
    assert document_bundles["index"] == primary


def test_root_bundle_source_is_not_a_runtime_mount_but_child_source_is(
    tmp_path: Path,
) -> None:
    """Only rebased child source roots enter the runtime mount set."""
    root_dir = tmp_path / "root"
    child_dir = tmp_path / "child"
    root_dir.mkdir()
    child_dir.mkdir()
    (root_dir / "index.rst").write_text("Root", encoding="utf-8")
    (child_dir / "index.rst").write_text("Child", encoding="utf-8")
    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="root",
                runtime_path="root",
                mount_at="",
                root_bundle=True,
            ),
            MountSpec(
                src_root="child",
                runtime_path="child",
                mount_at="child",
                root_bundle=False,
            ),
        ]
    )

    mounts = _resolve_source_mounts(manifest, tmp_path, None)

    assert mounts == [(manifest.mounts[1], child_dir.resolve())]


def test_mount_entry_uses_canonical_directory_for_symlinked_bundle(
    tmp_path: Path,
) -> None:
    """The external mounted root must match Sphinx's resolved asset paths."""
    canonical_repo = tmp_path / "repository-cache" / "bundle"
    canonical_dir = canonical_repo / "docs"
    canonical_dir.mkdir(parents=True)
    canonical_source = canonical_dir / "index.rst"
    canonical_source.write_text("Bundle", encoding="utf-8")
    staged_repo = tmp_path / "sandbox" / "external" / "bundle"
    staged_dir = staged_repo / "docs"
    staged_dir.mkdir(parents=True)
    staged_dir.joinpath("index.rst").symlink_to(canonical_source)
    spec = MountSpec(
        src_root="external/bundle/docs",
        runtime_path="../bundle/docs",
        mount_at="bundle",
        external=True,
        repository="bundle",
    )

    entry = _make_mount_entry(staged_dir, spec)

    assert entry["dir"] == str(canonical_dir)


def test_canonical_mount_dir_in_tree_sandbox_bundle(tmp_path: Path) -> None:
    """In-tree bundles with symlinked files must resolve to the workspace root."""
    workspace_docs = tmp_path / "workspace" / "module" / "docs"
    workspace_docs.mkdir(parents=True)
    (workspace_docs / "index.rst").write_text("Index", encoding="utf-8")
    (workspace_docs / "guide").mkdir()
    (workspace_docs / "guide" / "overview.rst").write_text("Overview", encoding="utf-8")

    sandbox_docs = tmp_path / "sandbox" / "module" / "docs"
    sandbox_docs.mkdir(parents=True)
    sandbox_docs.joinpath("index.rst").symlink_to(workspace_docs / "index.rst")
    (sandbox_docs / "guide").mkdir()
    sandbox_docs.joinpath("guide", "overview.rst").symlink_to(
        workspace_docs / "guide" / "overview.rst"
    )

    spec = MountSpec(
        src_root="module/docs", runtime_path="module/docs", mount_at="module"
    )

    entry = _make_mount_entry(sandbox_docs, spec)

    assert entry["dir"] == str(workspace_docs)


def test_canonical_mount_dir_empty_bundle_fallback(tmp_path: Path) -> None:
    """A bundle with no .rst/.md files falls back to walk_dir.resolve()."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "diagram.puml").write_text("@startuml\n@enduml", encoding="utf-8")

    spec = MountSpec(
        src_root="module/docs", runtime_path="module/docs", mount_at="module"
    )

    entry = _make_mount_entry(bundle_dir, spec)

    assert entry["dir"] == str(bundle_dir.resolve())


def test_mount_entry_uses_canonical_directory_for_generated_data_bundle(
    tmp_path: Path,
) -> None:
    """Generated data bundles may resolve from the sandbox to bazel-out."""
    canonical_dir = (
        tmp_path
        / "execroot"
        / "_main"
        / "bazel-out"
        / "k8-fastbuild"
        / "bin"
        / "src"
        / "extensions"
        / "score_metamodel"
        / "docs"
        / "generated"
    )
    canonical_dir.mkdir(parents=True)
    canonical_source = canonical_dir / "index.rst"
    canonical_source.write_text("Metamodel", encoding="utf-8")
    staged_dir = (
        tmp_path
        / "sandbox"
        / "linux-sandbox"
        / "42"
        / "execroot"
        / "_main"
        / "bazel-out"
        / "k8-fastbuild"
        / "bin"
        / "src"
        / "extensions"
        / "score_metamodel"
        / "docs"
        / "generated"
    )
    staged_dir.mkdir(parents=True)
    staged_dir.joinpath("index.rst").symlink_to(canonical_source)
    spec = MountSpec(
        src_root="",
        runtime_path="",
        mount_at="reference/metamodel",
        data=[
            "bazel-out/k8-fastbuild/bin/src/extensions/"
            "score_metamodel/docs/generated/index.rst"
        ],
    )

    entry = _make_mount_entry(staged_dir, spec)

    assert entry["dir"] == str(canonical_dir)
