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
"""Command-line interface for creating documentation delta reports."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from .comparison import DocsDeltaError, compare_needs, load_needs
from .github import github_pull_request, resolve_urls, resolved_baseline, workspace_path
from .rendered_html import compare_html
from .report import render_report, unavailable_report, write_report


def argument_parser() -> argparse.ArgumentParser:
    """Describe the local and GitHub Actions forms of the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        help="directory baseline; defaults to automatic gh-pages mode in PR Actions",
    )
    parser.add_argument(
        "--baseline-mode",
        choices=("directory", "gh-pages"),
        help="baseline source; inferred when omitted",
    )
    parser.add_argument(
        "--gh-pages-dir",
        type=Path,
        help="local full-history gh-pages checkout (defaults to .docs-baseline)",
    )
    parser.add_argument(
        "--current-dir",
        type=Path,
        help="current documentation directory (defaults to docs-artifact)",
    )
    parser.add_argument("--base-url")
    parser.add_argument("--pr-url")
    parser.add_argument(
        "--output",
        type=Path,
        help="report path (defaults to docs-artifact/docs-delta.md)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and write either a delta or an explicit unavailable report.

    A baseline may legitimately be absent while publishing is in progress; in
    that case the report is still successful and explains why it has no delta.
    Missing or malformed current build data is an error because it would make
    even the PR side of the comparison unreliable.
    """

    args = argument_parser().parse_args(argv)
    try:
        pull_request = github_pull_request(os.environ)
        current_dir = args.current_dir or workspace_path(os.environ, "docs-artifact")
        output = args.output or current_dir / "docs-delta.md"

        with resolved_baseline(args, pull_request, os.environ) as (
            baseline_dir,
            baseline_reason,
        ):
            if baseline_dir is None or not baseline_dir.is_dir():
                # A stale baseline would produce a plausible but misleading
                # diff. Surface the missing comparison in the comment instead.
                reason = baseline_reason or f"directory is missing: {baseline_dir}"
                write_report(output, unavailable_report(reason))
                return 0
            try:
                baseline_needs = load_needs(baseline_dir)
            except DocsDeltaError as exc:
                write_report(output, unavailable_report(str(exc)))
                return 0

            if not current_dir.is_dir():
                raise DocsDeltaError(
                    f"documentation directory is missing: {current_dir}"
                )
            current_needs = load_needs(current_dir)
            base_url, pr_url = resolve_urls(args, pull_request, os.environ)
            report = render_report(
                compare_needs(baseline_needs, current_needs),
                compare_html(baseline_dir, current_dir),
                base_url=base_url,
                pr_url=pr_url,
            )
            write_report(output, report)
    except (DocsDeltaError, OSError) as exc:
        print(f"docs_delta: error: {exc}", file=sys.stderr)
        return 2
    return 0
