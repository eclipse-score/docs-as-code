# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

load("//:docs.bzl", "docs", "docs_bundle")

filegroup(
    name = "fixture_build",
    srcs = ["BUILD"],
    visibility = ["//visibility:public"],
)

docs_bundle(
    name = "literalinclude_data",
    data = [":fixture_build"],
    visibility = ["//visibility:public"],
)

docs(
    source_dir = "docs",
    project = "Bundle Data Provider",
    project_url = "https://example.invalid/bundle-data-provider",
    data = [":fixture_build"],
    bundles = [{
        "bundle": ":literalinclude_data",
        "mount_at": "_literalinclude_data",
    }],
)
