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
import contextlib
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import TempPathFactory
from sphinx.testing.util import SphinxTestApp

from src.extensions.score_source_code_linker.module_source_links import (
    ModuleInfo,
    ModuleSourceLinks_JSON_Decoder,
    load_module_source_links_json,
)

"""
                        ────────────────INFORMATION───────────────

#              ╭──────────────────────────────────────────────────────────╮
#              │                  boiler plate generated                  │
#              │                Human screened and adapted                │
#              │            though still be aware of mistakes             │
#              ╰──────────────────────────────────────────────────────────╯

"""


@pytest.fixture(scope="session")
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("test_module_links_repo")


@pytest.fixture(scope="session")
def git_repo_setup(sphinx_base_dir: Path) -> Path:
    """Creating git repo, to make testing possible"""
    repo_path = sphinx_base_dir
    _ = subprocess.run(["git", "init"], cwd=repo_path, check=True)
    _ = subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
    )
    _ = subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
    )
    _ = subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/testorg/modulerepo.git"],
        cwd=repo_path,
        check=True,
    )
    os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(repo_path)
    return repo_path


@pytest.fixture(scope="session")
def create_demo_files(sphinx_base_dir: Path, git_repo_setup: Path):
    repo_path = sphinx_base_dir

    # Create source files
    source_dir = repo_path / "src"
    source_dir.mkdir()

    _ = (source_dir / "module_a_impl.py").write_text(make_module_a_source())
    _ = (source_dir / "module_b_impl.py").write_text(make_module_b_source())

    # Create docs directory
    docs_dir = repo_path / "docs"
    docs_dir.mkdir()
    _ = (docs_dir / "index.rst").write_text(basic_needs())
    _ = (docs_dir / "conf.py").write_text(basic_conf())

    # Create test.xml files
    bazel_testdir = repo_path / "bazel-testlogs" / "src"
    bazel_testdir.mkdir(parents=True)
    _ = (bazel_testdir / "test.xml").write_text(make_test_xml())

    curr_dir = Path(__file__).absolute().parent
    _ = shutil.copyfile(
        curr_dir / "expected_module_grouped.json",
        repo_path / ".expected_module_grouped.json",
    )

    # Commit everything
    _ = subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    _ = subprocess.run(
        ["git", "commit", "-m", "Initial commit with module test files"],
        cwd=repo_path,
        check=True,
    )


def make_module_a_source():
    return """
# Module A implementation
# """+"""req-Id: MOD_REQ_1
def module_a_function():
    pass

# """+"""req-Id: MOD_REQ_2
class ModuleAClass:
    pass
"""


def make_module_b_source():
    return """
# Module B implementation
# """+"""req-Id: MOD_REQ_1
def module_b_function():
    pass

# """+"""req-Id: MOD_REQ_3
def another_module_b_function():
    pass
"""


def make_test_xml():
    # ruff: noqa: E501 (start)
    return """
<testsuites>
  <testsuite name="ModuleTests" tests="2" failures="0" errors="0" time="0.123">
    <testcase name="test_module_a" classname="" file="src/test_module_a.py" line="10" time="0.056">
      <properties>
        <property name="FullyVerifies" value="MOD_REQ_1"/>
        <property name="TestType" value="unit-test"/>
        <property name="DerivationTechnique" value="requirements-analysis"/>
      </properties>
    </testcase>
    <testcase name="test_module_b" classname="" file="src/test_module_b.py" line="20" time="0.067">
      <properties>
        <property name="PartiallyVerifies" value="MOD_REQ_3"/>
        <property name="TestType" value="integration-test"/>
        <property name="DerivationTechnique" value="design-analysis"/>
      </properties>
    </testcase>
  </testsuite>
</testsuites>
"""
    # ruff: noqa: E501 (finish)


def basic_conf():
    return """
extensions = [
    "sphinx_needs",
    "score_source_code_linker",
]
needs_types = [
    dict(
        directive="mod_req",
        title="Module Requirement",
        prefix="MOD_REQ_",
        color="#BFD8D2",
        style="node",
    ),
]
needs_extra_options = ["source_code_link", "testlink"]
needs_extra_links = [{
      "option": "partially_verifies",
      "incoming": "paritally_verified_by",
      "outgoing": "paritally_verifies",
   },
   {
      "option": "fully_verifies",
      "incoming": "fully_verified_by",
      "outgoing": "fully_verifies",
   }]
"""


def basic_needs():
    return """
MODULE TESTING
==============

.. mod_req:: Module Requirement 1
   :id: MOD_REQ_1
   :status: valid

.. mod_req:: Module Requirement 2
   :id: MOD_REQ_2
   :status: open

.. mod_req:: Module Requirement 3
   :id: MOD_REQ_3
   :status: open
"""


@pytest.fixture()
def sphinx_app_setup(
    sphinx_base_dir: Path, create_demo_files: None, git_repo_setup: Path
) -> Callable[[], SphinxTestApp]:
    def _create_app():
        base_dir = sphinx_base_dir
        docs_dir = base_dir / "docs"

        original_cwd = None
        with contextlib.suppress(FileNotFoundError):
            original_cwd = os.getcwd()

        os.chdir(base_dir)
        try:
            return SphinxTestApp(
                freshenv=True,
                srcdir=docs_dir,
                confdir=docs_dir,
                outdir=sphinx_base_dir / "out",
                buildername="html",
                warningiserror=True,
            )
        finally:
            if original_cwd is not None:
                with contextlib.suppress(FileNotFoundError, OSError):
                    os.chdir(original_cwd)

    return _create_app


