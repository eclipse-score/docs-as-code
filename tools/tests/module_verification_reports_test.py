# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Unit and local integration coverage for the report gallery command."""

from __future__ import annotations

import contextlib
import json
import subprocess
from pathlib import Path

import pytest

from src.helper_lib import find_git_root
from tools.module_verification_reports import (
    DOCS_COMMAND,
    REPORT_DIRECTORY,
    CheckoutManager,
    DownstreamInjection,
    PreparedCheckout,
    Profile,
    ReportToolError,
    RepositoryResult,
    RepositorySpec,
    build_gallery,
    load_profile,
    local_module_override,
    report_need,
    resolve_cache_dir,
    select_repositories,
    validate_module_graph,
)


def test_cache_path_defaults_inside_the_workspace(tmp_path: Path) -> None:
    assert resolve_cache_dir(workspace_root=tmp_path) == (
        tmp_path / ".cache" / "repo-cache"
    )
    assert resolve_cache_dir(tmp_path / "explicit", workspace_root=tmp_path) == (
        tmp_path / "explicit"
    )


def test_profiles_and_filters_are_validated() -> None:
    main = load_profile("main")
    pinned = load_profile("pinned")
    assert [repository.name for repository in main.repositories] == [
        "lifecycle",
        "baselibs",
        "inc_someip_gateway",
        "persistency",
        "time",
    ]
    assert all(repository.revision == "main" for repository in main.repositories)
    assert all(len(repository.revision) == 40 for repository in pinned.repositories)
    assert [
        repository.name
        for repository in select_repositories(main, ["time", "lifecycle"])
    ] == [
        "time",
        "lifecycle",
    ]
    with pytest.raises(ReportToolError, match="at most 5"):
        select_repositories(main, ["lifecycle"] * 6)
    with pytest.raises(ReportToolError, match="only once"):
        select_repositories(main, ["lifecycle", "lifecycle"])


def test_pinned_profile_rejects_non_immutable_revisions(tmp_path: Path) -> None:
    (tmp_path / "module_verification_reports.toml").write_text(
        '[[repositories]]\nname = "lifecycle"\npinned = "main"\n',
        encoding="utf-8",
    )
    with pytest.raises(ReportToolError, match="full SHA"):
        load_profile("pinned", tmp_path)


def test_need_and_module_override_use_the_current_template_selector() -> None:
    page = report_need("inc_someip_gateway")
    assert ":id: doc__inc_someip_gateway_verification_report" in page
    assert ":post_template: mod_ver_report_tiny" in page
    assert ":realizes: wp__verification_module_ver_report" in page
    assert ":belongs_to:" not in page
    assert ":version: 1" in page
    assert "mod_ver_report\n" not in page

    original = """module(name = "consumer")
bazel_dep(name = "score_docs_as_code", version = "7.0.0")
git_override(
    module_name = "score_docs_as_code",
    commit = "deadbeef",
    remote = "https://example.invalid/docs-as-code.git",
)
"""
    updated = local_module_override(original)
    assert "local_path_override(" in updated
    assert 'path = "../docs_as_code"' in updated
    assert "deadbeef" not in updated


def _write_fake_checkout(path: Path, repository: str) -> None:
    path.mkdir(parents=True)
    (path / "MODULE.bazel").write_text(
        'module(name = "fake_consumer")\n'
        'bazel_dep(name = "score_docs_as_code", version = "7.0.0")\n',
        encoding="utf-8",
    )
    (path / "BUILD").write_text(
        'load("@score_docs_as_code//:docs.bzl", "docs")\n'
        'docs(source_dir = "docs", project = "Fake", project_url = "https://example.invalid")\n',
        encoding="utf-8",
    )
    docs = path / "docs"
    docs.mkdir()
    (docs / "index.rst").write_text(
        "Fake consumer\n==============\n\n.. toctree::\n   :maxdepth: 1\n\n",
        encoding="utf-8",
    )
    assert repository


