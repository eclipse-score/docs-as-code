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
import logging
import os
from collections import defaultdict
from collections.abc import Callable
from gettext import find
from pathlib import Path

import pytest
from pytest import TempPathFactory
from sphinx.testing.util import SphinxTestApp
from sphinx.application import Sphinx

from src.extensions.score_source_code_linker import (
    setup_once,
    find_git_root,
    get_github_base_url,
    get_github_repo_info,
    parse_git_output,
)
from src.extensions.score_source_code_linker import (
    LOGGER as scl_logger,
)
import tempfile

import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from collections import defaultdict
from copy import deepcopy


def create_dummy_sphinx_app():
    srcdir = tempfile.TemporaryDirectory()
    confdir = srcdir.name
    outdir = tempfile.TemporaryDirectory()
    doctreedir = tempfile.TemporaryDirectory()

    # You need at least an empty conf.py, create it:
    (Path(confdir) / "conf.py").write_text("")

    app = Sphinx(
        srcdir=confdir,
        confdir=confdir,
        outdir=outdir.name,
        doctreedir=doctreedir.name,
        buildername="html",
    )
    return app


def test_setup_once_early_return():
    # ws_root should be None here
    testApp = create_dummy_sphinx_app()
    assert setup_once(testApp) is None


def test_get_github_repo_info():
    # I'd argue the happy path is tested with the other ones?
    with pytest.raises(AssertionError):
        get_github_repo_info(Path("."))


git_test_data_ok = [
    (
        "origin  https://github.com/eclipse-score/test-repo.git (fetch)",
        "eclipse-score/test-repo",
    ),
    (
        "origin  git@github.com:eclipse-score/test-repo.git (fetch)",
        "eclipse-score/test-repo",
    ),
    ("origin  git@github.com:eclipse-score/test-repo.git", "eclipse-score/test-repo"),
    ("upstream  git@github.com:upstream/repo.git (fetch)", "upstream/repo"),
]


@pytest.mark.parametrize("input,output", git_test_data_ok)
def test_parse_git_output_ok(input, output):
    assert output == parse_git_output(input)


git_test_data_bad = [
    ("origin ", ""),
    (
        "    ",
        "",
    ),
]


@pytest.mark.parametrize("input,output", git_test_data_bad)
def test_parse_git_output_bad(caplog, input, output):
    with caplog.at_level(logging.WARNING, logger=scl_logger.name):
        result = parse_git_output(input)
    assert len(caplog.messages) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert (
        f"Got wrong input line from 'get_github_repo_info'. Input: {input}. Expected example: 'origin git@github.com:user/repo.git'"
        in caplog.records[0].message
    )
    assert output == result


# def test_get_github_base_url():
#     # Not really a great test imo.
#     git_root = find_git_root()
#     repo = get_github_repo_info(git_root)
#     expected = f"https://github.com/{repo}"
#     actual = get_github_base_url()
#     assert expected == actual
