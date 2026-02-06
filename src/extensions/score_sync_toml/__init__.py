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
from pathlib import Path

from sphinx.application import Sphinx


def setup(app: Sphinx) -> dict[str, str | bool]:
    """
    Extension to configure needs-config-writer for syncing needs configuration to TOML.

    See https://needs-config-writer.useblocks.com
    """

    app.config.needscfg_outpath = "ubproject.toml"
    """Write to the confdir directory."""

    app.config.needscfg_overwrite = True
    """Any changes to the shared/local configuration updates the generated config."""

    app.config.needscfg_write_all = True
    """Write full config, so the final configuration is visible in one file."""

    app.config.needscfg_exclude_defaults = True
    """Exclude default values from the generated configuration."""

    # This is disabled for right now as it causes a lot of issues
    # While we are not using the generated file anywhere
    app.config.needscfg_warn_on_diff = False
    """Running Sphinx with -W will fail the CI for uncommitted TOML changes."""

    app.config.needscfg_merge_toml_files = [
        str(Path(__file__).parent / "shared.toml"),
    ]
    """Merge the static TOML file into the generated configuration."""

    app.config.needscfg_relative_path_fields = [
        "needs_external_needs[*].json_path",
        {
            "field": "needs_flow_configs.score_config",
            "prefix": "!include ",
        },
    ]
    """Relative paths to confdir for Bazel provided absolute paths."""

    app.config.suppress_warnings += [
        "needs_config_writer.unsupported_type",
        "needs_config_writer.path_conversion",
    ]
    # TODO remove the suppress_warnings once fixed

    app.config.needscfg_exclude_vars = [
        "needs_from_toml",
        "needs_from_toml_table",
        # "needs_schema_definitions_from_json",
    ]

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
