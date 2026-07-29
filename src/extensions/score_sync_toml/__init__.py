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

from src.extensions.score_sync_toml._mounts import register_mounts
from src.helper_lib import config_setdefault, find_git_root


def setup(app: Sphinx) -> dict[str, str | bool]:
    """
    Extension to configure needs-config-writer for syncing needs configuration to TOML.

    See https://needs-config-writer.useblocks.com
    """

    # Emit a single ubproject.toml at the git repo root, where UI extensions
    # (ubCode / esbonio) look for it. needs-config-writer relativizes every path
    # field against the output file's directory, so anchoring the file at the
    # root yields root-relative paths automatically. find_git_root() resolves the
    # root under `bazel run` and esbonio alike; in a sandbox build it returns None
    # and we fall back to the confdir default (that copy is ephemeral / discarded).
    git_root = find_git_root()
    outpath = str(git_root / "ubproject.toml") if git_root else "ubproject.toml"
    config_setdefault(app.config, "needscfg_outpath", outpath)
    """Write a single ubproject.toml at the git repo root."""

    config_setdefault(app.config, "needscfg_overwrite", True)
    """Any changes to the shared/local configuration updates the generated config."""

    config_setdefault(app.config, "needscfg_write_all", True)
    """Write full config, so the final configuration is visible in one file."""

    config_setdefault(app.config, "needscfg_exclude_defaults", True)
    """Exclude default values from the generated configuration."""

    # This is disabled for right now as it causes a lot of issues
    # While we are not using the generated file anywhere
    config_setdefault(app.config, "needscfg_warn_on_diff", False)
    """Running Sphinx with -W will fail the CI for uncommitted TOML changes."""

    app.config.needscfg_merge_toml_files.append(
        str(Path(__file__).parent / "shared.toml")
    )
    """Merge the static TOML file into the generated configuration."""

    # score_mounts resolves Bazel's JSON manifest during ``config-inited``. Run
    # afterwards and serialize its structured entries here, alongside the rest
    # of the needs-config-writer configuration.
    app.connect(
        "config-inited", lambda app, config: register_mounts(config), priority=500
    )

    app.config.needscfg_relative_path_fields.extend(
        [
            "needs_external_needs[*].json_path",
            {
                "field": "needs_flow_configs.score_config",
                "prefix": "!include ",
            },
        ]
    )
    """Relative paths to confdir for Bazel provided absolute paths."""

    app.config.suppress_warnings += [
        "needs_config_writer.unsupported_type",
        "needs_config_writer.path_conversion",
    ]
    # TODO remove the suppress_warnings once fixed

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
