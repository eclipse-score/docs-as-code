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

load("//:docs.bzl", "docs")

# FIXME:
# The custom metamodel is supplied via score_metamodel_yaml in docs/conf.py
# rather than docs(metamodel=...), because the metamodel= wiring does not reach
# the :needs_json target in the current docs.bzl (regression from #484).
docs(
    source_dir = "docs",
)
