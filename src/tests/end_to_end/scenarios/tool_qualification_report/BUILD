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

load("@score_docs_as_code//:docs.bzl", "docs")

# A tool verification report in this module, next to the mounted documentation
# of a second Bazel module. The report may only count the tool requirements and
# testcases of its own module as not reached.
docs(
    bundles = [{
        "bundle": "@score_tool_report_mounted//:docs_bundle",
        "mount_at": "mounted",
    }],
    # The tool requirements satisfy process requirements.
    external_needs = ["@score_process_description//:needs_json"],
    project = "Tool Qualification Report",
    project_url = "https://example.invalid/tool-qualification-report",
    source_dir = "docs",
)
