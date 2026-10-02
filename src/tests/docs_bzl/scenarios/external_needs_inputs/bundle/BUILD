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

# This bundle is intentionally independent of the producer's composed docs
# tree, so importing its Needs cannot duplicate a Need from another input.
docs_bundle(
    name = "docs_bundle",
    source_dir = "content",
    visibility = ["//visibility:public"],
)
