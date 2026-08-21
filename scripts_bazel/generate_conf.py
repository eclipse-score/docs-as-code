# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Generate the default Sphinx configuration for a Bazel module."""

import argparse
import json
import re
from pathlib import Path


def module_name_without_prefix(module_file: Path) -> str:
    """Read a module name and remove its first underscore-separated prefix."""
    module_contents = module_file.read_text(encoding="utf-8")
    match = re.search(
        r"\bmodule\s*\(.*?\bname\s*=\s*[\"']([^\"']+)[\"']",
        module_contents,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"could not find module(name = ...) in {module_file}")

    module_name = match.group(1)
    return module_name.split("_", maxsplit=1)[-1]


def generate_conf(
    template: Path,
    module_file: Path,
    project: str,
    project_url: str,
    output: Path,
) -> None:
    """Expand the default configuration template."""
    substitutions = {
        "{PROJECT}": json.dumps(project),
        "{PROJECT_URL}": json.dumps(project_url),
        "{REQUIRED_IN_ID}": json.dumps([module_name_without_prefix(module_file)]),
    }
    contents = template.read_text(encoding="utf-8")
    for placeholder, value in substitutions.items():
        contents = contents.replace(placeholder, value)
    output.write_text(contents, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--module-file", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--project-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate_conf(
        template=args.template,
        module_file=args.module_file,
        project=args.project,
        project_url=args.project_url,
        output=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
