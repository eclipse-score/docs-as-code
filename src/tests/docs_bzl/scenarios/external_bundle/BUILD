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

# This fixture exercises the public Bzlmod contract. In particular, the
# sandboxed :needs_json target must be able to walk an external bundle rather
# than silently omitting it.
docs(
    source_dir = "host_docs",
    test_sources = ["src/tests/docs_bzl/scenarios/external_bundle"],
    bundles = [{
        "bundle": "@score_process_description//:docs_bundle",
        "mount_at": "process",
    }],
)