def test_injection_is_reversible(tmp_path: Path) -> None:
    checkout = tmp_path / "consumer"
    _write_fake_checkout(checkout, "lifecycle")
    module_before = (checkout / "MODULE.bazel").read_bytes()
    index_before = (checkout / "docs/index.rst").read_bytes()
    with DownstreamInjection(checkout, "lifecycle", Path(__file__).parents[2]):
        injected = (checkout / "MODULE.bazel").read_text(encoding="utf-8")
        index = (checkout / "docs/index.rst").read_text(encoding="utf-8")
        assert "local_path_override(" in injected
        assert ".. score-docs-as-code: module-verification-report begin" in index
        assert ".. score-docs-as-code: module-verification-report end" in index
        assert (checkout / "docs/module_verification_reports/lifecycle.rst").is_file()
    assert (checkout / "MODULE.bazel").read_bytes() == module_before
    assert (checkout / "docs/index.rst").read_bytes() == index_before
    assert not (checkout / "docs/module_verification_reports").exists()


def test_missing_graph_is_a_structural_failure() -> None:
    with pytest.raises(ReportToolError, match="no includes graph"):
        validate_module_graph({"mod__lifecycle": {"id": "mod__lifecycle"}}, "lifecycle")


def test_component_without_a_feature_link_is_a_structural_failure() -> None:
    with pytest.raises(ReportToolError, match="has no belongs_to feature"):
        validate_module_graph(
            {
                "mod__lifecycle": {"includes": ["comp__lifecycle"]},
                "comp__lifecycle": {},
            },
            "lifecycle",
        )


def test_feature_resolved_only_through_external_needs_is_not_a_failure() -> None:
    """A component may point at a feature that lives in another repository's
    needs.json (e.g. score_platform), reached only through Sphinx-needs'
    ``external_needs``. That feature never appears in this repository's own
    needs.json, but Sphinx-needs already validated the link during the docs
    build, so it must not be treated as a structural failure here.
    """

    validate_module_graph(
        {
            "mod__lifecycle": {"includes": ["comp__lifecycle"]},
            "comp__lifecycle": {"belongs_to": ["feat__lifecycle"]},
        },
        "lifecycle",
    )


class _GitCommandRecorder:
    def __init__(self, checkout: Path, *, origin: str) -> None:
        self.checkout = checkout
        self.origin = origin
        self.commands: list[list[str]] = []
        self.revisions = iter(["b" * 40, "a" * 40])

    def __call__(
        self, command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        if command[:3] == ["gh", "repo", "clone"]:
            self.checkout.mkdir(parents=True, exist_ok=True)
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1:] == ["remote", "get-url", "origin"]:
            return subprocess.CompletedProcess(command, 0, self.origin + "\n", "")
        if command[1:] == ["rev-parse", "--verify", "HEAD^{commit}"]:
            return subprocess.CompletedProcess(
                command, 0, next(self.revisions) + "\n", ""
            )
        return subprocess.CompletedProcess(command, 0, "", "")


def test_checkout_clone_refresh_pinned_selection_and_cleanup(tmp_path: Path) -> None:
    source_root = Path(__file__).parents[2]
    cache = tmp_path / "cache"
    spec = RepositorySpec("lifecycle", "a" * 40)
    checkout = cache / "eclipse-score/lifecycle"
    recorder = _GitCommandRecorder(
        checkout, origin="git@github.com:eclipse-score/lifecycle.git"
    )
    manager = CheckoutManager(cache, source_root, runner=recorder)
    with manager.checkout(spec) as prepared:
        assert prepared.default_revision == "b" * 40
        assert prepared.resolved_revision == "a" * 40
    assert any(command[:3] == ["gh", "repo", "clone"] for command in recorder.commands)
    assert ["git", "fetch", "--depth=1", "origin", "main"] in recorder.commands
    assert ["git", "fetch", "--depth=1", "origin", "a" * 40] in recorder.commands
    assert ["git", "checkout", "--detach", "--force", "b" * 40] in recorder.commands
    assert manager.lock_path("lifecycle").parent.name == "score-docs-as-code"


def test_cached_checkout_rejects_a_remote_mismatch(tmp_path: Path) -> None:
    checkout = tmp_path / "cache/eclipse-score/lifecycle"
    checkout.mkdir(parents=True)
    recorder = _GitCommandRecorder(checkout, origin="https://example.invalid/other.git")
    manager = CheckoutManager(
        tmp_path / "cache", Path(__file__).parents[2], runner=recorder
    )
    with (
        pytest.raises(ReportToolError, match="origin mismatch"),
        manager.checkout(RepositorySpec("lifecycle", "main")),
    ):
        pass


def _fake_result(
    returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(DOCS_COMMAND), returncode, stdout, stderr)


