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

load("@score_docs_as_code//:bzl/mount_rules.bzl", "create_composition_manifest")
load("@score_docs_as_code//:docs.bzl", "docs", "docs_bundle")

docs_bundle(
    name = "ordered_aggregate",
    bundles = [
        {
            "bundle": ":other",
            "mount_at": "first",
        },
        {
            "bundle": "@score_docs_as_code//docs/how-to/bundles/examples/nested_example:child",
            "mount_at": "second",
        },
    ],
)

docs_bundle(
    name = "other",
    source_dir = "other",
)

create_composition_manifest(
    name = "ordered_aggregate_manifest",
    bundle = ":ordered_aggregate",
)

# A complete docs() invocation is the synthetic host project driven by the
# end-to-end pytest suite in src/tests/end_to_end/testcases.
docs(
    bundles = [{
        "bundle": "@score_docs_as_code//docs/how-to/bundles/examples/nested_example:parent",
        "mount_at": "concepts/example_bundle",
        # Attach to the second toctree (index 1) of concepts/index.rst.
        "toctree_index": 1,
    }],
    code_targets = ["@score_docs_as_code//docs/how-to/bundles/examples/nested_example:example_binary"],
    source_dir = "host_docs",
    test_sources = ["scenarios/nested_bundles"],
)
