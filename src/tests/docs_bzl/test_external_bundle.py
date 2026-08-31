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

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
# *******************************************************************************
"""External docs_bundle() scenario."""

import json

from src.tests.docs_bzl.helpers import repo_root, run_scenario


def test_external_bundle_builds_in_sandbox_and_at_runtime():
    run_scenario("build", "external_bundle", ":needs_json")
    result = run_scenario("run", "external_bundle", ":docs")

    assert (result.build_dir / "index.html").is_file()
    report = json.loads(
        (result.build_dir / "compatibility-findings.json").read_text(encoding="utf-8")
    )
    assert report["summary"]["count"] >= 0


def test_public_bundle_examples_use_only_bundle_sources():
    page = repo_root() / "docs/how-to/bundles/examples.rst"
    content = page.read_text(encoding="utf-8")

    for relative_path in (
        "examples/nested_bundles.inc",
        "examples/generated_data.inc",
        "examples/external_bundle.inc",
    ):
        assert f"literalinclude:: {relative_path}" in content
        assert (page.parent / relative_path).is_file()

    assert "../../../src/tests/docs_bzl" not in content
