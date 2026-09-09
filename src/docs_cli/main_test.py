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
from src.docs_cli.cli import DocsCliConfig, sphinx_arguments


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
        "SCORE_SOURCELINKS",
        "GITHUB_REPOSITORY",
        "KNOWN_GOOD_JSON",
        "SPHINX_EXTRA_OPTS",
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
    monkeypatch.setenv("SPHINX_EXTRA_OPTS", "[]")
    monkeypatch.setenv("RUNFILES_DIR", str(workspace / "runfiles"))

    fs.create_dir(workspace / "component")
    fs.create_dir(workspace / "component/docs")
    fs.create_dir(workspace / "docs")
    fs.create_dir(workspace / "bundle/docs")
    fs.create_dir(workspace / "runfiles")
    fs.create_dir(workspace / "runfiles/config")
    for name in ("MODULE.bazel", "MODULE.bazel.lock", "component/BUILD"):
        fs.create_file(workspace / name, contents="stable")
    for name in (
        "runfiles/config/conf.py",
        "runfiles/config/metamodel.yaml",
        "source_links.json",
        "baseline.json",
        "metamodel.yaml",
        "bundle/conf.py",
        "bundle/metamodel.yaml",
    ):
        fs.create_file(workspace / name, contents="{}")
    fs.create_file(workspace / "runfiles/config/mounts.json", contents='{"mounts": []}')
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
    # The source and output paths are derived from the correct execution
    # context. The build action uses its execution-root source and declared
    # output; interactive actions use the workspace package cache.
    if action == "build_needs_json":
        assert arguments[:2] == [str(workspace / "docs"), str(build_dir)]
        # The declared output contains only the Needs inventory; Sphinx's
        # doctrees and warning diagnostics stay outside that output tree.
        assert ["-d", str(build_dir) + "_doctrees"] == arguments[10:12]
        assert "--warning-file" not in arguments
        update_hash.assert_not_called()
    else:
        assert arguments[:2] == [str(workspace / "component/docs"), str(build_dir)]
        assert "--warning-file" in arguments
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
    monkeypatch.setenv("ACTION", "incremental")
    monkeypatch.setenv("SPHINX_CONFIG_FILE", "config/conf.py")
    monkeypatch.setenv("SCORE_METAMODEL_YAML", "config/metamodel.yaml")
    monkeypatch.setenv("MOUNTS_MANIFEST", "config/mounts.json")
    monkeypatch.setenv("SCORE_SOURCELINKS", "source_links.json")
    monkeypatch.setenv("DATA", '[":bundle"]')
    monkeypatch.setenv("EXTERNAL_NEEDS_FILES", '["@vendor//:needs"]')
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("KNOWN_GOOD_JSON", "baseline.json")

    # Act
    config = DocsCliConfig.from_environment()
    assert config.source_directory == workspace / "component/docs"
    assert config.sphinx_config_file == workspace / "runfiles/config/conf.py"
    assert config.metamodel_yaml == workspace / "runfiles/config/metamodel.yaml"
    assert config.mounts_manifest == workspace / "runfiles/config/mounts.json"
    assert config.score_sourcelinks_json == workspace / "source_links.json"
    assert config.known_good_json == workspace / "baseline.json"
    arguments = sphinx_arguments(config)

    # Assert
    expected_arguments = {
        # Runfiles-backed configuration inputs use the runfiles tree.
        "-c",
        str(workspace / "runfiles/config"),
        f"--define=score_metamodel_yaml={workspace}/runfiles/config/metamodel.yaml",
        f"--define=mounts_manifest={workspace}/runfiles/config/mounts.json",
        f"--define=score_sourcelinks_json={workspace}/source_links.json",
        # DATA and EXTERNAL_NEEDS_FILES are passed as one Sphinx define.
        '--define=external_needs_source=[":bundle", "@vendor//:needs"]',
        # GitHub metadata must keep edit links repository-relative.
        "-A=github_user=owner",
        "-A=github_repo=repo",
        "-A=doc_path=component/docs",
        f"--define=KNOWN_GOOD_JSON={workspace}/baseline.json",
    }
    # Every expected option is present; their relative order is irrelevant here.
    assert expected_arguments <= set(arguments)


