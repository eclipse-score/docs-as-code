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
"""Black-box coverage for an external consumer mounting a data-backed bundle."""

import subprocess
from pathlib import Path

from src.tests.docs_bzl.helpers import repo_root, run_scenario


def _write_consumer(workspace: Path, source_root: Path) -> None:
    """Create a minimal Bzlmod consumer for the public provider bundle."""
    subprocess.run(["git", "init", "--quiet", str(workspace)], check=True)
    (workspace / ".bazelversion").write_text(
        (source_root / ".bazelversion").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (workspace / "MODULE.bazel").write_text(
        f'''module(name = "literalinclude_consumer")
bazel_dep(name = "rules_python", version = "1.8.5")
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(is_default = True, python_version = "3.12")
bazel_dep(name = "score_docs_as_code", version = "8.1.0")
local_path_override(module_name = "score_docs_as_code", path = "{source_root}")
''',
        encoding="utf-8",
    )
    (workspace / "BUILD").write_text(
        """load("@score_docs_as_code//:docs.bzl", "docs")

docs(
    source_dir = "docs",
    project = "Literalinclude Consumer",
    project_url = "https://example.invalid/literalinclude-consumer",
    bundles = [{
        "bundle": "@score_docs_as_code//src/tests/docs_bzl/scenarios/bundle_data_provider:docs_bundle",
        "mount_at": "provider",
    }],
)
""",
        encoding="utf-8",
    )
    docs = workspace / "docs"
    docs.mkdir()
    (docs / "index.rst").write_text(
        """Literalinclude Consumer
========================

The provider bundle is mounted below this page.
""",
        encoding="utf-8",
    )


def test_external_consumer_can_render_data_backed_literalincludes(
    tmp_path: Path,
) -> None:
    """A Bzlmod consumer can render a provider's original literalinclude path."""
    source_root = repo_root()
    _write_consumer(tmp_path, source_root)

    result = subprocess.run(
        [
            "bazel",
            "--batch",
            f"--output_user_root={tmp_path / '.bazel_output'}",
            f"--bazelrc={source_root / '.bazelrc'}",
            "run",
            # local_path_override cannot run the source-link helper in a
            # sandbox in this consumer setup; keep the Sphinx action sandboxed.
            "--strategy=MergeBundleSourcelinks=local",
            "//:docs",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    provider_page = tmp_path / "_build" / "provider" / "index.html"
    assert provider_page.is_file()
    assert "filegroup" in provider_page.read_text(encoding="utf-8")


def test_sandboxed_needs_build_stages_nested_bundle_supporting_files() -> None:
    """A nested data bundle supplies the original BUILD path to Sphinx."""
    run_scenario("build", "bundle_data_provider", ":needs_json")
