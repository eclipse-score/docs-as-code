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

load("//:docs.bzl", "docs_bundle")

# This component deliberately contains no links to Needs outside its own
# source tree. It is the control case for the linked component next to it: the
# same module can mount both bundles, while this one can also produce a local
# Needs inventory without the module's external Needs.
#
# Generate a small page from the metamodel input so the mounted source comes
# from bazel-out rather than from a checked-in RST tree. The line count makes
# the generated page depend on the actual metamodel without copying the full
# metamodel reference into this focused integration fixture.
genrule(
    name = "generated_metamodel_page",
    srcs = ["//src/extensions/score_metamodel:metamodel_yaml"],
    outs = ["generated/index.rst"],
    cmd = """source_lines=$$(wc -l < $(execpath //src/extensions/score_metamodel:metamodel_yaml))
cat > $@ <<EOF
Generated metamodel bundle page
================================

This page is generated from the SCORE metamodel input and mounted from a
Bazel output directory.

Generated source details
------------------------

The source metamodel contains $${source_lines} lines.
EOF""",
)

docs_bundle(
    name = "generated_metamodel",
    srcs = [":generated_metamodel_page"],
    entry_doc = "index",
)

# Mount the generated bundle below the component so the reference integration
# exercises the mounted-source sidebar path while the component's own source
# still covers the standalone Needs export.
docs_bundle(
    name = "docs_bundle",
    source_dir = ".",
    bundles = [{
        "bundle": ":generated_metamodel",
        "mount_at": "generated_metamodel",
    }],
    visibility = ["//visibility:public"],
)
