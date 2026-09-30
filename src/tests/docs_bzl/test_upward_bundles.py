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
"""Integration coverage for declared upward Needs visibility.

The fixture separates three concerns: ``root_docs`` supplies project
configuration, ``upward_bundles`` supplies link-validation inputs, and
``docs(bundles=...)`` composes pages for rendering. These tests exercise the
standalone child export so those relationships cannot be conflated.
"""

from typing import cast

import pytest

from src.tests.docs_bzl.helpers import built_output, load_needs, run_scenario


@pytest.mark.bazel_cached
def test_bundle_validates_parent_links_but_exports_only_owned_needs():
    """Import the parent for link resolution, then serialize only child-owned Needs.

    The child Need's link proves the parent was present in Sphinx's in-memory
    graph. The exact exported ID set proves the parent stayed external and was
    removed by Sphinx-Needs' default builder filter when JSON was written.
    """
    run_scenario(
        "build",
        "upward_bundle_needs",
        ":component.__internal__.needs_local",
    )

    needs_json = built_output(
        "scenarios/upward_bundle_needs",
        "component.__internal__.needs_local/_build/needs/needs.json",
    )
    needs = load_needs(needs_json)

    assert set(needs) == {"tsf__docs_as_code__child"}
    child = needs["tsf__docs_as_code__child"]
    assert isinstance(child, dict)
    child_record = cast("dict[str, object]", child)
    child_links = child_record.get("links")
    assert isinstance(child_links, list)
    # ``load_needs`` intentionally types nested JSON as ``object``. After
    # checking the Sphinx field is a list, narrow its element type for the ID
    # membership assertion below.
    typed_child_links = cast("list[str]", child_links)
    assert "tsf__docs_as_code__parent" in typed_child_links


@pytest.mark.bazel_cached
def test_bundle_rejects_parent_links_without_declared_upward_import():
    """The child cannot resolve an ancestor merely because it shares root_docs.

    This builds the same RST with the same project config as the successful
    case, but without ``upward_bundles``. The missing parent ID must therefore
    remain an unresolved Sphinx-Needs link.
    """
    result = run_scenario(
        "build",
        "upward_bundle_needs",
        ":component_without_upward_import.__internal__.needs_local",
        expect_error=True,
    )

    assert "tsf__docs_as_code__parent" in result.stderr
