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
"""End-to-end test for a documentation build with a mounted bundle."""

import json
from pathlib import Path

from src.tests.docs_e2e.support import run_docs_build, runfile


def test_docs_build_mounts_bundle_and_extends_toctree(tmp_path: Path):
    """A nested bundle keeps its placement and becomes part of the host site."""
    mounts_manifest = runfile("FIXTURE_MOUNTS_MANIFEST")
    manifest = json.loads(mounts_manifest.read_text(encoding="utf-8"))
    assert [mount["mount_at"] for mount in manifest["mounts"]] == [
        "concepts/example_bundle",
        "concepts/example_bundle/child",
    ]
    assert [mount["entry_doc"] for mount in manifest["mounts"]] == [
        "index",
        "landing",
    ]
    sourcelinks = json.loads(runfile("FIXTURE_SOURCELINKS").read_text(encoding="utf-8"))
    assert sourcelinks == [
        {
            "file": "src/tests/mounts_contract/child/example.py",
            "line": 14,
            "tag": "# req-traceability:",
            "need": "REQ_CHILD",
            "full_line": "# req-traceability: REQ_CHILD",
            "repo_name": "local_repo",
            "hash": "",
            "url": "",
        }
    ]

    result = run_docs_build(
        tmp_path,
        docs_binary=runfile("FIXTURE_DOCS_BINARY"),
        source_dir=runfile("HOST_DOCS_CONF").parent,
        mounts_manifest=mounts_manifest,
        sourcelinks=runfile("FIXTURE_SOURCELINKS"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "extended toctree #0 in 'concepts/index'" in result.stdout
    assert (
        tmp_path / "_build" / "concepts" / "example_bundle" / "index.html"
    ).is_file()
    assert (
        tmp_path / "_build" / "concepts" / "example_bundle" / "child" / "landing.html"
    ).is_file()
    toml = (tmp_path / "docs" / "ubproject.toml").read_text(encoding="utf-8")
    assert 'mount_at = "concepts/example_bundle"' in toml
    assert 'mount_at = "concepts/example_bundle/child"' in toml


def test_pure_aggregator_keeps_declared_mount_order():
    """An aggregator contributes no implicit package sources or reordered mounts."""
    manifest = json.loads(
        runfile("ORDERED_AGGREGATE_MANIFEST").read_text(encoding="utf-8")
    )
    assert [mount["mount_at"] for mount in manifest["mounts"]] == [
        "first",
        "second",
    ]
