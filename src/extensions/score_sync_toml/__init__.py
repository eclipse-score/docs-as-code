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

from src.helper_lib import config_setdefault


def _write_needs_types_toml(app: Sphinx) -> Path:
    """Serialize ``app.config.needs_types`` as ``[[needs.types]]`` TOML entries.

    ``needs_config_writer`` cannot serialize the complex ``ScoreNeedType``
    dicts (it emits an ``unsupported_type`` warning and skips them), so
    ``ubproject.toml`` ends up with no type definitions.  Without those,
    the ubCode language server does not recognise any RST directives as needs
    and indexes nothing.

    This function writes only the fields that ubCode requires to identify
    need directives (``directive``, ``title``, ``prefix``, and optionally
    ``color``/``style``) to a separate TOML file that is then merged into
    ``ubproject.toml`` by ``needs_config_writer``.

    Must be called *after* ``score_metamodel.setup()`` has run (i.e. after
    ``app.config.needs_types`` has been extended with the metamodel types).
    """
    lines: list[str] = [
        "# Auto-generated – do not edit manually.\n",
        "# Contains [[needs.types]] entries derived from metamodel.yaml.\n",
        "# Required for the ubCode language server to recognise need directives.\n\n",
    ]
    for nt in app.config.needs_types:
        lines.append("[[needs.types]]\n")
        lines.append(f'directive = "{nt["directive"]}"\n')
        lines.append(f'title = "{nt["title"]}"\n')
        lines.append(f'prefix = "{nt["prefix"]}"\n')
        if color := nt.get("color"):
            lines.append(f'color = "{color}"\n')
        if style := nt.get("style"):
            lines.append(f'style = "{style}"\n')
        lines.append("\n")

    output_path = Path(app.confdir) / "needs_types_generated.toml"
    output_path.write_text("".join(lines), encoding="utf-8")
    return output_path


def setup(app: Sphinx) -> dict[str, str | bool]:
    """
    Extension to configure needs-config-writer for syncing needs configuration to TOML.

    See https://needs-config-writer.useblocks.com
    """

    config_setdefault(app.config, "needscfg_outpath", "ubproject.toml")
    """Write to the confdir directory."""

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

    app.config.needscfg_exclude_vars = [
        # Default exclusions from needs-config-writer
        "needs_from_toml",
        "needs_from_toml_table",
        "needs_schema_definitions_from_json",
        # Exclude the expanded schema definitions generated from metamodel.yaml.
        # These are managed via schemas.json / score_metamodel and must not be
        # duplicated in ubproject.toml (ubCode only needs schema_definitions_from_json).
        "needs_schema_definitions",
        # needs_render_context contains Python callable objects (draw_full_interface,
        # draw_full_module, etc.) that cannot be serialized to TOML.
        # needs_config_writer emits unsupported_type warnings for these and skips them.
        "needs_render_context",
    ]
    """Exclude resolved/generated config values that don't belong in ubproject.toml."""

    app.config.needscfg_merge_toml_files.append(
        str(Path(__file__).parent / "shared.toml")
    )
    """Merge the static TOML file into the generated configuration."""

    # Write [[needs.types]] from the metamodel into a separate TOML fragment and
    # merge it.  needs_config_writer cannot serialise the complex ScoreNeedType
    # dicts itself (unsupported_type), so ubproject.toml would otherwise contain
    # no type definitions and the ubCode language server would index nothing.
    needs_types_toml = _write_needs_types_toml(app)
    app.config.needscfg_merge_toml_files.append(str(needs_types_toml))
    """Merge the generated [[needs.types]] TOML into the final ubproject.toml."""

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
        "needs_config_writer.path_conversion",
        # needs_render_context values are Python callables; they are excluded via
        # needscfg_exclude_vars above, but suppress the warning as a safety net.
        "needs_config_writer.unsupported_type",
    ]

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
