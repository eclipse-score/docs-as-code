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

import pytest

from src.extensions.score_mounts import _make_mount_entry, _resolve_data_mounts
from src.extensions.score_mounts._resolver import MountsManifest, MountSpec


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


def test_source_supporting_file_is_not_mounted_as_a_second_source_tree(
    tmp_path: Path,
) -> None:
    """Supporting files on a source bundle do not create a duplicate mount."""
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    (source_dir / "index.rst").write_text("Index", encoding="utf-8")
    fixture = tmp_path / "src" / "tests" / "scenario" / "BUILD"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("filegroup(name = 'fixture')", encoding="utf-8")

    spec = MountSpec(
        src_root="docs",
        runtime_path="docs",
        mount_at="docs",
        data=["src/tests/scenario/BUILD"],
        path_check="off",
    )
    manifest = MountsManifest(mounts=[spec])

    assert _resolve_data_mounts(manifest, tmp_path, tmp_path / "runfiles") == {}
    assert _make_mount_entry(source_dir, spec)["path_check"] == "off"


def test_non_document_payload_does_not_mount_its_parent_directory(
    tmp_path: Path,
) -> None:
    """A data-only BUILD payload must not turn neighboring docs into mounts."""
    data_file = tmp_path / "bazel-bin" / "scenario" / "BUILD"
    data_file.parent.mkdir(parents=True)
    data_file.write_text("filegroup(name = 'fixture')", encoding="utf-8")
    (data_file.parent / "index.rst").write_text("not a bundle page", encoding="utf-8")

    manifest = MountsManifest(
        mounts=[
            MountSpec(
                src_root="",
                runtime_path="",
                mount_at="data",
                data=["bazel-out/k8-fastbuild/bin/scenario/BUILD"],
            )
        ]
    )

    assert _resolve_data_mounts(manifest, tmp_path, tmp_path / "runfiles") == {}


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
