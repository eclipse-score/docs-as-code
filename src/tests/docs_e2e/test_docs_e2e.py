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
"""End-to-end test for a minimal docs() project without mounts."""

from pathlib import Path

from support import run_docs_build, runfile


def test_docs_builds_html(tmp_path: Path):
    """docs() builds the host documentation without a mount configuration."""
    result = run_docs_build(
        tmp_path,
        docs_binary=runfile("DOCS_BINARY"),
        source_dir=runfile("DOCS_CONF").parent,
        sourcelinks=runfile("SOURCELINKS"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "_build" / "index.html").is_file()
