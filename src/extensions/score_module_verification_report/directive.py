# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
"""The ``.. module-verification-report::`` Sphinx directive."""
from __future__ import annotations

import os

import yaml
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles

from .coverage import load_coverage_summary
from .rendering import render_report
from .scanner import discover_components, module_includes
from .templates import DEFAULT_FEATURE_WORKPRODUCTS, DEFAULT_WORKPRODUCTS


class ModuleVerificationReportDirective(SphinxDirective):
    """Expand to the per-module verification report body.

    Discovers components dynamically from the sphinx-needs data model by
    filtering all needs by ``type == "comp"`` and
    ``id.startswith(component_prefix)``.
    """

    required_arguments = 0
    optional_arguments = 0
    option_spec = {"config": str}
    has_content = False

    def _load_config(self, rel_config: str | None) -> dict:
        if not rel_config:
            return {}
        srcdir = self.env.srcdir
        config_path = os.path.join(srcdir, rel_config)
        if not os.path.isfile(config_path):
            self.state_machine.reporter.warning(
                f"module-verification-report: config not found: {config_path}",
                line=self.lineno,
            )
            return {}
        with open(config_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        self.env.note_dependency(config_path)
        return data

    def run(self) -> list[nodes.Node]:
        config = self._load_config(self.options.get("config"))

        module_id = config.get("module_id", "")
        component_prefix = config.get("component_prefix") or (
            "comp__" + module_id[len("mod__"):] + "_"
            if module_id.startswith("mod__")
            else "comp__"
        )
        module_short = (
            module_id[len("mod__"):]
            if module_id.startswith("mod__")
            else module_id
        )
        feature_id = config.get("feature_id") or f"feat__{module_short}"
        feature_slug = (
            feature_id.split("__", 1)[1]
            if "__" in feature_id
            else feature_id
        )
        workproducts = config.get("workproducts") or DEFAULT_WORKPRODUCTS
        feature_workproducts = (
            config.get("feature_workproducts") or DEFAULT_FEATURE_WORKPRODUCTS
        )
        overrides_by_id: dict[str, dict] = config.get("overrides") or {}

        all_needs = getattr(self.env, "module_verification_report_needs", [])
        include_ids = module_includes(all_needs, module_id)
        if include_ids is None:
            error = self.state_machine.reporter.error(
                f"module-verification-report: no '.. mod::' need with "
                f"id '{module_id}' found in the source tree "
                f"(is 'module_id' set correctly in the config?)",
                line=self.lineno,
            )
            return [error]

        components = discover_components(
            self.env, component_prefix, include_ids
        )
        missing = set(include_ids) - {c["id"] for c in components}
        for m in sorted(missing):
            required = include_ids[m]
            hint = f" (version=={required})" if required else ""
            self.state_machine.reporter.warning(
                f"module-verification-report: '{module_id}' includes "
                f"'{m}'{hint} but no matching '.. comp::' need was found",
                line=self.lineno,
            )
        if not components:
            error = self.state_machine.reporter.error(
                f"module-verification-report: '{module_id}' has no "
                f"resolvable components in ':includes:'",
                line=self.lineno,
            )
            return [error]

        coverage_data = load_coverage_summary(self.env)

        rst_text = render_report(
            components,
            feature_id,
            feature_slug,
            overrides_by_id,
            workproducts,
            feature_workproducts,
            coverage_data,
        )
        view_list = ViewList()
        source = "<module-verification-report>"
        for lineno, line in enumerate(rst_text.splitlines()):
            view_list.append(line, source, lineno)

        # Parse into a plain container (not a ``nodes.section``): a section
        # wrapper would push every heading we emit one level deeper than the
        # surrounding document sections, so ``Component Overview`` would
        # render as ``<h4>`` instead of ``<h3>`` alongside
        # ``Feature Requirements Statistics``.
        container = nodes.container()
        container.document = self.state.document
        nested_parse_with_titles(self.state, view_list, container)
        return container.children
