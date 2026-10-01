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
"""Integration coverage for bundle Needs visibility declared with external_needs.

The fixture separates three concerns: ``root_docs`` supplies project
configuration, ``external_needs`` supplies link-validation inputs, and
``docs(bundles=...)`` composes pages for rendering. These tests exercise the
standalone child export so those relationships cannot be conflated.
"""

import pytest

from src.tests.docs_bzl.helpers import built_output, load_needs, run_scenario


@pytest.mark.bazel_cached
def test_bundle_resolves_declared_parent_and_exports_only_owned_needs():
    """A declared parent link resolves, while the child's JSON stays owner-only.

    The build treats unresolved Needs links as errors, so its success confirms
    the imported parent is available. The exported ID set checks that the
    external parent remains outside the child's local inventory.
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


@pytest.mark.bazel_cached
def test_bundle_rejects_parent_links_without_external_needs_declaration():
    """The child cannot resolve an ancestor merely because it shares root_docs.

    This builds the same RST with the same project config as the successful
    case, but without ``external_needs``. The missing parent ID must therefore
    remain an unresolved Sphinx-Needs link.
    """
    result = run_scenario(
        "build",
        "upward_bundle_needs",
        ":component_without_upward_import.__internal__.needs_local",
        expect_error=True,
    )

    assert "tsf__docs_as_code__parent" in result.stderr


@pytest.mark.bazel_cached
def test_parent_bundle_reports_duplicate_need_ids_from_two_valid_children():
    """A combined import reports an ID collision hidden by a shared base URL.

    Each component exports the same local Need ID and imports the parent Need
    it links to, so either child is valid by itself. The top-level bundle then
    imports both inventories. Its warning proves that equal project URLs no
    longer let Sphinx-Needs silently replace the first child's Need.
    """
    run_scenario(
        "build",
        "upward_bundle_needs",
        ":component.__internal__.needs_local",
    )
    run_scenario(
        "build",
        "upward_bundle_needs",
        ":component_with_duplicate_need_id.__internal__.needs_local",
    )

    result = run_scenario(
        "build",
        "upward_bundle_needs",
        ":top_level_with_duplicate_child_need_id.__internal__.needs_local",
        expect_error=True,
    )

    assert (
        "External need ID 'tsf__docs_as_code__child' is present in both"
        in result.stderr
    )
    assert ":component.__internal__.needs_local" in result.stderr
    assert ":component_with_duplicate_need_id.__internal__.needs_local" in result.stderr
    assert "Both inventories use base URL" in result.stderr
