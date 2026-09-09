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

from pathlib import Path
from unittest.mock import Mock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem as FFS

from src.docs_cli import cli as docs_cli
from src.docs_cli.cli import sphinx_arguments


@pytest.fixture
def workspace(fs: FFS, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create the minimum Bazel workspace needed by the CLI tests."""

    # The CLI reads its configuration from the process environment, so remove
    # optional values left behind by the test runner before setting the basics.
    ENVIRONMENT_OVERRIDES = (
        "EXTERNAL_NEEDS_FILES",
        "TEST_SOURCES",
        "MOUNTS_MANIFEST",
        "SPHINX_CONFIG_FILE",
        "SCORE_METAMODEL_YAML",
        "GITHUB_REPOSITORY",
        "KNOWN_GOOD_JSON",
        "RUNFILES_DIR",
        "RUNFILES_MANIFEST_FILE",
    )
    for name in ENVIRONMENT_OVERRIDES:
        monkeypatch.delenv(name, raising=False)

    workspace = Path("/workspace")
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))
    monkeypatch.setenv("PACKAGE_DIR", "component")
    monkeypatch.setenv("SOURCE_DIRECTORY", "docs")
    monkeypatch.setenv("DATA", "[]")
    monkeypatch.setenv("RUNFILES_DIR", str(workspace / "runfiles"))

    fs.create_dir(workspace / "component")
    fs.create_dir(workspace / "runfiles")
    for name in ("MODULE.bazel", "MODULE.bazel.lock", "component/BUILD"):
        fs.create_file(workspace / name, contents="stable")
    return workspace


@pytest.mark.parametrize(
    "action,builder",
    [
        ("incremental", "html"),
        ("check", "needs"),
        ("linkcheck", "linkcheck"),
        ("build_needs_json", "needs"),
    ],
)
def test_build_action_selects_sphinx_builder(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    builder: str,
) -> None:
    """Each public action invokes Sphinx with its corresponding builder."""

    # Arrange
    monkeypatch.setenv("ACTION", action)
    build_dir = workspace / "component/_build"
    if action == "build_needs_json":
        # The sandboxed action uses its declared output, not the package cache.
        monkeypatch.chdir(workspace)
        monkeypatch.setenv("OUTPUT_DIRECTORY", "outputs/needs")
        build_dir = workspace / "outputs/needs"
    noop_sphinx = Mock(return_value=0)
    update_hash = Mock()
    monkeypatch.setattr(docs_cli, "sphinx_main", noop_sphinx)
    monkeypatch.setattr(docs_cli, "update_module_hash", update_hash)

    # Act
    exit_code = docs_cli.main([])

    # Assert
    # The CLI propagates Sphinx's successful result.
    assert exit_code == 0
    noop_sphinx.assert_called_once()
    arguments = noop_sphinx.call_args.args[0]
    # The source and output paths are derived from the Bazel package directory.
    if action == "build_needs_json":
        assert arguments[:2] == [str(workspace / "docs"), str(build_dir)]
        update_hash.assert_not_called()
    else:
        assert arguments[:2] == [str(workspace / "component/docs"), str(build_dir)]
    # The action selects the builder exposed by its public Bazel target.
    assert arguments[-2:] == ["-b", builder]


def test_failed_build_returns_exit_code_and_forces_next_build_clean(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure without Sphinx warnings must still invalidate partial output."""

    # Arrange
    monkeypatch.setenv("ACTION", "incremental")
    build_dir = workspace / "component/_build"

    def failing_sphinx_mock(arguments: list[str]) -> int:
        build_dir.mkdir()
        # Simulate a partial build by creating a dummy output file.
        # That file must not survive a failed build.
        (build_dir / "partial-output").touch()
        return 2

    monkeypatch.setattr(docs_cli, "sphinx_main", failing_sphinx_mock)

    # Act
    exit_code = docs_cli.main([])

    # Assert
    # The original Sphinx failure is returned to Bazel.
    assert exit_code == 2
    # The failure marker explains why the partial output must not be reused.
    assert "Build failed with exit code 2" in (build_dir / "warnings.txt").read_text()
    # Failed builds must not record a successful input hash.
    assert not (build_dir / ".module_bazel_hash").exists()

    # Arrange
    # Use a second replacement to observe whether the failed output was removed.
    def rebuild(arguments: list[str]) -> int:
        assert not build_dir.exists()
        build_dir.mkdir()
        return 0

    monkeypatch.setattr(docs_cli, "sphinx_main", rebuild)

    # Act
    rebuild_exit_code = docs_cli.main([])

    # Assert
    # The marker from the failed build causes the next invocation to start clean.
    assert rebuild_exit_code == 0


def test_live_preview_uses_port_and_bundle_watches(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("ACTION", "live_preview")
    manifest = workspace / "mounts.json"
    manifest.write_text(
        '{"mounts": [{"src_root": "extra/docs", "runtime_path": "extra/docs", "mount_at": "extra"}]}'
    )
    monkeypatch.setenv("MOUNTS_MANIFEST", str(manifest))
    autobuild = Mock()
    monkeypatch.setattr(docs_cli, "sphinx_autobuild_main", autobuild)

    # Act
    exit_code = docs_cli.main(["--port", "42424242424"])

    # Assert
    # Live preview exits after handing control to sphinx-autobuild.
    assert exit_code == 0
    autobuild.assert_called_once()
    arguments = autobuild.call_args.args[0]
    # The requested port and source-linker setting are forwarded unchanged.
    assert "--port=42424242424" in arguments
    assert "--define=skip_rescanning_via_source_code_linker=1" in arguments
    # Mounted bundle sources are watched in addition to the main docs tree.
    assert arguments[-2:] == ["--watch", str(workspace / "extra/docs")]
    # Live preview does not write the successful-build hash.
    assert not (workspace / "component/_build/.module_bazel_hash").exists()


def test_bazel_configuration_resolves_runfiles_and_preserves_repo_relative_edit_path(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("SPHINX_CONFIG_FILE", "config/conf.py")
    monkeypatch.setenv("SCORE_METAMODEL_YAML", "config/metamodel.yaml")
    monkeypatch.setenv("DATA", '[":bundle"]')
    monkeypatch.setenv("EXTERNAL_NEEDS_FILES", '["@vendor//:needs"]')
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("KNOWN_GOOD_JSON", "baseline.json")
    package = workspace / "component"

    # Act
    arguments = sphinx_arguments(workspace, package, package / "_build")

    # Assert
    expected_arguments = {
        # Generated configuration and metamodel paths use the runfiles tree.
        "-c",
        str(workspace / "runfiles/config"),
        f"--define=score_metamodel_yaml={workspace}/runfiles/config/metamodel.yaml",
        # DATA and EXTERNAL_NEEDS_FILES are passed as one Sphinx define.
        '--define=external_needs_source=[":bundle", "@vendor//:needs"]',
        # GitHub metadata must keep edit links repository-relative.
        "-A=github_user=owner",
        "-A=github_repo=repo",
        "-A=doc_path=component/docs",
        "--define=KNOWN_GOOD_JSON=baseline.json",
    }
    # Every expected option is present; their relative order is irrelevant here.
    assert expected_arguments <= set(arguments)


def test_direct_invocation_resolves_metamodel_relative_to_workspace(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    # This test covers the non-Bazel fallback, so no runfiles directory exists.
    monkeypatch.delenv("RUNFILES_DIR", raising=False)
    monkeypatch.setenv("SCORE_METAMODEL_YAML", "metamodel.yaml")

    # Act
    arguments = sphinx_arguments(workspace, workspace, workspace / "_build")

    # Assert
    # Without Bazel runfiles, the metamodel falls back to the workspace root.
    assert f"--define=score_metamodel_yaml={workspace}/metamodel.yaml" in arguments
    # A direct invocation has no generated Sphinx config to resolve.
    assert "-c" not in arguments