def test_local_fake_downstream_build_populates_gallery_and_assets(
    tmp_path: Path,
) -> None:
    source_root = Path(__file__).parents[2]
    checkout = tmp_path / "lifecycle"
    _write_fake_checkout(checkout, "lifecycle")
    output = tmp_path / "gallery"
    spec = RepositorySpec("lifecycle", "main")
    profile = Profile("main", (spec,))

    @contextlib.contextmanager
    def fake_checkout(_spec: RepositorySpec):
        yield PreparedCheckout(spec, checkout, "a" * 40, "a" * 40)

    def fake_command(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        assert command == list(DOCS_COMMAND)
        build = checkout / "_build"
        (build / "module_verification_reports").mkdir(parents=True)
        (build / "module_verification_reports/lifecycle.html").write_text(
            "<html>fake report</html>\n", encoding="utf-8"
        )
        (build / "_static").mkdir()
        (build / "_static/site.css").write_text("body {}\n", encoding="utf-8")
        needs = {
            "versions": {
                "1.0": {
                    "needs": {
                        "mod__lifecycle": {"includes": ["comp__lifecycle"]},
                        "comp__lifecycle": {"belongs_to": ["feat__lifecycle"]},
                        "feat__lifecycle": {"title": "Lifecycle"},
                    }
                }
            }
        }
        (build / "needs.json").write_text(json.dumps(needs), encoding="utf-8")
        return _fake_result()

    results, strict_failure = build_gallery(
        profile,
        (spec,),
        source_root=source_root,
        output_dir=output,
        cache_dir=tmp_path / "cache",
        checkout_factory=fake_checkout,
        command_runner=fake_command,
    )
    assert not strict_failure
    assert results[0].status == "success"
    assert (output / "lifecycle/report.html").read_text(encoding="utf-8") == (
        "<html>fake report</html>\n"
    )
    assert (output / "_static/site.css").is_file()
    assert json.loads((output / "manifest.json").read_text())["repositories"][0][
        "report_path"
    ] == ("lifecycle/report.html")


def test_local_fake_downstream_runs_the_real_docs_target(tmp_path: Path) -> None:
    """Exercise injection and a real Bazel/Sphinx build without network access."""

    source_root = find_git_root()
    if source_root is None:
        pytest.skip("a real workspace checkout is required for the nested Bazel smoke")
    checkout = tmp_path / "lifecycle"
    _write_fake_checkout(checkout, "lifecycle")
    # Reuse the repository's docs-as-code fixture through its public external
    # macro.  The fake checkout remains the Bazel workspace and all inputs are
    # local; the test needs no downstream clone or network access.
    (checkout / "BUILD").write_text(
        'load("@score_docs_as_code//:docs.bzl", "docs")\n'
        'docs(source_dir = "docs", metamodel = "docs/metamodel.yaml", '
        'project = "Fake", project_url = "https://example.invalid")\n',
        encoding="utf-8",
    )
    (checkout / "docs/metamodel.yaml").write_text(
        """needs_types:
  feat:
    title: Feature
    prefix: feat__
    parts: 2
    mandatory_options:
      id: ^feat__.*$
      security: ^(YES|NO)$
      safety: ^(QM|ASIL_B)$
      status: ^(valid|invalid)$
      version: ^[0-9]+$
    optional_options:
      tags: .*
      content: .*
      template: .*
  comp:
    title: Component
    prefix: comp__
    parts: 2
    mandatory_options:
      id: ^comp__.*$
      security: ^(YES|NO)$
      safety: ^(QM|ASIL_B)$
      status: ^(valid|invalid)$
      version: ^[0-9]+$
    mandatory_links:
      belongs_to: feat
    optional_options:
      tags: .*
      content: .*
      template: .*
  mod:
    title: Module
    prefix: mod__
    parts: 2
    mandatory_options:
      id: ^mod__.*$
      security: ^(YES|NO)$
      safety: ^(QM|ASIL_B)$
      status: ^(valid|invalid)$
      version: ^[0-9]+$
    mandatory_links:
      includes: comp
    optional_options:
      tags: .*
      content: .*
      template: .*
  workproduct:
    title: Workproduct
    prefix: wp__
    parts: 2
    mandatory_options:
      id: ^wp__.*$
      status: ^(valid|draft)$
      version: ^[0-9]+$
    optional_options:
      tags: .*
      content: .*
      template: .*
  document:
    title: Generic Document
    prefix: doc__
    parts: 2
    mandatory_options:
      status: ^(valid|draft|invalid)$
      safety: ^(QM|ASIL_B)$
      security: ^(YES|NO)$
      version: ^[0-9]+$
    mandatory_links:
      realizes: workproduct
    optional_options:
      tags: .*
      content: .*
      template: .*
links: {}
needs_extra_links:
  belongs_to:
    incoming: has
    outgoing: belongs to
  includes:
    incoming: included by
    outgoing: includes
  realizes:
    incoming: realized by
    outgoing: realizes
""",
        encoding="utf-8",
    )
    (checkout / ".bazelversion").write_bytes(
        (source_root / ".bazelversion").read_bytes()
    )
    (checkout / ".bazelrc").write_bytes((source_root / ".bazelrc").read_bytes())
    # A real downstream clone always carries its own committed lockfile;
    # incremental.py hashes it unconditionally as a build-cache sentinel.
    (checkout / "MODULE.bazel.lock").write_text("{}\n", encoding="utf-8")
    (checkout / "MODULE.bazel").write_text(
        'module(name = "fake_report_consumer")\n'
        'bazel_dep(name = "rules_python", version = "1.8.5")\n'
        'python = use_extension("@rules_python//python/extensions:python.bzl", "python")\n'
        'python.toolchain(is_default = True, python_version = "3.12")\n'
        'bazel_dep(name = "sphinxdocs", version = "2.2.0")\n'
        'bazel_dep(name = "aspect_rules_py", version = "1.4.0")\n'
        'bazel_dep(name = "buildifier_prebuilt", version = "8.2.0.2")\n'
        'bazel_dep(name = "rules_java", version = "8.15.1")\n'
        'bazel_dep(name = "score_process_description", version = "2.1.2")\n'
        'bazel_dep(name = "score_devcontainer", version = "1.11.0")\n'
        'bazel_dep(name = "score_docs_as_code", version = "4.6.0")\n',
        encoding="utf-8",
    )
    (checkout / "docs/index.rst").write_text(
        """Fake report consumer
=====================

.. toctree::
   :maxdepth: 1

.. feat:: Lifecycle Feature
   :id: feat__lifecycle
   :security: YES
   :safety: ASIL_B
   :status: valid
   :version: 1

.. comp:: Lifecycle Component
   :id: comp__lifecycle
   :security: YES
   :safety: ASIL_B
   :status: valid
   :belongs_to: feat__lifecycle
   :version: 1

.. mod:: Lifecycle Module
   :id: mod__lifecycle
   :security: YES
   :safety: ASIL_B
   :status: valid
   :includes: comp__lifecycle
   :version: 1

.. workproduct:: Requirements Inspection
   :id: wp__requirements_inspect
   :status: valid
   :version: 1

.. workproduct:: Architecture Inspection
   :id: wp__sw_arch_verification
   :status: valid
   :version: 1

.. workproduct:: Implementation Inspection
   :id: wp__sw_implementation_inspection
   :status: valid
   :version: 1

.. workproduct:: DFA
   :id: wp__sw_component_dfa
   :status: valid
   :version: 1

.. workproduct:: FMEA
   :id: wp__sw_component_fmea
   :status: valid
   :version: 1

.. workproduct:: Module Verification Report
   :id: wp__verification_module_ver_report
   :status: valid
   :version: 1
""",
        encoding="utf-8",
    )
    (checkout / "docs/conf.py").write_text(
        "project = 'Fake'\n"
        "project_url = 'https://example.invalid'\n"
        "version = '0.0.0'\n"
        "required_in_id = ['lifecycle']\n"
        "extensions = ['score_sphinx_bundle']\n",
        encoding="utf-8",
    )
    # A few docs extensions use the workspace Git root to compute source
    # links.  A disposable empty repository gives the fake checkout the same
    # local-workspace contract as a real downstream clone.
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(checkout)],
        check=True,
        text=True,
        capture_output=True,
    )
    spec = RepositorySpec("lifecycle", "main")
    profile = Profile("main", (spec,))

    @contextlib.contextmanager
    def fake_checkout(_spec: RepositorySpec):
        yield PreparedCheckout(spec, checkout, "a" * 40, "a" * 40)

    def real_docs_command(
        command: list[str], *, cwd: Path, **_: object
    ) -> subprocess.CompletedProcess[str]:
        assert command == list(DOCS_COMMAND)
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    results, strict_failure = build_gallery(
        profile,
        (spec,),
        source_root=source_root,
        output_dir=tmp_path / "gallery",
        cache_dir=tmp_path / "cache",
        checkout_factory=fake_checkout,
        command_runner=real_docs_command,
    )
    assert not strict_failure
    assert results[0].status == "success", results[0].details
    assert (tmp_path / "gallery/lifecycle/report.html").is_file()


