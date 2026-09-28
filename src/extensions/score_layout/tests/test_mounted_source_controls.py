# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Tests for the secondary sidebar handling of mounted documents."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from sphinx.application import Sphinx

from src.extensions.score_layout import configure_mounted_source_controls


def _app(source_path: str) -> Sphinx:
    """Create the minimal Sphinx stub used by the page-context handler."""
    env = SimpleNamespace(doc2path=lambda _pagename, base: Path(source_path))
    return cast(Sphinx, SimpleNamespace(env=env))


def _context() -> dict[str, Any]:
    """Create a page context as the PyData theme leaves it behind."""
    return {
        "page_source_suffix": ".rst",
        "sourcename": "index.rst.txt",
        "secondary_sidebar_items": [
            "page-toc.html",
            "edit-this-page.html",
            "sourcelink.html",
        ],
    }


def test_local_page_keeps_all_source_controls() -> None:
    """A page with a relative source path is not a mounted page."""
    context = _context()

    configure_mounted_source_controls(
        _app("index.rst"), "index", "page.html", context, None
    )

    assert context == _context()


def test_mounted_page_keeps_page_toc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Only the controls that need a resolvable source file are removed."""
    monkeypatch.delenv("BUILD_WORKSPACE_DIRECTORY", raising=False)
    context = _context()

    configure_mounted_source_controls(
        _app(str(tmp_path / "mounted.rst")), "mounted", "page.html", context, None
    )

    assert context["page_source_suffix"] == ""
    assert context["sourcename"] == ""
    assert context["secondary_sidebar_items"] == ["page-toc.html"]
