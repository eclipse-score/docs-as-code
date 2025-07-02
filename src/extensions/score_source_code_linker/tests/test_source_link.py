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
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import TempPathFactory
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData

from src.extensions.score_source_code_linker import (
    get_github_base_url,
    get_github_link
)
from src.extensions.score_source_code_linker.needlinks import ( 
    NeedLink
)
from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_ws_root
)
import os


def construct_gh_url() -> str:
    gh = get_github_base_url()
    return f"{gh}/blob/"


@pytest.fixture(scope="session")
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("sphinx")
    os.environ["SPHINX_TEST_DIR"] = str(path)
    return path


@pytest.fixture(scope="session")
def sphinx_app_setup(
    sphinx_base_dir: Path,
) -> Callable[[str, str], SphinxTestApp]:
    def _create_app(
        conf_content: str, rst_content: str,
    ):
        src_dir = sphinx_base_dir / "src"
        src_dir.mkdir(exist_ok=True)

        (src_dir / "conf.py").write_text(conf_content)
        (src_dir / "index.rst").write_text(rst_content)

        return SphinxTestApp(
            freshenv=True,
            srcdir=Path(src_dir),
            confdir=Path(src_dir),
            outdir=sphinx_base_dir / "out",
            buildername="html",
            warningiserror=True,
        )

    return _create_app


@pytest.fixture(scope="session")
def basic_conf():
    return """
extensions = [
    "sphinx_needs",
    "score_source_code_linker",
]
needs_types = [
    dict(
        directive="test_req",
        title="Testing Requirement",
        prefix="TREQ_",
        color="#BFD8D2",
        style="node",
    ),
]
needs_extra_options = ["source_code_link"]
"""


@pytest.fixture(scope="session")
def basic_needs():
    return """
TESTING SOURCE LINK
===================

.. test_req:: TestReq1
   :id: TREQ_ID_1
   :status: valid

.. test_req:: TestReq2
   :id: TREQ_ID_2
   :status: open
"""

@pytest.fixture(scope="session")
def example_source_link_text_all_ok():
    return {
        "TREQ_ID_1": [
            NeedLink(
                file= Path("/tools/sources/implementation1.py#L2"),
                line= 1,
                tag= "#"+ " req-Id:",
                need= "TREQ_ID_1",
            full_line=""
            ),
            NeedLink(
            file=Path("/tools/sources/implementation_2_new_file.py"),
            line= 20,
            tag= "#"+ " req-Id:",
            need= "TREQ_ID_1",
            full_line=""
        )],
        "TREQ_ID_2": [
        NeedLink(
            file= Path(f"tools/sources/implementation1.py#L18"),
            need= "TREQ_ID_2",
            tag= "#"+ " req-Id:",
            line= 18,
            full_line=""
            )]
    }


@pytest.fixture(scope="session")
def example_source_link_text_non_existent():
    github_base_url = construct_gh_url()
    return {
        "TREQ_ID_200": [
            f"{github_base_url}f53f50a0ab1186329292e6b28b8e6c93b37ea41/tools/sources/bad_implementation.py#L17"
        ],
    }


def make_source_link(ws_root: Path, needlinks): 
    return ", ".join(
                f"{get_github_link(ws_root, n)}<>{n.file}:{n.line}" for n in needlinks
            )

def test_source_link_integration_ok(
    sphinx_app_setup: Callable[[str, str], SphinxTestApp],
    basic_conf: str,
    basic_needs: str,
    example_source_link_text_all_ok: dict[str, list[str]],
    sphinx_base_dir: Path,
):
    app = sphinx_app_setup(basic_conf, basic_needs)
    try:
        app.build()
        ws_root = find_ws_root()
        if ws_root is None:
            ws_root = Path(".")
        Needs_Data = SphinxNeedsData(app.env)
        needs_data = {x["id"]: x for x in Needs_Data.get_needs_view().values()}
        assert "TREQ_ID_1" in needs_data
        assert "TREQ_ID_2" in needs_data
        expected_link1 = make_source_link(ws_root, example_source_link_text_all_ok["TREQ_ID_1"])
        expected_link2 = make_source_link(ws_root, example_source_link_text_all_ok["TREQ_ID_2"])
        print(expected_link1)
        print(expected_link2)
        # extra_options are only available at runtime
        assert expected_link2 == needs_data["TREQ_ID_2"]["source_code_link"]  # type: ignore)
        assert expected_link1 == needs_data["TREQ_ID_1"]["source_code_link"]  # type: ignore)
    finally:
        app.cleanup()


def test_source_link_integration_non_existent_id(
    sphinx_app_setup: Callable[[str, str], SphinxTestApp],
    basic_conf: str,
    basic_needs: str,
    example_source_link_text_non_existent: dict[str, list[str]],
    sphinx_base_dir: Path,
):
    app = sphinx_app_setup( basic_conf, basic_needs)
    try:
        app.build()
        warnings = app.warning.getvalue()
        assert (
            "tools/sources/bad_implementation.py:17: Could not find {TREQ_ID_200} in documentation" in warnings
        )
    finally:
        app.cleanup()
