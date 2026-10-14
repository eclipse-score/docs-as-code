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

"""Test-only stand-in for a Doxygen run: one action that outputs a directory."""

def _fake_doxygen_impl(ctx):
    out = ctx.actions.declare_directory(ctx.label.name)
    ctx.actions.run_shell(
        outputs = [out],
        command = """
mkdir -p "$1/files"
echo '<html><body>Fake API index</body></html>' > "$1/index.html"
echo '<html><body>Fake nested page</body></html>' > "$1/files/page.html"
echo 'body { color: black; }' > "$1/doxygen.css"
""",
        arguments = [out.path],
        # A dedicated mnemonic lets a test find this action in the action graph.
        mnemonic = "FakeDoxygen",
    )
    return [DefaultInfo(files = depset([out]))]

fake_doxygen = rule(
    implementation = _fake_doxygen_impl,
    doc = "Writes a small HTML tree into a directory output, like Doxygen does.",
)
