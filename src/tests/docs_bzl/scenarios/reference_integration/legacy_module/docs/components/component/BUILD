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

load("//:docs.bzl", "docs_bundle")

filegroup(
    name = "component_sources",
    srcs = ["implementation.py"],
)

# This component is a nested documentation package below the module's source
# directory. The implementation file is deliberately supplied through
# ``code_targets`` so its traceability annotation exercises the source-link
# generation path used by real component bundles.
docs_bundle(
    # Deliberately keep the Bazel target name independent from the Need ID.
    # The explicit primary_need_id is the only association used for metadata.
    name = "docs_bundle",
    source_dir = ".",
    code_targets = [":component_sources"],
    primary_need_id = "tool_req__legacy_component",
    visibility = ["//visibility:public"],
)
