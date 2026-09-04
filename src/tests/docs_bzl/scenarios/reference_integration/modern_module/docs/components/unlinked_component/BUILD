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
docs_bundle(
    name = "docs_bundle",
    source_dir = ".",
    visibility = ["//visibility:public"],
)
