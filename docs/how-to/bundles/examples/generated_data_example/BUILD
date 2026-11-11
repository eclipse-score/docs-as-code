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

# Example for docs/how-to/bundles/examples.rst ("Mount generated bundle
# content"). The project's own documentation mounts :data_bundle, and the
# data_files_runfiles end-to-end scenario in src/tests/docs_bzl tests it.

load("//:docs.bzl", "docs_bundle")

# Emit into a ``generated/`` subdirectory (as the real metamodel bundle does)
# so the resolved mount directory contains only the genrule output and not the
# sibling ``docs.runfiles/`` tree.
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
    # The shell writes the text below, up to each EOF marker, into the
    # generated RST and Mermaid files. $(execpath ...) expands to each declared
    # output's path in this build action, so the files land where Bazel expects.
    cmd = """cat > $(execpath generated/index.rst) <<'EOF'
Generated Data Page
===================

.. mermaid:: generated_data.mmd
   :name: generated-data-diagram
EOF
cat > $(execpath generated/generated_data.mmd) <<'EOF'
classDiagram
  class GeneratedData
EOF""",
)

docs_bundle(
    name = "data_bundle",
    srcs = [":generated_page"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)
