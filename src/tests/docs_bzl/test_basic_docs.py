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

"""Public docs() smoke scenario."""

from src.tests.docs_bzl.helpers import built_output, load_needs_json, run_scenario


def test_basic_docs_builds_html():
    result = run_scenario("run", "basic_docs", ":docs")

    index_html = result.build_dir / "index.html"

    assert "Basic Test" in index_html.read_text(encoding="utf-8")


def test_basic_docs_builds_needs_without_conf_py():
    """Root docs data supports literalinclude in the sandboxed Sphinx build."""
    result = run_scenario("build", "basic_docs", ":needs_json")

    # With no docs/conf.py the generated config is used; it must set a non-empty
    # version so sphinx-needs writes a non-empty current_version into needs.json
    # (an empty current_version makes the file unusable for external consumers).
    assert result.artifacts is not None, f"expected artifacts: {result}"
    data = load_needs_json(result.artifacts["needs.json"])
    assert data["current_version"], "current_version must be non-empty"

    generated_conf = built_output("scenarios/basic_docs", "docs/conf.py")
    assert 'required_in_id = ["docs_as_code"]' in generated_conf.read_text(
        encoding="utf-8"
    )
