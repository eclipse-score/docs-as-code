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
"""Copy the ``expected_*.json`` golden files with their placeholders filled in.

The golden files contain placeholders such as ``"@LOCAL_REPO@"`` instead of
values that are defined in code. That way a changed constant does not require
editing every golden file by hand.
"""

import json
from pathlib import Path

from src.helper_lib.repo_info import LOCAL_REPO

# Placeholder string as it appears in the golden JSON => value it stands for.
GOLDEN_FILE_PLACEHOLDERS: dict[str, str] = {
    "@LOCAL_REPO@": LOCAL_REPO,
}


def copy_golden_file(source: Path, target: Path) -> None:
    """Copy ``source`` to ``target`` and replace all placeholders.

    Placeholders are replaced in their JSON-encoded form (with quotes), so the
    result stays valid JSON even if a value contains special characters.
    The replacement happens at copy time because some golden files are also
    used as input for the Sphinx build, not only for comparison.
    """
    text = source.read_text(encoding="utf-8")
    for placeholder, value in GOLDEN_FILE_PLACEHOLDERS.items():
        text = text.replace(json.dumps(placeholder), json.dumps(value))
    target.write_text(text, encoding="utf-8")