def test_direct_invocation_resolves_metamodel_relative_to_workspace(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    # This test covers the non-Bazel fallback, so no runfiles directory exists.
    monkeypatch.setenv("ACTION", "incremental")
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)
    monkeypatch.delenv("RUNFILES_DIR", raising=False)
    monkeypatch.setenv("SCORE_METAMODEL_YAML", "metamodel.yaml")
    monkeypatch.chdir(workspace)

    # Act
    arguments = sphinx_arguments(DocsCliConfig.from_environment())

    # Assert
    # Without Bazel runfiles, the metamodel falls back to the workspace root.
    assert f"--define=score_metamodel_yaml={workspace}/metamodel.yaml" in arguments
    # A direct invocation has no generated Sphinx config to resolve.
    assert "-c" not in arguments


def test_bazel_run_allows_workspace_root_package(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The root package is represented by an intentionally empty PACKAGE_DIR."""
    # Arrange
    monkeypatch.setenv("ACTION", "incremental")
    monkeypatch.setenv("PACKAGE_DIR", "")

    # Act
    config = DocsCliConfig.from_environment()

    # Assert
    assert config.is_bazel_run
    assert config.package_directory == Path()
    assert config.package_dir == workspace
    assert config.source_directory == workspace / "docs"
    assert config.build_dir == workspace / "_build"


def test_bazel_build_configuration_uses_execution_root_paths_and_extra_options(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build actions use declared paths and preserve action-specific options."""
    # Arrange
    monkeypatch.setenv("ACTION", "build_needs_json")
    monkeypatch.setenv("SOURCE_DIRECTORY", "bundle/docs")
    monkeypatch.setenv("OUTPUT_DIRECTORY", "outputs/needs")
    monkeypatch.setenv("SPHINX_CONFIG_FILE", "bundle/conf.py")
    monkeypatch.setenv("SCORE_METAMODEL_YAML", "bundle/metamodel.yaml")
    monkeypatch.setenv("SPHINX_EXTRA_OPTS", '["--define=custom=value with spaces"]')
    monkeypatch.chdir(workspace)

    # Act
    config = DocsCliConfig.from_environment()
    arguments = sphinx_arguments(config)

    # Assert
    assert config.is_bazel_build
    assert not config.is_bazel_run
    assert config.source_directory == workspace / "bundle/docs"
    assert config.output_directory == workspace / "outputs/needs"
    assert config.sphinx_config_file == workspace / "bundle/conf.py"
    assert config.metamodel_yaml == workspace / "bundle/metamodel.yaml"
    assert arguments[:2] == [
        str(workspace / "bundle/docs"),
        str(workspace / "outputs/needs"),
    ]
    assert ["-d", str(workspace / "outputs/needs_doctrees")] == arguments[10:12]
    assert "--warning-file" not in arguments
    assert "--define=custom=value with spaces" in arguments


@pytest.mark.parametrize(
    "environment_name,value",
    [
        ("BUILD_WORKSPACE_DIRECTORY", "/workspace/missing"),
        ("SOURCE_DIRECTORY", "missing/docs"),
        ("SPHINX_CONFIG_FILE", "config/missing.py"),
        ("SCORE_METAMODEL_YAML", "config/missing.yaml"),
        ("KNOWN_GOOD_JSON", "missing.json"),
        ("MOUNTS_MANIFEST", "/workspace/missing-mounts.json"),
        ("SCORE_SOURCELINKS", "missing-source-links.json"),
    ],
)
def test_configuration_rejects_missing_input_paths_early(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    environment_name: str,
    value: str,
) -> None:
    """Configured workspace and input paths fail before Sphinx is invoked."""
    # Arrange
    monkeypatch.setenv("ACTION", "incremental")
    monkeypatch.setenv(environment_name, value)

    # Act and assert
    with pytest.raises(ValueError, match=environment_name):
        DocsCliConfig.from_environment()


def test_bazel_build_allows_declared_output_to_be_created_by_sphinx(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sandboxed action validates inputs but leaves its output creation to Sphinx."""
    # Arrange
    monkeypatch.setenv("ACTION", "build_needs_json")
    monkeypatch.setenv("OUTPUT_DIRECTORY", "outputs/not-created-yet")
    monkeypatch.chdir(workspace)

    # Act
    config = DocsCliConfig.from_environment()

    # Assert
    assert config.output_directory == workspace / "outputs/not-created-yet"
    assert not config.output_directory.exists()
