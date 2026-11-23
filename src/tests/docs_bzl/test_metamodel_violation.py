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
"""Invalid metamodel scenario for the public docs() API."""

import pytest
from score_pytest.attribute_plugin import add_test_properties

from src.tests.docs_bzl.helpers import run_scenario


@pytest.fixture(scope="module")
def stderr() -> str:
    """Build once; the build fails, and -W --keep-going reports every warning."""
    return run_scenario(
        "build", "metamodel_violation", ":needs_json", expect_error=True
    ).stderr


@pytest.mark.bazel_slow
def test_metamodel_violation_fails_build(stderr: str):
    # Match the need ID: test_req__needextend_delete also loses its status.
    assert "test_req__demo_missing: is missing required attribute: `status`." in stderr


@pytest.mark.bazel_slow
@add_test_properties(
    partially_verifies=["tool_req__docs_restrict_needextend"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_needextend_violations_are_reported(stderr: str):
    """needextend may only add values to unset options in its own document.

    Replace, delete and append actions, filters without c.this_doc() and
    unknown IDs are reported. Setting an unset string or list option is
    allowed.
    """
    for expected in [
        "Error when extending need: test_req__needextend_replace_set. "
        "Replacing of options that are already set is not allowed via needextends.",
        "Error when extending need: test_req__needextend_replace_link. "
        "Replace or Delete action is not allowed via needextends.",
        "Error when extending need: test_req__needextend_delete. "
        "Delete action is not allowed via needextends.",
        "Error when extending need: test_req__needextend_append. "
        "Append action is not allowed via needextends on 'string type options'.",
        "needextend in S-CORE must always be used per document only.",
        "Provided id 'test_req__unknown' for needextend does not exist.",
    ]:
        assert expected in stderr
    assert "Error when extending need: test_req__needextend_replace_unset." not in (
        stderr
    )
