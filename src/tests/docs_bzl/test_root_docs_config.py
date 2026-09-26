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
"""Integration coverage for configuration supplied by a root docs target."""

from src.tests.docs_bzl.helpers import (
    built_output,
    load_needs,
    load_needs_json,
    run_scenario,
)


def test_child_bundle_uses_root_docs_config_without_a_child_conf_py():
    """The child uses root config, metamodel, and ID namespace."""
    run_scenario("build", "root_docs_config", ":component.__internal__.needs_local")

    needs_json = built_output(
        "scenarios/root_docs_config",
        "component.__internal__.needs_local/_build/needs/needs.json",
    )
    needs = load_needs(needs_json)
    metadata = load_needs_json(needs_json)

    assert "test_req__docs_as_code__temperature" in needs
    assert metadata["project"] == "Root docs configuration fixture"
    assert metadata["project_url"] == (
        "https://example.invalid/root-docs-config/"
        "src/tests/docs_bzl/scenarios/root_docs_config"
    )


def test_child_bundle_does_not_inherit_the_root_legacy_conf_py():
    """A legacy root conf.py is not part of the root config contract."""
    result = run_scenario(
        "build",
        "root_docs_config",
        ":conf_sensitive_child.__internal__.needs_local",
        expect_error=True,
    )

    assert "Feature part" in result.stderr
    assert "legacy_parent" in result.stderr
