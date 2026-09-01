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

load("//:docs.bzl", "docs", "docs_bundle")

docs_bundle(
    name = "platform",
    source_dir = "platform",
)

docs_bundle(
    name = "component",
    source_dir = "component",
    upward_bundles = [":docs_source_bundle"],
)

# Keep the source-less hierarchy-group export contract covered as well.
docs_bundle(
    name = "hierarchy_group",
    upward_bundles = [":component"],
    tags = ["manual"],
)

# Multiple direct parents are merged in declaration order. The hierarchy group
# and platform together provide both the module/component closure and the
# platform-level Need.
docs_bundle(
    name = "multiple_parent_group",
    upward_bundles = [":hierarchy_group", ":platform"],
    tags = ["manual"],
)

# Both direct parents expose the component/module closure. The merger must
# accept the identical shared ancestor records without duplicating them.
docs_bundle(
    name = "diamond_group",
    upward_bundles = [":hierarchy_group", ":component"],
    tags = ["manual"],
)

docs_bundle(
    name = "subcomponent",
    source_dir = "subcomponent",
    upward_bundles = [":hierarchy_group"],
)

docs(
    source_dir = "module",
    project = "SCORE upward bundle example",
    project_url = "https://example.invalid/upward-bundles",
    upward_bundles = [":platform"],
    test_sources = ["src/tests/docs_bzl/scenarios/upward_bundles"],
    metamodel = "//src/extensions/score_metamodel:metamodel_yaml",
    bundles = [
        {"bundle": ":component", "mount_at": "component"},
        {"bundle": ":subcomponent", "mount_at": "component/subcomponent"},
    ],
)
