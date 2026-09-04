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

from src.tests.docs_bzl.helpers import run_scenario


@pytest.mark.bazel_slow
def test_metamodel_violation_fails_build():
    result = run_scenario(
        "build", "metamodel_violation", ":needs_json", expect_error=True
    )
    assert "is missing required attribute" in result.stderr
