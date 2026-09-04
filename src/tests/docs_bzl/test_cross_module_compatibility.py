# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Black-box coverage for a real Bzlmod documentation-module boundary."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from src.tests.docs_bzl.helpers import repo_root, run_scenario


def _write_cross_module_consumer(
    workspace: Path, compatibility_config: str = ""
) -> None:
    source_root = repo_root()
    fixture = source_root / "src/tests/docs_bzl/cross_module_fixture"
    shutil.copyfile(source_root / ".bazelversion", workspace / ".bazelversion")
    subprocess.run(["git", "init", "--quiet", str(workspace)], check=True)
    workspace.joinpath("MODULE.bazel").write_text(
        f'''module(name = "compatibility_consumer")
bazel_dep(name = "rules_python", version = "1.8.5")
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(is_default = True, python_version = "3.12")
bazel_dep(name = "score_docs_as_code", version = "4.6.0")
local_path_override(module_name = "score_docs_as_code", path = "{source_root}")
bazel_dep(name = "score_docs_compatibility_fixture", version = "0.0.1")
local_path_override(module_name = "score_docs_compatibility_fixture", path = "{fixture}")
''',
        encoding="utf-8",
    )
    workspace.joinpath("BUILD").write_text(
        """load("@score_docs_as_code//:docs.bzl", "docs")
docs(source_dir = "docs", bundles = [{"bundle": "@score_docs_compatibility_fixture//:docs_bundle", "mount_at": "fixture"}])
""",
        encoding="utf-8",
    )
    docs = workspace / "docs"
    docs.mkdir()
    docs.joinpath("conf.py").write_text(
        f"""import os

project = "Cross module compatibility consumer"
project_url = "https://example.invalid/cross-module-consumer"
extensions = ["score_sphinx_bundle"]
score_metamodel_yaml = os.path.join(os.path.dirname(__file__), "metamodel.yaml")
required_in_id = ["host", "fixture"]
{compatibility_config}
""",
        encoding="utf-8",
    )
    docs.joinpath("metamodel.yaml").write_text(
        """needs_types:
  test_req:
    title: Test Requirement
    prefix: test_req__
    parts: 3
    mandatory_options:
      id: ^test_req__[0-9a-zA-Z_]*$
      status: ^(draft|valid)$
      version: ^[0-9]+$
    optional_options:
      tags: .*
      content: .*
      template: .*
    optional_links:
      links: ANY
links: {}
""",
        encoding="utf-8",
    )
    docs.joinpath("index.rst").write_text(
        """Cross module compatibility
==========================

.. toctree::
   :maxdepth: 1

.. test_req:: Host target
   :id: test_req__host__target
   :status: valid
   :version: 2
""",
        encoding="utf-8",
    )


@pytest.mark.bazel_slow
def test_cross_module_version_mismatch_is_reported_without_failing(
    tmp_path: Path,
) -> None:
    _write_cross_module_consumer(
        tmp_path,
        "score_cross_module_compatibility_allow_missing_mandatory_attributes = True\n"
        "score_cross_module_compatibility_allow_version_mismatches = True",
    )
    result = subprocess.run(
        ["bazel", f"--bazelrc={repo_root() / '.bazelrc'}", "run", "//:docs"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Compatibility finding:" in result.stdout
    report = json.loads(
        (tmp_path / "_build/compatibility-findings.json").read_text(encoding="utf-8")
    )
    assert report["summary"] == {"count": 2, "modules": 1}
    findings = report["findings"]
    assert {finding["category"] for finding in findings} == {
        "mandatory-attribute",
        "version-mismatch",
    }
    assert {finding["need_id"] for finding in findings} == {"test_req__fixture__source"}
    version_finding = next(
        finding for finding in findings if finding["category"] == "version-mismatch"
    )
    assert version_finding["target_id"] == "test_req__host__target"

    index = (tmp_path / "_build/index.html").read_text(encoding="utf-8")
    assert "External documentation compatibility findings" in index
    assert (tmp_path / "_build/compatibility-findings.html").is_file()


@pytest.mark.bazel_slow
def test_external_findings_remain_fatal_by_default(tmp_path: Path) -> None:
    _write_cross_module_consumer(tmp_path)
    result = subprocess.run(
        ["bazel", f"--bazelrc={repo_root() / '.bazelrc'}", "run", "//:docs"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "is missing required attribute: `status`" in result.stderr


@pytest.mark.bazel_slow
def test_local_version_mismatch_remains_fatal() -> None:
    result = run_scenario("run", "local_version_mismatch", ":docs", expect_error=True)
    assert "condition 'version==1' not satisfied" in result.stderr
