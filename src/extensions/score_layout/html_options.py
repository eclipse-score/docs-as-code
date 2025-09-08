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
from typing import Any

from sphinx.application import Sphinx


def return_html_theme_options(app: Sphinx) -> dict[str, Any]:
    theme_options: dict[str, Any] = {
        "navbar_align": "content",
        "header_links_before_dropdown": 5,
        "icon_links": [
            {
                "name": "GitHub",
                "url": "https://github.com/eclipse-score",
                "icon": "fa-brands fa-github",
                "type": "fontawesome",
            }
        ],
        # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/source-buttons.html#add-an-edit-button
        "use_edit_page_button": True,
        "collapse_navigation": True,
        "logo": {
            "text": "Eclipse S-CORE",
        },
    }

    # Enable version switcher if github_user and github_repo are provided via CLI
    if (
        app.config.html_context.get("github_user") != "dummy"
        and app.config.html_context.get("github_repo") != "dummy"
    ):
        theme_options["switcher"] = {
            "json_url": (
                f"https://{app.config.html_context['github_user']}.github.io/"
                f"{app.config.html_context['github_repo']}/versions.json"
            ),  # URL to JSON file, hardcoded for now
            "version_match": app.config.release,
        }
        theme_options["navbar_end"] = [
            "theme-switcher",
            "navbar-icon-links",
            "version-switcher",
        ]
    else:
        theme_options["navbar_end"] = ["theme-switcher", "navbar-icon-links"]

    return theme_options


html_theme = "pydata_sphinx_theme"  # "alabaster"
html_static_path = ["src/assets", "_assets"]
html_css_files = [
    "css/score.css",
    "css/score_needs.css",
    "css/score_design.css",
]

# html_logo = "_assets/S-CORE_Logo_white.svg"


def return_html_context(app: Sphinx) -> dict[str, str]:
    if not hasattr(app.config, "html_context") or (
        not app.config.html_context.get("github_user")
        and not app.config.html_context.get("github_repo")
    ):
        return {
            # still required for use_edit_page_button and other elements
            # except version switcher
            "github_user": "dummy",
            "github_repo": "dummy",
            "github_version": "main",
            "doc_path": "docs",
        }
    return app.config.html_context
