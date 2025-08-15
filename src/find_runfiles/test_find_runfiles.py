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

# TODO: why is there an __init__.py file in tooling?
from src import find_runfiles


def get_runfiles_dir_impl(
    cwd: str, conf_dir: str, env_runfiles: str | None, git_root: str
):
    return str(
        find_runfiles.get_runfiles_dir_impl(
            cwd=Path(cwd),
            conf_dir=Path(conf_dir),
            env_runfiles=Path(env_runfiles) if env_runfiles else None,
            git_root=Path(git_root),
        )
    )


def test_run_incremental():
    """bazel run //process-docs:incremental"""
    # in incremental.py:
    assert get_runfiles_dir_impl(
        cwd="/home/vscode/.cache/bazel/_bazel_vscode/6084288f00f33db17acb4220ce8f1999/execroot/_main/bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles/_main",
        conf_dir="process-docs",
        env_runfiles="/home/vscode/.cache/bazel/_bazel_vscode/6084288f00f33db17acb4220ce8f1999/execroot/_main/bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles",
        git_root="/workspaces/process",
    ) == (
        "/workspaces/process/bazel-out/k8-fastbuild/bin/process-docs/"
        "incremental.runfiles"
    )

    # in conf.py:
    assert get_runfiles_dir_impl(
        cwd="/workspaces/process/process-docs",
        conf_dir="process-docs",
        env_runfiles="/home/vscode/.cache/bazel/_bazel_vscode/6084288f00f33db17acb4220ce8f1999/execroot/_main/bazel-out/k8-fastbuild/bin/process-docs/incremental.runfiles",
        git_root="/workspaces/process",
    ) == (
        "/workspaces/process/bazel-out/k8-fastbuild/bin/process-docs/"
        "incremental.runfiles"
    )


def test_build_incremental_and_exec_it():
    """bazel build //process-docs:incremental && bazel-bin/process-docs/incremental"""
    assert (
        get_runfiles_dir_impl(
            cwd="/workspaces/process/process-docs",
            conf_dir="process-docs",
            env_runfiles="bazel-bin/process-docs/incremental.runfiles",
            git_root="/workspaces/process",
        )
        == "/workspaces/process/bazel-bin/process-docs/incremental.runfiles"
    )


def test_esbonio_old():
    """Observed with esbonio 0.x"""
    assert (
        get_runfiles_dir_impl(
            cwd="/workspaces/process/process-docs",
            conf_dir="process-docs",
            env_runfiles=None,
            git_root="/workspaces/process",
        )
        == "/workspaces/process/bazel-bin/process-docs/ide_support.runfiles"
    )


def test3():
    # docs named differently, just to make sure nothing is hardcoded
    # bazel run //other-docs:incremental
    assert get_runfiles_dir_impl(
        cwd="/workspaces/process/other-docs",
        conf_dir="other-docs",
        env_runfiles="/home/vscode/.cache/bazel/_bazel_vscode/6084288f00f33db17acb4220ce8f1999/execroot/_main/bazel-out/k8-fastbuild/bin/other-docs/incremental.runfiles",
        git_root="/workspaces/process",
    ) == (
        "/workspaces/process/bazel-out/k8-fastbuild/bin/other-docs/incremental.runfiles"
    )
