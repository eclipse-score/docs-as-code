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

"""Verify that genrule-generated RST files are reachable at ``bazel run`` time.

The ``data`` attribute of ``docs_bundle`` carries genrule outputs that live
in ``bazel-out/.../bin/``.  The fix in ``_external_docs_runfiles_impl`` stages
them into the runfiles of ``:docs``; ``score_mounts`` then resolves the
execroot-relative paths against ``<ws_root>/bazel-bin`` and mounts them.  This
end-to-end test fails if either half of that chain regresses."""

from src.tests.docs_bzl.helpers import run_scenario


def test_data_files_reachable_at_runtime():
    """Genrule output in a docs_bundle data dep must be resolved by Sphinx."""
    result = run_scenario("run", "data_files_runfiles", ":docs")

    generated_html = result.build_dir / "data_test" / "index.html"

    assert "Generated Data Page" in generated_html.read_text(encoding="utf-8")
