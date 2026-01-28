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

import sys
import os
from sphinx.application import Sphinx
from sphinx.util import logging

try:
    from bazel_runfiles import runfiles
except ImportError:
    try:
        from . import runfiles as runfiles
    except ImportError:
        import runfiles as runfiles
    except Exception as e:
        print("Could not import bazel_runfiles module.", file=sys.stderr)
        raise e
except Exception as e:
    print("Could not import bazel_runfiles module.", file=sys.stderr)
    raise e

logger = logging.getLogger(__name__)

# YOUR MODULE NAME (adjust as needed if it changes in bzlmod)
MODULE_NAME_CANDIDATES = [
    "score_docs_as_code+",
    "score_docs_as_code~",
    "_main",
]

PLANTUML_REL_PATH = "src/plantuml"  # Or whatever your actual structure is

def _find_plantuml_path():
    r = runfiles.Create()
    # Try all possible module prefixes
    for module_prefix in MODULE_NAME_CANDIDATES:
        key = f"{module_prefix}/{PLANTUML_REL_PATH}"
        candidate = r.Rlocation(key)
        if candidate and os.path.exists(candidate):
            logger.debug(f"Found PlantUML at: {candidate}")
            return candidate
    msg = (
        f"Could not find PlantUML binary in runfiles. "
        f"Tried keys: {[f'{m}/{PLANTUML_REL_PATH}' for m in MODULE_NAME_CANDIDATES]}. "
        "Have a look at README.md for instructions on how to build docs."
    )
    logger.error(msg)
    raise FileNotFoundError(msg)

def setup(app: Sphinx):
    plantuml_bin = _find_plantuml_path()
    app.config.plantuml = plantuml_bin
    app.config.plantuml_output_format = "svg_obj"
    app.config.plantuml_syntax_error_image = True
    app.config.needs_build_needumls = "_plantuml_sources"

    logger.info(f"PlantUML binary found at {app.config.plantuml}")
    return {"parallel_read_safe": True, "parallel_write_safe": True}
