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
"""Invalid docs_bundle() placement scenario."""

from src.tests.docs_bzl.helpers import run_scenario


def test_invalid_bundle_placements_are_rejected_during_analysis():
    run_scenario("build", "invalid_bundle_placements", ":bad", expect_error=True)
    run_scenario(
        "build", "invalid_bundle_placements", ":bad_attach_to", expect_error=True
    )
    run_scenario("build", "invalid_bundle_placements", ":cycle_a", expect_error=True)
