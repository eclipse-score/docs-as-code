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
from sphinx.application import Sphinx
from pathlib import Path


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Global settings
    # Note: the "sub-extensions" also set their own config values

    app.config.needscfg_outpath = "ubproject.toml"
    """Write to the confdir directory."""

    app.config.needscfg_overwrite = True
    """Any changes to the shared/local configuration shall update the generated config file."""

    app.config.needscfg_write_all = True
    """Write full config, so the final configuration is visible in one file."""

    app.config.needscfg_warn_on_diff = True
    """Be sure to update this - running Sphinx with -W will fail the CI, that's wanted."""

    app.config.needscfg_merge_toml_files = [
        str(Path(__file__).parent / "shared.toml"),
    ]

    app.config.suppress_warnings += [
        "needs_config_writer.unsupported_type",
        "ubproject.path_conversion",
    ]
    # TODO remove the suppress_warnings once fixed

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
