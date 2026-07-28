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

load("//:bzl/mount_rules.bzl", "create_mounts_manifest")
load("//:docs.bzl", "docs", "docs_bundle")
load("//:score_pytest.bzl", "score_pytest")

docs_bundle(
    name = "child",
    source_dir = "child",
    scan_code = [":scan_code"],
)

filegroup(
    name = "scan_code",
    srcs = ["child/example.py"],
)

# The child is nested below the parent bundle before the parent itself is
# mounted into the synthetic host tree below.
docs_bundle(
    name = "parent",
    source_dir = "parent",
    bundles = [{
        "bundle": ":child",
        "mount_at": "child",
    }],
)

# An aggregator deliberately has no source_dir. It only propagates its child
# and must preserve the declaration order in the generated manifest.
docs_bundle(
    name = "ordered_aggregate",
    bundles = [
        {"bundle": ":other", "mount_at": "first"},
        {"bundle": ":child", "mount_at": "second"},
    ],
)

docs_bundle(
    name = "other",
    source_dir = "other",
)

create_mounts_manifest(
    name = "ordered_aggregate_manifest",
    bundle = ":ordered_aggregate",
)

# A complete docs() invocation is the synthetic host project used by the
# end-to-end test below.
docs(
    source_dir = "host_docs",
    bundles = [{
        "bundle": ":parent",
        "mount_at": "concepts/example_bundle",
    }],
)

score_pytest(
    name = "mount_docs_e2e_test",
    size = "medium",
    srcs = ["test_mount_docs_e2e.py"],
    data = [
        ":docs",
        ":_mounts_manifest",
        ":ordered_aggregate_manifest",
        ":sourcelinks_json",
        ":parent",
        "host_docs/conf.py",
        "host_docs/concepts/index.rst",
        "host_docs/index.rst",
    ],
    deps = ["//src/tests/docs_e2e:e2e_support"],
    env = {
        "FIXTURE_DOCS_BINARY": "$(rootpath :docs)",
        "FIXTURE_MOUNTS_MANIFEST": "$(rootpath :_mounts_manifest)",
        "ORDERED_AGGREGATE_MANIFEST": "$(rootpath :ordered_aggregate_manifest)",
        "FIXTURE_SOURCELINKS": "$(rootpath :sourcelinks_json)",
        "HOST_DOCS_CONF": "$(rootpath host_docs/conf.py)",
    },
    pytest_config = "//:pyproject.toml",
)
