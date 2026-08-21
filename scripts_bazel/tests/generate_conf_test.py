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
"""Tests for the default Sphinx configuration generator."""

from pathlib import Path

from scripts_bazel.generate_conf import generate_conf


def test_generate_conf_uses_module_name_without_first_prefix(tmp_path: Path) -> None:
    module_file = tmp_path / "MODULE.bazel"
    module_file.write_text(
        'module(\n    name = "score_docs_as_code",\n    version = "1.0.0"\n)\n',
        encoding="utf-8",
    )
    template = tmp_path / "default_conf.py.tpl"
    template.write_text(
        "project = {PROJECT}\n"
        "project_url = {PROJECT_URL}\n"
        "required_in_id = {REQUIRED_IN_ID}\n",
        encoding="utf-8",
    )
    output = tmp_path / "conf.py"

    generate_conf(
        template=template,
        module_file=module_file,
        project="Docs-as-Code",
        project_url="https://example.invalid/docs",
        output=output,
    )

    assert output.read_text(encoding="utf-8") == (
        'project = "Docs-as-Code"\n'
        'project_url = "https://example.invalid/docs"\n'
        'required_in_id = ["docs_as_code"]\n'
    )
