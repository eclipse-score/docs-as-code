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

load("//:docs.bzl", "docs", "docs_bundle")

# The root documentation target owns the structured configuration. Its legacy
# conf.py deliberately contains a value that must not cross the root-docs
# configuration boundary.
docs(
    source_dir = "platform",
    project = "Root docs configuration fixture",
    project_url = "https://example.invalid/root-docs-config",
    metamodel = ":metamodel.yaml",
    bundles = [{
        "bundle": ":component",
        "mount_at": "component",
    }],
)

# The child has no conf.py of its own. Its Needs export must receive the root
# project's structured configuration, ID namespace, and custom metamodel
# through the independent internal config target.
docs_bundle(
    name = "component",
    source_dir = "component",
    root_docs = "//src/tests/docs_bzl/scenarios/root_docs_config:docs",
)

# This bundle's Need ID is valid only when the root's legacy conf.py is
# propagated. The expected failure documents that conf.py is not part of the
# root-docs configuration interface.
docs_bundle(
    name = "conf_sensitive_child",
    source_dir = "conf_sensitive_child",
    root_docs = "//src/tests/docs_bzl/scenarios/root_docs_config:docs",
)
