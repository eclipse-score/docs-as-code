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

import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util import logging

from src.helper_lib import config_setdefault, get_runfiles_dir

logger = logging.getLogger(__name__)


def use_document_source_as_plantuml_cwd(
    app: Sphinx, doctree: nodes.document, docname: str
) -> None:
    """Make PlantUML includes resolve from the real source-file directory.

    ``sphinx_mounts`` assigns mounted documents a logical docname below the
    primary project's source directory, while their files live in a Bazel
    runfiles tree.  ``sphinxcontrib.plantuml`` uses ``incdir`` as its working
    directory; for generated ``needuml`` nodes that value is derived from the
    logical docname and therefore does not exist.  Its error message then
    misleadingly claims that the PlantUML executable is missing.

    An absolute ``incdir`` is accepted by ``sphinxcontrib.plantuml`` and takes
    precedence over ``builder.srcdir`` when joined.  Run after sphinx-needs has
    replaced ``needuml`` nodes, so the generated PlantUML nodes carry their
    actual source path.

    Upstream bug report: https://github.com/useblocks/sphinx-needs/issues/1749
    Once solved we can remove this function.
    """
    from sphinxcontrib.plantuml import plantuml

    del app, docname  # Required by Sphinx's event callback signature.
    # ``sphinxcontrib.plantuml`` ships no type information; its nodes are
    # ordinary docutils elements.
    plantuml_nodes = cast("Iterator[nodes.Element]", doctree.findall(plantuml))
    for node in plantuml_nodes:
        if node.source is None:
            continue
        source = Path(node.source)
        if source.is_file():
            node["incdir"] = str(source.parent)


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


def check_graphviz(app: Sphinx) -> None:
    """Report a missing Graphviz dependency before rendering any diagrams."""

    # Ensure plantuml only for HTML builder
    if "html" not in app.builder.name:
        return

    result = subprocess.run(
        [app.config.plantuml, "-version"],
        capture_output=True,
        check=False,
        text=True,
    )
    output = (result.stdout + result.stderr).strip()

    if "Dot executable does not exist" in output:
        logger.error(
            "PlantUML requires Graphviz, but its 'dot' executable is not "
            "available on PATH. Install the 'graphviz' package in the "
            "development environment.\n\nPlantUML output:\n" + output
        )
        raise SystemExit(1)


def setup(app: Sphinx):
    # we must overwrite the plantuml path due to Bazel
    app.config.plantuml = str(find_correct_path(get_runfiles_dir()))
    config_setdefault(app.config, "plantuml_output_format", "svg_obj")
    config_setdefault(app.config, "plantuml_syntax_error_image", True)
    config_setdefault(app.config, "needs_build_needumls", "_plantuml_sources")

    logger.debug(f"PlantUML binary found at {app.config.plantuml}")
    app.connect("builder-inited", check_graphviz)
    # sphinx-needs creates PlantUML nodes during ``doctree-resolved``.  Its
    # standard-priority handler must run first, hence the larger priority.
    app.connect("doctree-resolved", use_document_source_as_plantuml_cwd, priority=800)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
