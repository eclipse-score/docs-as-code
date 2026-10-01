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

load("//:docs.bzl", "docs", "docs_bundle")

# ``docs()`` below publishes the root as ``:docs`` and owns the parent Need.
# ``root_docs`` shares that project's configuration with the child, but does
# not make the parent's Needs available during a standalone child build. This
# child explicitly imports ``:docs`` so Sphinx-Needs can resolve the link in
# component/index.rst. It is a validation dependency, separate from the
# ``docs(bundles = ...)`` rendering composition below.
docs_bundle(
    name = "component",
    source_dir = "component",
    root_docs = ":docs",
    external_needs = [":docs"],
    visibility = ["//visibility:public"],
)

# This second target uses the same RST but omits ``external_needs``. Its Needs
# build must fail on the parent ID, proving that root_docs and page composition
# do not implicitly grant link visibility.
docs_bundle(
    name = "component_without_upward_import",
    source_dir = "component",
    root_docs = ":docs",
)

# Mounting the successful child creates the public rendered composition. The
# tests also build its owner-only Needs export directly to check that the
# parent's imported inventory is not copied into that artifact.
docs(
    source_dir = "docs",
    project = "Upward bundle Needs fixture",
    project_url = "https://example.invalid/upward-bundle-needs",
    bundles = [{
        "bundle": ":component",
        "mount_at": "component",
    }],
)
