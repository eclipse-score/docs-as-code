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
# only content is a genrule output living in ``bazel-out/.../bin/``.  That
# output must reach the runfiles of ``:docs`` (via _external_docs_runfiles)
# and be resolved by ``score_mounts`` at ``bazel run`` time.  See PR #686.

load("//:docs.bzl", "docs", "docs_bundle")

# Emit into a ``generated/`` subdirectory (as the real metamodel bundle does)
# so the resolved mount directory contains only the genrule output and not the
# sibling ``docs.runfiles/`` tree.
# BEGIN docs-bundle-howto: generated-data
genrule(
    name = "generated_page",
    srcs = [],
    outs = [
        "generated/index.rst",
        "generated/generated_data.mmd",
    ],
    # The RST and Mermaid file are both declared sources, but only the RST
    # should be registered as a Sphinx document. The Mermaid file is a
    # companion asset that must remain readable next to the original RST.
    cmd = """cat > $(location generated/index.rst) <<'EOF'
Generated Data Page
===================

.. mermaid:: generated_data.mmd
   :name: generated-data-diagram
EOF
cat > $(location generated/generated_data.mmd) <<'EOF'
classDiagram
  class GeneratedData
EOF""",
)

# Source bundle: the genrule output lives in ``bazel-out/``, not the tree.
docs_bundle(
    name = "data_bundle",
    srcs = [":generated_page"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)

# This source bundle deliberately declares only one file from ``isolated/``.
# The sibling below must not become part of the mounted documentation merely
# because it shares the source file's original parent directory.
docs_bundle(
    name = "isolated_source_bundle",
    srcs = ["isolated/index.rst"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)

docs(
    source_dir = "docs",
    # Keep this fixture's test-source scope local. The default imports every
    # test report in the repository, including unrelated external-link
    # warnings that would make this focused runtime scenario fail as an
    # accidental side effect of the global test corpus.
    test_sources = ["src/tests/docs_bzl/scenarios/data_files_runfiles"],
    bundles = [{
        "bundle": ":data_bundle",
        "mount_at": "data_test",
        "attach_to": "index",
    }, {
        "bundle": ":legacy_data_bundle",
        "mount_at": "legacy_data_test",
        "attach_to": "index",
    }, {
        "bundle": ":isolated_source_bundle",
        "mount_at": "isolated_test",
        "attach_to": "index",
    }],
)

# END docs-bundle-howto: generated-data

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
