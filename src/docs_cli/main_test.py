# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem as FFS

from src.docs_cli import cli as docs_cli
from src.docs_cli.cli import sphinx_arguments


def _docs_config(**overrides: object) -> dict[str, object]:
    """Return a complete version-1 payload suitable for CLI unit tests."""
    config: dict[str, object] = {
        "version": 1,
        "action": "incremental",
        "package_directory": "component",
        "source_directory": "docs",
        "output_directory": "_build",
        "config_file": "",
        "external_needs_sources": [],
        "testcase_source_dirs": [],
        "mounts_manifest": None,
        "source_links": None,
        "metamodel": None,
        "known_good": None,
        "master_doc": None,
        "bundle_needs_export": None,
        "plain_links": None,
    }
    config.update(overrides)
    return config


def _set_docs_config(
    monkeypatch: pytest.MonkeyPatch, **overrides: object
) -> dict[str, object]:
    """Install one structured payload and return the decoded fixture value."""
    config = _docs_config(**overrides)
    monkeypatch.setenv("SCORE_DOCS_CONFIG", json.dumps(config))
    return config


@pytest.fixture
def workspace(fs: FFS, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create the minimum Bazel workspace needed by the CLI tests."""

    # Runtime context is intentionally separate from the documentation payload.
    for name in ("GITHUB_REPOSITORY", "RUNFILES_DIR", "RUNFILES_MANIFEST_FILE"):
        monkeypatch.delenv(name, raising=False)

    workspace = Path("/workspace")
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))
    monkeypatch.setenv("RUNFILES_DIR", str(workspace / "runfiles"))
    _set_docs_config(monkeypatch)

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

    _set_docs_config(monkeypatch, action=action)
    build_dir = workspace / "component/_build"
    if action == "build_needs_json":
        # The sandboxed action uses its declared output, not the package cache.
        monkeypatch.chdir(workspace)
        _set_docs_config(
            monkeypatch,
            action=action,
            package_directory="",
            output_directory="outputs/needs",
        )
        build_dir = workspace / "outputs/needs"
    noop_sphinx = Mock(return_value=0)
    update_hash = Mock()
    monkeypatch.setattr(docs_cli, "sphinx_main", noop_sphinx)
    monkeypatch.setattr(docs_cli, "update_module_hash", update_hash)

    exit_code = docs_cli.main([])

    assert exit_code == 0
    noop_sphinx.assert_called_once()
    arguments = noop_sphinx.call_args.args[0]
    if action == "build_needs_json":
        assert arguments[:2] == [str(workspace / "docs"), str(build_dir)]
        update_hash.assert_not_called()
    else:
        assert arguments[:2] == [str(workspace / "component/docs"), str(build_dir)]
    assert arguments[-2:] == ["-b", builder]


def test_failed_build_returns_exit_code_and_forces_next_build_clean(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure without Sphinx warnings must still invalidate partial output."""

    _set_docs_config(monkeypatch, action="incremental")
    build_dir = workspace / "component/_build"

    def failing_sphinx_mock(arguments: list[str]) -> int:
        build_dir.mkdir()
        (build_dir / "partial-output").touch()
        return 2

    monkeypatch.setattr(docs_cli, "sphinx_main", failing_sphinx_mock)

    exit_code = docs_cli.main([])

    assert exit_code == 2
    assert "Build failed with exit code 2" in (build_dir / "warnings.txt").read_text()
    assert not (build_dir / ".module_bazel_hash").exists()

    def rebuild(arguments: list[str]) -> int:
        assert not build_dir.exists()
        build_dir.mkdir()
        return 0

    monkeypatch.setattr(docs_cli, "sphinx_main", rebuild)
    assert docs_cli.main([]) == 0


def test_live_preview_uses_port_and_bundle_watches(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = workspace / "mounts.json"
    manifest.write_text(
        '{"mounts": [{"src_root": "extra/docs", "runtime_path": "extra/docs", "mount_at": "extra"}]}'
    )
    _set_docs_config(monkeypatch, action="live_preview", mounts_manifest=str(manifest))
    autobuild = Mock()
    monkeypatch.setattr(docs_cli, "sphinx_autobuild_main", autobuild)

    exit_code = docs_cli.main(["--port", "42424242424"])

    assert exit_code == 0
    autobuild.assert_called_once()
    arguments = autobuild.call_args.args[0]
    assert "--port=42424242424" in arguments
    assert "--define=skip_rescanning_via_source_code_linker=1" in arguments
    assert arguments[-2:] == ["--watch", str(workspace / "extra/docs")]
    assert not (workspace / "component/_build/.module_bazel_hash").exists()


def test_interactive_configuration_resolves_runfiles_and_preserves_repo_relative_edit_path(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _set_docs_config(
        monkeypatch,
        config_file="config/conf.py",
        metamodel="config/metamodel.yaml",
        source_links="links.json",
        external_needs_sources=[":bundle", "@vendor//:needs"],
        testcase_source_dirs=["src/tests"],
        known_good="baseline.json",
    )
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    package = workspace / "component"

    arguments = sphinx_arguments(
        config,
        workspace,
        package,
        package / "_build",
        workspace / "runfiles",
    )

    expected_arguments = {
        "-c",
        str(workspace / "runfiles/config"),
        f"--define=score_metamodel_yaml={workspace}/runfiles/config/metamodel.yaml",
        f"--define=score_sourcelinks_json={workspace}/runfiles/links.json",
        '--define=external_needs_source=[":bundle", "@vendor//:needs"]',
        '--define=testcase_source_dirs=["src/tests"]',
        "-A=github_user=owner",
        "-A=github_repo=repo",
        "-A=doc_path=component/docs",
        f"--define=KNOWN_GOOD_JSON={workspace}/runfiles/baseline.json",
    }
    assert expected_arguments <= set(arguments)


def test_direct_invocation_resolves_metamodel_relative_to_workspace(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RUNFILES_DIR", raising=False)
    config = _set_docs_config(monkeypatch, metamodel="metamodel.yaml")

    arguments = sphinx_arguments(config, workspace, workspace, workspace / "_build")

    assert f"--define=score_metamodel_yaml={workspace}/metamodel.yaml" in arguments
    assert "-c" not in arguments


def test_sandbox_configuration_resolves_execution_root_paths(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(workspace)
    config = _set_docs_config(
        monkeypatch,
        action="build_needs_json",
        package_directory="",
        source_directory="external/vendor/docs",
        output_directory="bazel-out/k8-fastbuild/bin/needs_json/_build/needs",
        config_file="bazel-out/k8-fastbuild/bin/docs/conf.py",
        source_links="bazel-out/k8-fastbuild/bin/sourcelinks.json",
        metamodel="bazel-out/k8-fastbuild/bin/metamodel.yaml",
        known_good="bazel-out/k8-fastbuild/bin/known_good.json",
    )

    arguments = sphinx_arguments(
        config,
        None,
        workspace,
        workspace / "bazel-out/k8-fastbuild/bin/needs_json/_build/needs",
    )

    assert arguments[:2] == [
        str(workspace / "external/vendor/docs"),
        str(workspace / "bazel-out/k8-fastbuild/bin/needs_json/_build/needs"),
    ]
    assert (
        f"--define=score_sourcelinks_json={workspace}/bazel-out/k8-fastbuild/bin/sourcelinks.json"
        in arguments
    )
    assert (
        f"--define=score_metamodel_yaml={workspace}/bazel-out/k8-fastbuild/bin/metamodel.yaml"
        in arguments
    )
    assert "-c" in arguments
    assert str(workspace / "bazel-out/k8-fastbuild/bin/docs") in arguments


def test_missing_configuration_payload_is_rejected(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SCORE_DOCS_CONFIG", raising=False)

    with pytest.raises(ValueError, match="SCORE_DOCS_CONFIG is not set"):
        docs_cli.main([])


def test_missing_configuration_version_is_rejected(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SCORE_DOCS_CONFIG", json.dumps({"action": "incremental"}))

    with pytest.raises(ValueError, match="missing required field 'version'"):
        docs_cli.main([])


def test_malformed_configuration_json_is_rejected(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SCORE_DOCS_CONFIG", "not-json")

    with pytest.raises(ValueError, match="SCORE_DOCS_CONFIG must contain valid JSON"):
        docs_cli.main([])


@pytest.mark.parametrize("payload", [{"version": 2}, {"version": 0}])
def test_unsupported_configuration_payload_version_is_rejected(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, payload: dict[str, int]
) -> None:
    monkeypatch.setenv("SCORE_DOCS_CONFIG", json.dumps(payload))

    with pytest.raises(ValueError, match="Unsupported SCORE_DOCS_CONFIG version"):
        docs_cli.main([])


def test_shared_sphinx_diagnostics_are_each_emitted_once(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _set_docs_config(monkeypatch)

    arguments = sphinx_arguments(
        config,
        workspace,
        workspace / "component",
        workspace / "component/_build",
        workspace / "runfiles",
    )

    assert arguments.count("-W") == 1
    assert arguments.count("--keep-going") == 1
    assert arguments.count("-T") == 1
