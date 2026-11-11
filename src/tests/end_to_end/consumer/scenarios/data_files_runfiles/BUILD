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

# This fixture exercises the public docs() macro with a source bundle whose
# only content is a genrule output living in ``bazel-out/.../bin/``
# (//docs/how-to/bundles/examples/generated_data_example:data_bundle).  That
# output must reach the runfiles of ``:docs`` (via _external_docs_runfiles)
# and be resolved by ``score_mounts`` at ``bazel run`` time.  See PR #686.

load("@score_docs_as_code//:docs.bzl", "docs", "docs_bundle")

docs_bundle(
    name = "isolated_source_bundle",
    srcs = ["isolated/index.rst"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)

docs(
    bundles = [
        {
            "bundle": "@score_docs_as_code//docs/how-to/bundles/examples/generated_data_example:data_bundle",
            "mount_at": "data_test",
            "attach_to": "index",
        },
        {
            "bundle": ":legacy_data_bundle",
            "mount_at": "legacy_data_test",
            "attach_to": "index",
        },
        {
            "bundle": ":isolated_source_bundle",
            "mount_at": "isolated_test",
            "attach_to": "index",
        },
    ],
    source_dir = "docs",
    # Keep this fixture's test-source scope local. The default imports every
    # test report in the repository, including unrelated external-link
    # warnings that would make this focused runtime scenario fail as an
    # accidental side effect of the global test corpus.
    test_sources = ["scenarios/data_files_runfiles"],
)

# Legacy compatibility: generated RST files declared through ``data`` must
# remain mountable while callers migrate to the explicit ``srcs`` attribute.
genrule(
    name = "legacy_generated_page",
    srcs = [],
    outs = ["legacy_generated/index.rst"],
    cmd = """echo 'Legacy Data Page
==================' > $@""",
)

# Legacy compatibility bundle: ``data`` still reaches the Sphinx mount walker.
docs_bundle(
    name = "legacy_data_bundle",
    data = [":legacy_generated_page"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)
