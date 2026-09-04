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

# This component is a nested documentation package, like the feature bundles
# in the S-CORE integration. Its parent module owns the surrounding source
# tree and mounts this bundle at the component placement. The implementation
# file is supplied through ``code_targets`` to exercise source-link generation
# for a component that is propagated through the module bundle.
#
# The component intentionally does not import the platform Needs itself. Its
# requirement links to the platform feature, so the component Needs target is
# valid only when the parent module supplies that external Needs.
docs_bundle(
    name = "docs_bundle",
    source_dir = ".",
    code_targets = [":component_sources"],
    visibility = ["//visibility:public"],
)
