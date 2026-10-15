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
"""A custom source generator for exercising generated implementation files."""

def _custom_source_generator_impl(ctx):
    """Copy one source or header to a generated default output."""
    if len(ctx.files.srcs) != 1:
        fail("custom_source_generator requires exactly one input file")
    ctx.actions.symlink(
        output = ctx.outputs.out,
        target_file = ctx.files.srcs[0],
    )
    return [DefaultInfo(files = depset([ctx.outputs.out]))]

custom_source_generator = rule(
    implementation = _custom_source_generator_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "out": attr.output(mandatory = True),
    },
)
