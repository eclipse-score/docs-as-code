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
    
    This extension allows downstream modules to access transitive dependencies
    like score_python_basics without explicitly declaring them in their MODULE.bazel.
    
    The key insight is that this module already depends on score_python_basics,
    so the dependency is available transitively. This extension just provides
    a way for downstream consumers to access it via use_repo().
    
    Usage in downstream MODULE.bazel:
        use_extension("@score_docs_as_code//setup:setup.bzl", "setup")
        use_repo(setup, "score_python_basics")
    
    Note: This follows the standard Bazel module extension pattern. The
    pattern suggested in the issue description with setup.setup_dependencies()
    is not how Bazel module extensions work in practice.
    """
    # The extension implementation doesn't need to create or modify repositories.
    # It just needs to exist so that downstream consumers can use use_repo()
    # to access the transitive dependencies that this module provides.
    pass

# Define the module extension named "setup"
setup = module_extension(
    implementation = _setup_impl,
)