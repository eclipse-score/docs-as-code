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

# The mount feature's own documentation, mounted back into the site via the
# mount feature itself (dogfooding). One subdirectory per bundle: mounts are
# directory-scoped, so co-locating both files in one dir would graft both at
# each mount point.
docs_bundle(
    name = "concept",
    source_dir = "concept",
    visibility = ["//visibility:public"],
)

docs_bundle(
    name = "howto",
    source_dir = "howto",
    visibility = ["//visibility:public"],
)

docs_bundle(
    name = "internals",
    source_dir = "internals",
    visibility = ["//visibility:public"],
)