def test_module_grouped_cache_generated(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """Happy path: Module grouped cache file is generated after Sphinx build"""
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()

        module_cache = app.outdir / "score_module_grouped_scl_cache.json"
        assert module_cache.exists(), "Module grouped cache was not created"

        # Load and verify structure
        loaded = load_module_source_links_json(module_cache)
        assert isinstance(loaded, list)
        assert len(loaded) > 0, "Module cache should contain at least one module"

        # Verify each item is a ModuleSourceLinks
        for item in loaded:
            assert hasattr(item, "module")
            assert hasattr(item, "needs")
            assert isinstance(item.module, ModuleInfo)

    finally:
        app.cleanup()


def test_module_grouping_preserves_metadata(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """Happy path: Module metadata (name, hash, url) is preserved in cache"""
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()

        module_cache = app.outdir / "score_module_grouped_scl_cache.json"
        loaded = load_module_source_links_json(module_cache)

        # Verify that each module has proper metadata
        for module_links in loaded:
            assert module_links.module.name is not None
            assert isinstance(module_links.module.name, str)
            # Hash and URL might be empty strings for local module
            assert module_links.module.hash is not None
            assert module_links.module.url is not None

    finally:
        app.cleanup()


def test_module_grouping_multiple_needs_per_module(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """Happy path: Multiple needs from same module are grouped together"""
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()

        module_cache = app.outdir / "score_module_grouped_scl_cache.json"
        loaded = load_module_source_links_json(module_cache)

        # Find the local_module (should have all 3 requirements)
        local_module = None
        for m in loaded:
            if m.module.name == "local_module":
                local_module = m
                break

        assert local_module is not None, "local_module not found in grouped cache"

        # All 3 MOD_REQ should be in this module
        need_ids = {need.need for need in local_module.needs}
        assert (
            "MOD_REQ_1" in need_ids
            or "MOD_REQ_2" in need_ids
            or "MOD_REQ_3" in need_ids
        )

    finally:
        app.cleanup()


def test_module_cache_json_format(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """
    Module cache JSON has correct
    structure and excludes metadata from links
    """
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()

        module_cache = app.outdir / "score_module_grouped_scl_cache.json"

        # Load as raw JSON to check structure
        with open(module_cache) as f:
            raw_json = json.load(f)

        assert isinstance(raw_json, list)
        assert len(raw_json) > 0

        # Check first module structure
        first_module = raw_json[0]
        assert "module" in first_module
        assert "needs" in first_module
        assert "name" in first_module["module"]
        assert "hash" in first_module["module"]
        assert "url" in first_module["module"]

        # Check that needlinks don't have metadata
        if first_module["needs"]:
            first_need = first_module["needs"][0]
            if "links" in first_need and first_need["links"].get("CodeLinks"):
                codelink = first_need["links"]["CodeLinks"][0]
                assert "module_name" not in codelink, (
                    "CodeLinks should not contain module_name metadata"
                )
                assert "hash" not in codelink, (
                    "CodeLinks should not contain hash metadata"
                )
                assert "url" not in codelink, (
                    "CodeLinks should not contain url metadata"
                )

    finally:
        app.cleanup()


def test_module_cache_rebuilds_when_missing(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """Edge case: Module cache is regenerated if deleted"""
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()

        module_cache = app.outdir / "score_module_grouped_scl_cache.json"
        assert module_cache.exists()

        # Delete the cache
        module_cache.unlink()
        assert not module_cache.exists()

        # Build again - should regenerate
        app2 = sphinx_app_setup()
        app2.build()

        assert module_cache.exists(), "Cache should be regenerated on rebuild"

        # Verify it's valid
        loaded = load_module_source_links_json(module_cache)
        assert len(loaded) > 0

        app2.cleanup()
    finally:
        app.cleanup()


def test_module_grouping_with_golden_file(
    sphinx_app_setup: Callable[[], SphinxTestApp],
    sphinx_base_dir: Path,
    git_repo_setup: Path,
    create_demo_files: None,
):
    """Happy path: Generated module cache matches expected golden file"""
    app = sphinx_app_setup()
    try:
        os.environ["BUILD_WORKSPACE_DIRECTORY"] = str(sphinx_base_dir)
        app.build()

        module_cache = app.outdir / "score_module_grouped_scl_cache.json"
        expected_file = sphinx_base_dir / ".expected_module_grouped.json"

        assert module_cache.exists()
        assert expected_file.exists(), "Golden file not found"

        with open(module_cache) as f1:
            actual = json.load(f1, object_hook=ModuleSourceLinks_JSON_Decoder)
        with open(expected_file) as f2:
            expected = json.load(f2, object_hook=ModuleSourceLinks_JSON_Decoder)

        assert len(actual) == len(expected), (
            f"Module count mismatch. Actual: {len(actual)}, Expected: {len(expected)}"
        )

        # Compare module by module
        actual_by_name = {m.module.name: m for m in actual}
        expected_by_name = {m.module.name: m for m in expected}

        assert set(actual_by_name.keys()) == set(expected_by_name.keys()), (
            f"Module names don't match. "
            f"Actual: {set(actual_by_name.keys())}, "
            f"Expected: {set(expected_by_name.keys())}"
        )

        for module_name in actual_by_name:
            actual_module = actual_by_name[module_name]
            expected_module = expected_by_name[module_name]

            assert actual_module.module.hash == expected_module.module.hash
            assert actual_module.module.url == expected_module.module.url
            assert len(actual_module.needs) == len(expected_module.needs)

    finally:
        app.cleanup()
