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

"""App-level tests for the merge tool using needs.json from Sphinx."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import cast

import pytest
from sphinx.testing.util import SphinxTestApp

from scripts_bazel.merge_needs_json import merge_needs_json

REPO_ROOT = Path(__file__).absolute().parents[2]
SCENARIOS_DIR = REPO_ROOT / "src/tests/docs_bzl/scenarios"


def _single_version_needs(needs_json: Path) -> tuple[str, dict[str, object]]:
    data = json.loads(needs_json.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    raw_versions = cast(object, data["versions"])
    assert isinstance(raw_versions, dict)
    versions = cast(dict[str, object], raw_versions)
    assert len(versions) == 1

    version_key, raw_version_object = next(iter(versions.items()))
    assert isinstance(raw_version_object, dict)
    version_data = cast(dict[str, object], raw_version_object)
    raw_needs = version_data.get("needs")
    assert isinstance(raw_needs, dict)
    return version_key, cast(dict[str, object], raw_needs)


def _write_conf(
    source_dir: Path,
    *,
    project: str,
    project_url: str,
    version: str | None = None,
    producer_type: bool = False,
) -> None:
    config = [
        f"project = {project!r}",
        f"project_url = {project_url!r}",
        'extensions = ["sphinx_needs"]',
        "needs_id_regex = r'^[A-Za-z0-9_-]{6,}'",
    ]
    if version is not None:
        config.append(f"version = {version!r}")
    if producer_type:
        config.append(
            "needs_types = [{"
            "'directive': 'test_req', "
            "'title': 'Test Requirement', "
            "'prefix': 'test_req__', "
            "'parts': 3, "
            "'mandatory_options': {"
            "'id': r'^test_req__[0-9a-zA-Z_]*$', "
            "'status': r'^(draft|valid)$'}, "
            "'optional_options': {'tags': '.*', 'content': '.*', "
            "'template': '.*'}, "
            "'mandatory_links': {}, "
            "'optional_links': {}}]"
        )

    source_dir.joinpath("conf.py").write_text(
        "\n".join(config) + "\n",
        encoding="utf-8",
    )


def _build_needs_json(
    source_dir: Path,
    build_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    app = SphinxTestApp(
        buildername="needs",
        srcdir=source_dir,
        builddir=build_dir,
        freshenv=True,
        warningiserror=True,
    )
    monkeypatch.chdir(source_dir)
    try:
        app.build()
    finally:
        app.cleanup()

    needs_json = build_dir / "needs" / "needs.json"
    assert needs_json.is_file(), f"Sphinx did not create {needs_json}"
    return needs_json


def test_merges_needs_json_generated_by_sphinx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    basic_source = tmp_path / "basic_docs"
    shutil.copytree(SCENARIOS_DIR / "basic_docs" / "docs", basic_source)
    _write_conf(
        basic_source,
        project="Basic Test",
        project_url="https://github.com/eclipse-score/docs-as-code",
        version="0.0.0",
    )

    producer_source = tmp_path / "producer"
    shutil.copytree(
        SCENARIOS_DIR / "external_needs" / "producer" / "docs",
        producer_source,
    )
    _write_conf(
        producer_source,
        project="External Needs Producer",
        project_url="https://example.invalid/external-needs-producer",
        version="main",
        producer_type=True,
    )

    empty_source = tmp_path / "empty"
    shutil.copytree(
        SCENARIOS_DIR / "nested_bundles" / "host_docs",
        empty_source,
    )
    _write_conf(
        empty_source,
        project="Mount contract fixture",
        project_url="https://example.invalid/mount-contract",
    )

    basic_needs_json = _build_needs_json(
        basic_source, tmp_path / "basic_out", monkeypatch
    )
    producer_needs_json = _build_needs_json(
        producer_source, tmp_path / "producer_out", monkeypatch
    )
    empty_needs_json = _build_needs_json(
        empty_source, tmp_path / "empty_out", monkeypatch
    )

    basic_version, basic_needs = _single_version_needs(basic_needs_json)
    producer_version, producer_needs = _single_version_needs(producer_needs_json)
    empty_version, empty_needs = _single_version_needs(empty_needs_json)

    assert basic_version == "0.0.0"
    assert producer_version == "main"
    assert empty_version == ""
    assert basic_needs == {}
    assert empty_needs == {}
    assert set(producer_needs) == {"test_req__producer__demo"}

    merged = merge_needs_json([basic_needs_json, producer_needs_json, empty_needs_json])
    raw_merged_versions = merged["versions"]
    assert isinstance(raw_merged_versions, dict)
    merged_versions = cast(dict[str, object], raw_merged_versions)
    assert set(merged_versions) == {basic_version}

    raw_merged_version = merged_versions[basic_version]
    assert isinstance(raw_merged_version, dict)
    merged_version = cast(dict[str, object], raw_merged_version)
    raw_merged_needs = merged_version["needs"]
    assert isinstance(raw_merged_needs, dict)
    merged_needs = cast(dict[str, object], raw_merged_needs)
    assert set(merged_needs) == set(producer_needs)
    assert merged_version["needs_amount"] == len(merged_needs)

    # Top-level metadata remains owned by the first input.
    assert merged["project"] == "Basic Test"
