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
"""Regression tests for PlantUML's Bazel launcher runfiles resolution."""

import os
import subprocess
from pathlib import Path


def test_launcher_resolves_binary_from_containing_runfiles_tree(tmp_path: Path) -> None:
    """The IDE launcher is nested in another target's runfiles tree."""
    runfiles = tmp_path / "ide_support.runfiles"
    launcher = runfiles / "_main" / "src" / "plantuml"
    binary = runfiles / "plantuml_native_linux_amd64" / "plantuml"
    launcher.parent.mkdir(parents=True)
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$*\"\n")
    binary.chmod(0o755)
    launcher.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ -n \"${RUNFILES_DIR:-}\" ]]; then
  runfiles=\"$RUNFILES_DIR\"
elif [[ -d \"$0.runfiles\" ]]; then
  runfiles=\"$0.runfiles\"
elif [[ \"$0\" == *.runfiles/* ]]; then
  runfiles=\"${0%.runfiles/*}.runfiles\"
else
  echo \"Cannot locate PlantUML runfiles directory\" >&2
  exit 1
fi
exec \"$runfiles/plantuml_native_linux_amd64/plantuml\" \"$@\"
"""
    )
    launcher.chmod(0o755)

    env = os.environ.copy()
    for key in ("RUNFILES_DIR", "RUNFILES_MANIFEST_FILE", "JAVA_RUNFILES"):
        env.pop(key, None)
    result = subprocess.run(
        [str(launcher), "-version"],
        capture_output=True,
        check=False,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "-version"
