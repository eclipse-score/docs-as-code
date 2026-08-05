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

# This fixture exercises the public docs() macro with data (genrule output)
# that must be reachable through runfiles at ``bazel run`` time. See PR #686.

load("//:docs.bzl", "docs")

# Generate an RST file that only exists as a data dep (not in the source tree).
genrule(
    name = "generated_index",
    srcs = [],
    outs = ["index.rst"],
    cmd = """echo '::

Data RST Title' > $@""",
)

docs(
    source_dir = ".",
    data = [":generated_index"],
)