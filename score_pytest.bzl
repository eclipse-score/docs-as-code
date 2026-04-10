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
"""Bazel interface for running pytest"""

load("@docs_as_code_hub_env//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_test")

def score_pytest(name, srcs, args = [], data = [], deps = [], env = {}, plugins = [], pytest_config = None, **kwargs):
    pytest_bootstrap = Label("@score_docs_as_code//score_pytest:main.py")

    if not pytest_config:
        pytest_config = Label("@score_docs_as_code//score_pytest:pytest.ini")

    if not srcs:
        fail("No source files provided for %s! (Is your glob empty?)" % name)

    plugins = ["-p attribute_plugin"] + ["-p %s" % plugin for plugin in plugins]

    docs_pytest = requirement("pytest")
    pytest_in_deps = False
    for dep in deps:
        if "//pytest:pkg" in str(dep):
            if str(dep) != str(docs_pytest):
                fail("Please do not provide your own pytest version. We want to use the same pytest version everywhere.")
            pytest_in_deps = True
    if not pytest_in_deps:
        deps = deps + [docs_pytest]

    py_test(
        name = name,
        srcs = [
            pytest_bootstrap,
        ] + srcs,
        main = pytest_bootstrap,
        args = [
                   "-c $(location %s)" % pytest_config,
                   "-p no:cacheprovider",

                   # XML_OUTPUT_FILE: Location to which test actions should write a test
                   # result XML output file. Otherwise, Bazel generates a default XML
                   # output file wrapping the test log as part of the test action. The XML
                   # schema is based on the JUnit test result schema.
                   "--junitxml=$$XML_OUTPUT_FILE",
               ] +
               args +
               plugins +
               ["$(location %s)" % x for x in srcs],
        deps = deps + ["@score_docs_as_code//score_pytest:attribute_plugin"],
        data = [
            pytest_config,
        ] + data,
        env = env | {
            "PYTHONDONOTWRITEBYTECODE": "1",
        },
        **kwargs
    )
