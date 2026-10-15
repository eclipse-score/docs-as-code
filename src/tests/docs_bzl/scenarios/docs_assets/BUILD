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

# This fixture mounts pre-built files of several types with docs_assets: a
# generated HTML directory (standing in for Doxygen), a generated PDF and PNG,
# and a checked-in SVG. They are placed at ``api`` inside a child bundle that
# is itself mounted at ``child``, so they land in ``child/api/``.

load("//:docs.bzl", "docs", "docs_assets", "docs_bundle")
load(":fake_doxygen.bzl", "fake_doxygen")

# Directory output: its contents go to <mount_at>/ (index.html, files/page.html).
fake_doxygen(name = "api_html")

genrule(
    name = "manual_pdf",
    outs = ["manual.pdf"],
    cmd = "printf '%%PDF-1.4\\n%%%%EOF\\n' > $@",
)

genrule(
    name = "logo_png",
    outs = ["logo.png"],
    # A 1x1 pixel PNG.
    cmd = "echo iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg== | base64 -d > $@",
)

# BEGIN docs-assets-howto
docs_assets(
    name = "api_assets",
    srcs = [
        ":api_html",  # directory: contents go to api/
        ":manual_pdf",  # file: goes to api/manual.pdf
        ":logo_png",  # file: goes to api/logo.png
        "assets/diagram.svg",  # checked-in file: goes to api/diagram.svg
    ],
)

docs_bundle(
    name = "child",
    source_dir = "child",
    bundles = [{
        "bundle": ":api_assets",
        "mount_at": "api",
    }],
)

docs(
    source_dir = "docs",
    # Keep this fixture's test-source scope local, see data_files_runfiles.
    test_sources = ["src/tests/docs_bzl/scenarios/docs_assets"],
    bundles = [{
        "bundle": ":child",
        "mount_at": "child",
        "attach_to": "index",
    }],
)
# END docs-assets-howto
