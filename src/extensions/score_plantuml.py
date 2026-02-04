# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

"""
This extension sets up PlantUML within the SCORE Bazel environment.

The complexity arises, as the plantuml binary is only available through Bazel.
However going through `bazel run //docs:plantuml` for every PlantUML diagram
is simply too slow.

This extension determines the path to the plantuml binary and sets it up in the
Sphinx configuration.

In addition it sets common PlantUML options, like output to svg_obj.
"""

from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util import logging

from src.helper_lib import get_runfiles_dir

logger = logging.getLogger(__name__)


def find_correct_path(runfiles: Path) -> Path:
    """
    This ensures that the 'plantuml' binary path is found in local 'score_docs_as_code'
    and module use.
    """
    if (Path(runfiles) / "score_docs_as_code+").exists():
        # Docs-as-code used as a module with bazel 8
        module = "score_docs_as_code+"
    elif (Path(runfiles) / "score_docs_as_code~").exists():
        # Docs-as-code used as a module with bazel 7
        module = "score_docs_as_code~"
    else:
        # Docs-as-code is the current module
        module = "_main"

    return runfiles / module / "src" / "plantuml"


def setup(app: Sphinx):
    app.config.plantuml = str(find_correct_path(get_runfiles_dir()))
    app.config.plantuml_output_format = "svg_obj"
    app.config.plantuml_syntax_error_image = True
    app.config.needs_build_needumls = "_plantuml_sources"

    logger.debug(f"PlantUML binary found at {app.config.plantuml}")

    # The extension is not even active at runtime.
    return {"parallel_read_safe": True, "parallel_write_safe": True}
