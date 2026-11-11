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
"""Exercise the built PlantUML launcher through Sphinx's direct invocation."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("runfiles_mode", ["directory", "inferred", "manifest"])
def test_direct_launcher_renders_svg_without_bazel_args(
    runfiles_mode: str,
    tmp_path: Path,
) -> None:
    """A nested launcher must find its native binary and preserve renderer arguments.

    This runs against the generated executable in the test's real runfiles tree,
    including when this test target is used from a downstream Bazel module.
    """
    launcher = Path(__file__).absolute().with_name("plantuml")
    env = os.environ.copy()
    for key in ("RUNFILES_DIR", "RUNFILES_MANIFEST_FILE", "JAVA_RUNFILES"):
        env.pop(key, None)
    runfiles = Path(os.environ["TEST_SRCDIR"])
    if runfiles_mode == "directory":
        env["RUNFILES_DIR"] = str(runfiles)
    elif runfiles_mode == "manifest":
        # Copy the real generated script outside the tree so discovery must use
        # the manifest, as on systems without runfiles directory symlinks.
        launcher = Path(shutil.copyfile(launcher, tmp_path / "plantuml"))
        launcher.chmod(0o755)
        # Sandboxed tests need not contain Bazel's outer MANIFEST. Map the
        # actual inputs from this test's tree into a standalone manifest.
        manifest = tmp_path / "MANIFEST"
        manifest.write_text(
            "".join(
                f"{file.relative_to(runfiles)} {file}\n"
                for file in runfiles.rglob("*")
                if file.is_file()
            )
        )
        env["RUNFILES_MANIFEST_FILE"] = str(manifest)
    result = subprocess.run(
        [str(launcher), "-tsvg", "-pipe"],
        input="@startuml\nAlice -> Bob: direct launcher\n@enduml\n",
        capture_output=True,
        check=False,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert "<svg" in result.stdout, result.stdout
    assert "direct launcher" in result.stdout
