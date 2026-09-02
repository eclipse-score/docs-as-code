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
"""External needs scenario for the public docs() API."""

from src.tests.docs_bzl.helpers import load_needs, run_scenario


def test_producer_needs_json_contains_local_need():
    result = run_scenario("build", "external_needs/producer", ":needs_json")
    assert result.artifacts

    needs = load_needs(result.artifacts["needs.json"])
    assert "test_req__producer__demo" in needs, sorted(needs)


def test_consumer_link_resolves_and_legacy_data_bundle_mounts():
    """A consumer handles explicit needs and a legacy data-based bundle.

    The scenario is deliberately two-level: the legacy consumer imports the
    producer's directory-valued ``needs_json`` through ``docs(data = [...])``;
    this consumer then mounts the legacy consumer's ``docs_bundle``. The host
    run is intentionally end-to-end so it verifies that accepted docs data
    remains mountable after bundle composition, rather than only checking that
    the producer target is present in the build graph.
    """
    result = run_scenario("run", "external_needs/consumer", ":docs")

    html = (result.build_dir / "index.html").read_text(encoding="utf-8")
    assert "external-needs-producer/main/index.html#test_req__producer__demo" in html
    # The mounted bundle's entry page is available once its data mount has
    # been resolved successfully.
    assert (result.build_dir / "legacy" / "index.html").is_file()
