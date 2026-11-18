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
from types import SimpleNamespace
from typing import cast

from attribute_plugin import add_test_properties  # type: ignore[import-untyped]
from sphinx.application import Sphinx

from src.extensions.score_metamodel.checks.id_contains_feature import (
    id_contains_feature,
)
from src.extensions.score_metamodel.tests import fake_check_logger, need


def _app(bundle_export: bool) -> Sphinx:
    config = SimpleNamespace(required_in_id=[], score_bundle_needs_export=bundle_export)
    return cast(Sphinx, SimpleNamespace(config=config))


def _need():
    return need(
        id="comp_req__bitmanipulation__bit_operations",
        docname="requirements/index",
        lineno=42,
    )


@add_test_properties(
    partially_verifies=["tool_req__docs_common_attr_id_scheme"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_feature_part_must_be_in_path():
    """Outside a bundle export the feature part must appear in the path."""
    logger = fake_check_logger()
    id_contains_feature(_app(bundle_export=False), _need(), logger)
    logger.assert_warning(
        "Feature part 'bitmanipulation' not found in path", expect_location=False
    )


@add_test_properties(
    partially_verifies=["tool_req__docs_common_attr_id_scheme"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_bundle_export_skips_path_check():
    """A bundle's own export does not know its mount path."""
    logger = fake_check_logger()
    id_contains_feature(_app(bundle_export=True), _need(), logger)
    logger.assert_no_warnings()
