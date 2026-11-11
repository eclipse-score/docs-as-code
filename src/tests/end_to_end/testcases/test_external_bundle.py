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
"""external_bundle: mount a docs_bundle published by another Bazel module."""

from typing import Any

import pytest

from src.tests.end_to_end.testcases.helpers import (
    load_json,
    load_needs,
    run_scenario,
    toctree_links,
)

SCENARIO = "external_bundle"

# A stable requirement of the mounted @score_process_description bundle.
EXTERNAL_NEED = "gd_req__req_attr_uid"


@pytest.mark.bazel_cached
def test_external_bundle_needs_are_exported_below_its_mount():
    """Needs of the external bundle end up in needs.json below the mount point."""
    result = run_scenario("build", SCENARIO, ":needs_json")
    assert result.artifacts is not None

    needs: dict[str, Any] = load_needs(result.artifacts["needs.json"])
    assert EXTERNAL_NEED in needs
    docnames: set[str] = {need["docname"] for need in needs.values()}
    assert all(docname.startswith("process/") for docname in docnames), docnames


@pytest.mark.bazel_slow
def test_mount_without_attach_to_joins_the_root_toctree():
    """A bundle mounted without attach_to is linked from the root page."""
    result = run_scenario("run", SCENARIO, ":docs")

    html = (result.build_dir / "index.html").read_text(encoding="utf-8")
    assert toctree_links(html) == {"process/index.html": "Process description"}
    assert (result.build_dir / "process" / "index.html").is_file()

    report = load_json(result.build_dir / "compatibility-findings.json")
    assert report["summary"]["count"] == 0
