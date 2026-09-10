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
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import html_options
import sphinx_options
from sphinx.application import Sphinx

from src.helper_lib import Environment, config_setdefault

logger = logging.getLogger(__name__)
env = Environment()

# TEMP UNTIL UPSTREAM FIX - BEGIN
# Bug ref: https://github.com/useblocks/sphinx-needs/issues/1913
# Sphinx-Needs discovers these files with ``Path.glob``.  The filesystem
# does not define the order returned by that operation, while Sphinx preserves
# registration order for stylesheets with the same priority.  Keep the CSS
# cascade stable across Bazel runfiles, local virtual environments, and CI.
_NEEDS_COMMON_CSS_ORDER = (
    "sphinx-needs/common_css/needstable.css",
    "sphinx-needs/common_css/need_core.css",
    "sphinx-needs/common_css/need_style.css",
    "sphinx-needs/common_css/need_toggle.css",
    "sphinx-needs/common_css/need_links.css",
)
_NEEDS_COMMON_CSS_POSITION = {
    filename: position for position, filename in enumerate(_NEEDS_COMMON_CSS_ORDER)
}
# TEMP UNTIL UPSTREAM FIX - END


def setup(app: Sphinx) -> dict[str, str | bool]:
    logger.debug("score_layout setup called")

    app.connect("config-inited", update_config)
    # Run after the PyData theme creates its edit-URL callback so mounted pages
    # can replace the callback with a workspace-aware one.
    app.connect("html-page-context", configure_mounted_source_controls, priority=800)
    app.connect("html-page-context", normalize_needs_css_order)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def update_config(app: Sphinx, _config: Any):
    logger.debug("score_layout update_config called")

    # Merge: user's entries take precedence over our defaults
    app.config.needs_layouts = {
        **sphinx_options.needs_layouts,
        **app.config.needs_layouts,
    }
    config_setdefault(
        app.config, "needs_default_layout", sphinx_options.needs_default_layout
    )
    config_setdefault(app.config, "html_theme", html_options.html_theme)
    app.config.html_context = {
        **html_options.return_html_context(app),
        **app.config.html_context,
    }
    app.config.html_theme_options = {
        **html_options.return_html_theme_options(app),
        **app.config.html_theme_options,
    }

    logger.debug(f"score_layout __file__: {__file__}")

    score_layout_path = Path(__file__).parent.resolve()
    logger.debug(f"score_layout_path: {score_layout_path}")

    app.config.html_static_path.append(str(score_layout_path / "assets"))

    puml = score_layout_path / "assets" / "puml-theme-score.puml"
    app.config.needs_flow_configs.setdefault("score_config", f"!include {puml}")

    app.add_css_file("css/score.css", priority=500)
    app.add_css_file("css/score_needs.css", priority=500)
    app.add_css_file("css/score_design.css", priority=500)


# TEMP UNTIL UPSTREAM FIX - BEGIN
# Bug ref: https://github.com/useblocks/sphinx-mounts/issues/47
def configure_mounted_source_controls(
    app: Sphinx,
    pagename: str,
    _templatename: str,
    context: dict[str, Any],
    _doctree: Any,
) -> None:
    """Configure safe source/edit controls for mounted documents.

    ``sphinx-mounts`` stores the absolute filesystem path of a mounted source
    in Sphinx. Sphinx currently derives ``page_source_suffix`` from that path,
    which makes themes such as PyData build malformed source and edit URLs.
    A real source file inside the current workspace can still be mapped to a
    safe repository-relative URL. Generated and external sources have no such
    guaranteed URL, so their controls remain hidden until the mount extension
    exposes a logical source path and repository mapping.
    """
    source_path = Path(app.env.doc2path(pagename, base=False))
    if not source_path.is_absolute():
        return

    source_path = source_path.resolve()
    workspace_directory = env.optional_path("BUILD_WORKSPACE_DIRECTORY")
    if workspace_directory:
        workspace_root = workspace_directory.resolve()
        if (
            source_path.is_relative_to(workspace_root)
            and not {"bazel-bin", "bazel-out"}.intersection(source_path.parts)
            and _configure_workspace_edit_url(context, source_path, workspace_root)
        ):
            return

    context["page_source_suffix"] = ""
    context["sourcename"] = ""
    context["secondary_sidebar_items"] = []


def _configure_workspace_edit_url(
    context: dict[str, Any], source_path: Path, workspace_root: Path
) -> bool:
    """Install a GitHub edit callback for a source file in the workspace."""
    if context.get("edit_page_url_template") is not None:
        return False

    github_values = tuple(
        context.get(name) for name in ("github_user", "github_repo", "github_version")
    )
    if not all(
        isinstance(value, str) and value not in {"", "dummy", "None"}
        for value in github_values
    ):
        return False

    github_user, github_repo, github_version = cast(tuple[str, str, str], github_values)
    relative_path = quote(source_path.relative_to(workspace_root).as_posix(), safe="/")
    github_url = str(context.get("github_url", "https://github.com")).rstrip("/")
    edit_url = (
        f"{github_url}/{quote(github_user, safe='')}/{quote(github_repo, safe='')}"
        f"/edit/{quote(github_version, safe='')}/{relative_path}"
    )

    def get_edit_provider_and_url() -> tuple[str, str]:
        """Return the edit URL for the mounted workspace source."""
        return "GitHub", edit_url

    context["get_edit_provider_and_url"] = get_edit_provider_and_url
    return True


# TEMP UNTIL UPSTREAM FIX - END


# TEMP UNTIL UPSTREAM FIX - BEGIN
# Bug ref: https://github.com/useblocks/sphinx-needs/issues/1913
def normalize_needs_css_order(
    _app: Sphinx,
    _pagename: str,
    _templatename: str,
    context: dict[str, Any],
    _doctree: Any,
) -> None:
    """Make Sphinx-Needs common stylesheets deterministic before rendering."""
    css_files = context.get("css_files")
    if not isinstance(css_files, list):
        return
    css_files = cast(list[Any], css_files)

    common_css = [
        (index, css_file)
        for index, css_file in enumerate(css_files)
        if _css_filename(css_file) in _NEEDS_COMMON_CSS_POSITION
    ]
    if len(common_css) < 2:
        return

    positions = [index for index, _ in common_css]
    ordered_common_css = sorted(
        (css_file for _, css_file in common_css),
        key=lambda css_file: _NEEDS_COMMON_CSS_POSITION[_css_filename(css_file)],
    )
    normalized_css_files = list(css_files)
    for index, css_file in zip(positions, ordered_common_css, strict=True):
        normalized_css_files[index] = css_file
    context["css_files"] = normalized_css_files


def _css_filename(css_file: Any) -> str:
    """Return a stylesheet's path in the form used by Sphinx-Needs."""
    filename = str(os.fspath(getattr(css_file, "filename", css_file)))
    return Path(filename).as_posix().removeprefix("_static/")


# TEMP UNTIL UPSTREAM FIX - END
