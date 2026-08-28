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
# Default Sphinx configuration for a ``docs_bundle`` local Needs export.

project = {PROJECT}
version = "0.0.0"
master_doc = {ENTRY_DOC}

extensions = ["score_sphinx_bundle"]

# A bundle-local export intentionally omits mounted descendants. The composed
# host Needs build resolves those outgoing links later.
suppress_warnings = ["needs.link_outgoing"]
