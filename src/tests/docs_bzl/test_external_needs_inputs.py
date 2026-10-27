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
"""Coverage for public bundle labels and direct Needs inventory inputs."""

import pytest

from src.tests.docs_bzl.helpers import run_package


@pytest.mark.bazel_slow
def test_public_docs_bundle_and_needs_json_file_inputs_resolve_needs():
    """The consumer resolves Needs from docs(), docs_bundle(), and a JSON file."""
    result = run_package("run", "scenarios/external_needs_inputs", ":docs")
    html = (result.build_dir / "index.html").read_text(encoding="utf-8")

    assert "#feat_req__platform__feature" in html
    assert "#gd_req__external_bundle" in html
    assert "#gd_req__producer_root" in html
