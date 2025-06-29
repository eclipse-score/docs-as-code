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
from src.extensions.score_source_code_linker.parse_source_files import (
    get_github_base_url,
)
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData


def construct_gh_url() -> str:
    gh = get_github_base_url()
    return f"{gh}/blob/"


@pytest.fixture(scope="session")
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("sphinx")


@pytest.fixture(scope="session")
def sphinx_app_setup(
    sphinx_base_dir: Path,
) -> Callable[[str, str, dict[str, list[str]]], SphinxTestApp]:
    def _create_app(
        conf_content: str, rst_content: str, requierments_text: dict[str, list[str]]
    ):
        src_dir = sphinx_base_dir / "src"
        src_dir.mkdir(exist_ok=True)

        (src_dir / "conf.py").write_text(conf_content)
        (src_dir / "index.rst").write_text(rst_content)
        (src_dir / "score_source_code_parser.json").write_text(
            json.dumps(requierments_text)
        )

        return SphinxTestApp(
            freshenv=True,
            srcdir=Path(src_dir),
            confdir=Path(src_dir),
            outdir=sphinx_base_dir / "out",
            buildername="html",
            warningiserror=True,
            confoverrides={
                "score_source_code_linker_file_overwrite": str(
                    src_dir / "score_source_code_parser.json"
                )
            },
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
needs_string_links = {
    "source_code_linker": {
        "regex": r"(?P<value>[^,]+)",
        "link_url": "{{value}}",
        "link_name": "Source Code Link",
        "options": ["source_code_link"],
    },
}
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
    github_base_url = construct_gh_url()
    return {
        "TREQ_ID_1": [
            f"{github_base_url}aacce4887ceea1f884135242a8c182db1447050/tools/sources/implementation1.py#L2",
            f"{github_base_url}/tools/sources/implementation_2_new_file.py#L20",
        ],
        "TREQ_ID_2": [
            f"{github_base_url}f53f50a0ab1186329292e6b28b8e6c93b37ea41/tools/sources/implementation1.py#L18"
        ],
    }


@pytest.fixture(scope="session")
def example_source_link_text_non_existent():
    github_base_url = construct_gh_url()
    return {
        "TREQ_ID_200": [
            f"{github_base_url}f53f50a0ab1186329292e6b28b8e6c93b37ea41/tools/sources/bad_implementation.py#L17"
        ],
    }


def test_source_link_integration_ok(
    sphinx_app_setup: Callable[[str, str, dict[str, list[str]]], SphinxTestApp],
    basic_conf: str,
    basic_needs: str,
    example_source_link_text_all_ok: dict[str, list[str]],
    sphinx_base_dir: Path,
):
    github_url = construct_gh_url()
    app = sphinx_app_setup(basic_conf, basic_needs, example_source_link_text_all_ok)
    try:
        app.build()
        Needs_Data = SphinxNeedsData(app.env)
        needs_data = {x["id"]: x for x in Needs_Data.get_needs_view().values()}
        assert "TREQ_ID_1" in needs_data
        assert "TREQ_ID_2" in needs_data
        # extra_options are only available at runtime
        assert (
            ",".join(example_source_link_text_all_ok["TREQ_ID_1"])
            == needs_data["TREQ_ID_1"]["source_code_link"]  # type: ignore
        )
        assert (
            ",".join(example_source_link_text_all_ok["TREQ_ID_2"])
            == needs_data["TREQ_ID_2"]["source_code_link"]  # type: ignore
        )
    finally:
        app.cleanup()


def test_source_link_integration_non_existent_id(
    sphinx_app_setup: Callable[[str, str, dict[str, list[str]]], SphinxTestApp],
    basic_conf: str,
    basic_needs: str,
    example_source_link_text_non_existent: dict[str, list[str]],
    sphinx_base_dir: Path,
):
    app = sphinx_app_setup(
        basic_conf, basic_needs, example_source_link_text_non_existent
    )
    try:
        app.build()
        warnings = app.warning.getvalue()
        assert (
            "WARNING: Could not find TREQ_ID_200 in the needs id's. Found in "
            "file(s): ['tools/sources/bad_implementation.py#L17']" in warnings
        )
    finally:
        app.cleanup()
