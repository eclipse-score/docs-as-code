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

"""
end-to-end tests for the public docs() macro.
See README.md in this directory for usage instructions.
"""

from pathlib import Path

from src.tests.docs_bzl.helpers import (
    load_needs,
    run_fixture,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_basic_docs_builds_html():
    result = run_fixture("run", "basic", ":docs")

    index_html = result.build_dir / "index.html"

    assert "Basic Test" in index_html.read_text(encoding="utf-8")


def test_metamodel_violation_fails_build():
    result = run_fixture(
        "build", "metamodel_violation", ":needs_json", expect_error=True
    )
    assert "is missing required attribute" in result.stderr


def test_producer_needs_json_contains_local_need():
    """
    The producer must export its own need
    """
    result = run_fixture("build", "external_needs/producer", ":needs_json")
    assert result.artifacts

    needs_json = result.artifacts["needs.json"]
    needs = load_needs(needs_json)

    assert "test_req__producer__demo" in needs, sorted(needs)


def test_consumer_link_resolves():
    """
    The consumer must resolve the producer's need as an external link in its HTML output.

    Exit 0 under -W already proves no "not found" warning fired;
    the html-content assert is the stronger guard: the producer id must
    appear as a resolved external link (href into the producer's base_url), not
    just as literal text.
    """
    result = run_fixture("run", "external_needs/consumer", ":docs")

    index = result.build_dir / "index.html"
    html = index.read_text(encoding="utf-8")

    # A resolved external link points at the producer's base_url + fragment.
    assert "external-needs-producer/main/index.html#test_req__producer__demo" in html, (
        html
    )
