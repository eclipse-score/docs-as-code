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
"""A minimal target for testing arbitrary dependency-graph boundaries."""

def _dependency_probe_impl(ctx):
    """Publish no files while allowing arbitrary targets on a deps edge."""
    return [DefaultInfo(files = depset())]

dependency_probe = rule(
    implementation = _dependency_probe_impl,
    attrs = {
        "deps": attr.label_list(),
    },
)
