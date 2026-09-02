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

load("//:docs.bzl", "docs")

# This fixture represents the middle layer of the regression scenario:
#
#   producer:needs_json
#       -> legacy_consumer: docs(data = [producer:needs_json])
#       -> legacy_consumer:docs_bundle
#       -> outer consumer mounts that bundle
#
# The legacy ``docs(data = [...])`` form is used by existing consumers such as
# score_platform. The parameter remains valid for importing external needs,
# and the target is also retained as data on this project's public
# ``docs_bundle``. The outer consumer is therefore essential: running only this
# docs target does not ask score_mounts to resolve the bundle's data.
#
# The process-description ``needs_json`` output is a Bazel TreeArtifact (a
# directory), not a single file. Running this docs target by itself exercises
# the supported external-needs import. The outer consumer mounts this bundle to
# exercise the additional bundle-data path that currently fails when
# score_mounts insists that every data path be a regular file.
docs(
    project = "Legacy External Needs Consumer",
    project_url = "https://example.invalid/legacy-external-needs-consumer",
    source_dir = "docs",
    data = [
        "@score_process_description//:needs_json",
    ],
)