def test_main_is_partial_but_pinned_is_strict_on_build_failure(tmp_path: Path) -> None:
    source_root = Path(__file__).parents[2]
    specs = (RepositorySpec("lifecycle", "main"), RepositorySpec("baselibs", "main"))

    def run(
        profile_name: str, revision: str, output: Path
    ) -> tuple[list[RepositoryResult], bool]:
        profile = Profile(
            profile_name, tuple(RepositorySpec(spec.name, revision) for spec in specs)
        )

        @contextlib.contextmanager
        def fake_checkout(spec: RepositorySpec):
            checkout = tmp_path / f"{profile_name}-{spec.name}"
            _write_fake_checkout(checkout, spec.name)
            yield PreparedCheckout(spec, checkout, "b" * 40, "b" * 40)

        def partially_failing_command(
            command: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            assert command == list(DOCS_COMMAND)
            checkout_path = kwargs["cwd"]
            assert isinstance(checkout_path, Path)
            if checkout_path.name.endswith("lifecycle"):
                build = checkout_path / "_build"
                (build / REPORT_DIRECTORY).mkdir(parents=True)
                (build / f"{REPORT_DIRECTORY}/lifecycle.html").write_bytes(
                    b"successful report\n"
                )
                (build / "needs.json").write_text(
                    json.dumps(
                        {
                            "versions": {
                                "1": {
                                    "needs": {
                                        "mod__lifecycle": {
                                            "includes": ["comp__lifecycle"]
                                        },
                                        "comp__lifecycle": {
                                            "belongs_to": ["feat__lifecycle"]
                                        },
                                        "feat__lifecycle": {},
                                    }
                                }
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                return _fake_result()
            return _fake_result(1, stderr="intentional build failure")

        return build_gallery(
            profile,
            specs,
            source_root=source_root,
            output_dir=output,
            cache_dir=tmp_path / "cache",
            checkout_factory=fake_checkout,
            command_runner=partially_failing_command,
        )

    main_results, main_strict = run("main", "main", tmp_path / "main-gallery")
    pinned_results, pinned_strict = run("pinned", "a" * 40, tmp_path / "pinned-gallery")
    assert [result.status for result in main_results] == ["success", "failure"]
    assert (tmp_path / "main-gallery/lifecycle/report.html").is_file()
    assert not main_strict
    assert [result.status for result in pinned_results] == ["success", "failure"]
    assert (tmp_path / "pinned-gallery/lifecycle/report.html").is_file()
    assert pinned_strict


def test_pinned_golden_comparison_is_byte_for_byte(tmp_path: Path) -> None:
    source_root = Path(__file__).parents[2]
    checkout = tmp_path / "lifecycle"
    _write_fake_checkout(checkout, "lifecycle")
    spec = RepositorySpec("lifecycle", "a" * 40)
    profile = Profile("pinned", (spec,))

    @contextlib.contextmanager
    def fake_checkout(_spec: RepositorySpec):
        yield PreparedCheckout(spec, checkout, "a" * 40, "a" * 40)

    def fake_command(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        build = checkout / "_build"
        (build / "module_verification_reports").mkdir(parents=True)
        (build / "module_verification_reports/lifecycle.html").write_bytes(b"report\n")
        (build / "needs.json").write_text(
            json.dumps(
                {
                    "versions": {
                        "1": {
                            "needs": {
                                "mod__lifecycle": {"includes": ["comp__lifecycle"]},
                                "comp__lifecycle": {"belongs_to": ["feat__lifecycle"]},
                                "feat__lifecycle": {},
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return _fake_result()

    golden_root = tmp_path / "goldens"
    golden = golden_root / "pinned/lifecycle/report.html"
    golden.parent.mkdir(parents=True)
    golden.write_bytes(b"different\n")
    results, strict = build_gallery(
        profile,
        (spec,),
        source_root=source_root,
        output_dir=tmp_path / "gallery",
        cache_dir=tmp_path / "cache",
        golden_root=golden_root,
        check_goldens=True,
        checkout_factory=fake_checkout,
        command_runner=fake_command,
    )
    assert results[0].status == "failure"
    assert "golden mismatch" in results[0].details
    assert strict
