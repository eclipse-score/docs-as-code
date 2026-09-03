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

# This scenario specifies the intended split between a bundle's own Needs and
# the Needs inherited from explicitly declared direct ancestors. It is a rough
# draft for the later propagation implementation.
docs_bundle(
    name = "platform",
    source_dir = "platform",
)

docs_bundle(
    name = "component",
    source_dir = "component",
    # Expected future API: make the platform export available as direct
    # resolution context and merge it into component's upward export.
    upward_bundles = ["platform"],
)

docs_bundle(
    name = "application",
    # Declaring only component must not implicitly include platform.
    upward_bundles = ["component"],
)

# A source-less hierarchy group must not be accepted as a direct Needs ancestor.
docs_bundle(
    name = "invalid_child",
    upward_bundles = ["application"],
)
