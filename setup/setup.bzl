# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

"""Bazel extension to expose transitive dependencies for score_docs_as_code."""

def _setup_impl(module_ctx):
    """Module extension implementation that exposes transitive dependencies.
    
    This allows downstream modules to access transitive dependencies like
    score_python_basics without explicitly declaring them in their MODULE.bazel.
    """
    # This extension simply needs to exist to allow downstream modules to use use_repo()
    # to access the transitive dependencies that this module already provides
    pass

# Define the module extension named "setup"
setup = module_extension(
    implementation = _setup_impl,
)