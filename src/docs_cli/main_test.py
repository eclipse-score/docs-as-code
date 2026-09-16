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
from src.helper_lib import config as config_module
from src.helper_lib.config import DocsCliConfig


@pytest.fixture
def workspace(fs: FFS, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create the minimum Bazel workspace needed by the CLI tests."""

    # The CLI reads its configuration from the process environment, so remove
    # optional values left behind by the test runner before setting the basics.
    ENVIRONMENT_OVERRIDES = (
        "EXTERNAL_NEEDS_FILES",
        "TEST_SOURCES",
        "MOUNTS_MANIFEST",
        "SCORE_SOURCELINKS",
        "SPHINX_CONFIG_FILE",
        "SCORE_METAMODEL_YAML",
        "SPHINX_EXTRA_OPTS",
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
        # BUILD_WORKSPACE_DIRECTORY is available to ``bazel run`` only; leaving
        # it unset lets DocsCliConfig identify this as the build environment.
        monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY")
        monkeypatch.chdir(workspace)
        monkeypatch.setenv("OUTPUT_DIRECTORY", "outputs/needs")
        build_dir = Path("outputs/needs")
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
    # Build actions pass their source and output paths relative to the execroot.
    if action == "build_needs_json":
        assert arguments[:2] == ["docs", str(build_dir)]
        update_hash.assert_not_called()
    else:
        assert arguments[:2] == [str(workspace / "component/docs"), str(build_dir)]
    # The action selects the builder exposed by its public Bazel target.
    assert arguments[-2:] == ["-b", builder]


def test_needs_build_uses_environment_for_file_inputs_and_json_for_other_options(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Needs actions pass file paths separately from Sphinx option overrides."""

    # Arrange
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY")
    monkeypatch.setenv("ACTION", "build_needs_json")
    monkeypatch.setenv("OUTPUT_DIRECTORY", "outputs/needs")
    monkeypatch.chdir(workspace)
    mounts_manifest = Path("bazel-out/k8-fastbuild/bin/pkg/mounts.json")
    source_links = Path("bazel-out/k8-fastbuild/bin/pkg/sourcelinks.json")
    metamodel = Path("bazel-out/k8-fastbuild/bin/pkg/metamodel.yaml")
    monkeypatch.setenv("MOUNTS_MANIFEST", str(mounts_manifest))
    monkeypatch.setenv("SCORE_SOURCELINKS", str(source_links))
    monkeypatch.setenv("SCORE_METAMODEL_YAML", str(metamodel))
    monkeypatch.setenv(
        "SPHINX_EXTRA_OPTS",
        '["--define=master_doc=custom-index", "--define=score_source_code_linker_plain_links=1"]',
    )
    noop_sphinx = Mock(return_value=0)
    monkeypatch.setattr(docs_cli, "sphinx_main", noop_sphinx)
    monkeypatch.setattr(docs_cli, "update_module_hash", Mock())

    # Act
    assert docs_cli.main([]) == 0

    # Assert
    arguments = noop_sphinx.call_args.args[0]
    # The launcher converts the two environment paths that are Sphinx config
    # values into defines; the source-linker consumes its path from the env.
    assert f"--define=mounts_manifest={mounts_manifest}" in arguments
    assert f"--define=score_metamodel_yaml={workspace / metamodel}" in arguments
    assert not any(
        arg.startswith("--define=score_sourcelinks_json=") for arg in arguments
    )
    # Non-path Sphinx overrides retain their JSON transport.
    assert "--define=master_doc=custom-index" in arguments
    assert "--define=score_source_code_linker_plain_links=1" in arguments


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
    monkeypatch.setenv("ACTION", "incremental")

    # Act
    config = DocsCliConfig()
    arguments = sphinx_arguments(config)

    # Assert
    assert config.resolve_input_path(Path("config/conf.py")) == (
        workspace / "runfiles/config/conf.py"
    )
    # Runfile addresses, including external repository short paths, resolve
    # through the config instead of requiring callers to join RUNFILES_DIR.
    assert config.resolve_input_path(
        Path("_main/../vendor+/docs"), runfiles_relative=True
    ) == (workspace / "runfiles/vendor+/docs")
    assert config.relative_to_runfiles(workspace / "runfiles/vendor+/docs") == Path(
        "vendor+/docs"
    )
    # Bazel's execroot-relative output spelling maps to the workspace-visible
    # bazel-bin path in an interactive run.
    assert (
        config.resolve_bazel_output_path("bazel-out/k8-fastbuild/bin/pkg/generated")
        == workspace / "bazel-bin/pkg/generated"
    )
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


def test_direct_invocation_resolves_paths_relative_to_cwd(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    # A direct invocation has neither Bazel's workspace marker nor a runfiles
    # tree. PACKAGE_DIR is a docs.bzl value and must not be needed here.
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY")
    monkeypatch.delenv("PACKAGE_DIR")
    monkeypatch.delenv("RUNFILES_DIR", raising=False)
    monkeypatch.delenv("RUNFILES_MANIFEST_FILE", raising=False)
    monkeypatch.setattr(
        config_module.Runfiles,
        "Create",
        staticmethod(lambda: None),
    )
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("SCORE_METAMODEL_YAML", "metamodel.yaml")
    monkeypatch.setenv("ACTION", "incremental")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

    # Act
    config = DocsCliConfig()
    arguments = sphinx_arguments(config)

    # Assert
    assert config.is_direct
    assert arguments[:2] == ["docs", "_build"]
    # Without Bazel metadata, relative inputs are resolved from cwd.
    assert f"--define=score_metamodel_yaml={workspace}/metamodel.yaml" in arguments
    # A direct invocation has no generated Sphinx config to resolve.
    assert "-c" not in arguments
    # Direct callers do not have BUILD_WORKSPACE_DIRECTORY, so keep their
    # cwd-relative source path instead of trying to relativize it to a workspace.
    assert "-A=doc_path=docs" in arguments


def test_config_defaults_make_all_paths_available_without_launcher_values(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standalone extensions can inspect config without docs.bzl variables."""

    # Arrange
    for name in (
        "ACTION",
        "BUILD_WORKSPACE_DIRECTORY",
        "PACKAGE_DIR",
        "SOURCE_DIRECTORY",
        "OUTPUT_DIRECTORY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("RUNFILES_DIR", raising=False)
    monkeypatch.delenv("RUNFILES_MANIFEST_FILE", raising=False)
    monkeypatch.setattr(
        config_module.Runfiles,
        "Create",
        staticmethod(lambda: None),
    )
    monkeypatch.chdir(workspace)

    # Act
    config = DocsCliConfig()

    # Assert
    assert config.is_direct
    assert config.action is None
    assert config.package_dir == Path()
    assert config.output_dir == Path("_build")


def test_config_finds_ide_support_runfiles_for_direct_invocations(
    workspace: Path,
    fs: FFS,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct Sphinx launched from the IDE venv can still locate Bazel runfiles."""

    # Arrange
    for name in (
        "ACTION",
        "BUILD_WORKSPACE_DIRECTORY",
        "PACKAGE_DIR",
        "RUNFILES_DIR",
        "RUNFILES_MANIFEST_FILE",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        config_module.Runfiles,
        "Create",
        staticmethod(lambda: None),
    )
    monkeypatch.chdir(workspace)
    fs.create_dir(workspace / ".git")
    ide_runfiles_dir = workspace / "bazel-bin/ide_support.runfiles"
    fs.create_dir(ide_runfiles_dir)
    fs.create_file(ide_runfiles_dir / "_main/src/config/conf.py")

    # Act
    config = DocsCliConfig()

    # Assert
    assert config.is_direct
    assert config.uses_ide_support_runfiles
    assert config.resolve_input_path(
        Path("_main/src/config/conf.py"), runfiles_relative=True
    ) == (ide_runfiles_dir / "_main/src/config/conf.py")


def test_config_recovers_execroot_for_runfiles_output_paths(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execroot = workspace / "sandbox/execroot/_main"
    monkeypatch.setenv(
        "RUNFILES_DIR",
        str(execroot / "bazel-out/k8-fastbuild/bin/docs.runfiles"),
    )

    config = DocsCliConfig()

    assert (
        config.resolve_bazel_output_path(
            "bazel-out/k8-fastbuild/bin/pkg/generated/index.rst"
        )
        == execroot / "bazel-out/k8-fastbuild/bin/pkg/generated/index.rst"
    )
