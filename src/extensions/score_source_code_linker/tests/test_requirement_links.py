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
    # find_git_root,
    # get_git_hash,
    # get_github_base_url,
    # get_github_repo_info,
    # parse_git_output,
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


