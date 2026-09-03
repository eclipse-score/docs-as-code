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

# A source-bearing bundle exports the Needs declared by its own documentation
# through the internal ``needs_local`` target. This fixture deliberately has no
# cross-bundle references; those are handled by a later hierarchy change.
docs_bundle(
    name = "platform",
    source_dir = "platform",
)
