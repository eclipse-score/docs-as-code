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

# This fixture exercises the public docs() macro with a data bundle whose
# only content is a genrule output living in ``bazel-out/.../bin/``.  That
# output must reach the runfiles of ``:docs`` (via _external_docs_runfiles)
# and be resolved by ``score_mounts`` at ``bazel run`` time.  See PR #686.

load("//:docs.bzl", "docs", "docs_bundle")

filegroup(
    name = "generated_data_build",
    srcs = ["BUILD"],
    visibility = ["//visibility:public"],
)

# Emit into a ``generated/`` subdirectory (as the real metamodel bundle does)
# so the resolved mount directory contains only the genrule output and not the
# sibling ``docs.runfiles/`` tree.
# BEGIN docs-bundle-howto: generated-data
genrule(
    name = "generated_page",
    srcs = [],
    outs = ["generated/index.rst"],
    cmd = """echo 'Generated Data Page
===================' > $@""",
)

# Pure-data bundle: the genrule output lives in ``bazel-out/``, not the tree.
docs_bundle(
    name = "data_bundle",
    data = [":generated_page"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)

docs(
    source_dir = "docs",
    test_sources = ["src/tests/docs_bzl/scenarios/data_files_runfiles"],
    bundles = [{
        "bundle": ":data_bundle",
        "mount_at": "data_test",
        "attach_to": "index",
    }],
)

# END docs-bundle-howto: generated-data
