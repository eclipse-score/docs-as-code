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

# Must match the `python_version` of the `pip.parse()` for `docs_as_code_hub_env`
# in MODULE.bazel. The wheels in that hub are only available for this version, so
# the test target is pinned to it. Otherwise a consumer module whose default Python
# toolchain differs would fail analysis with "No matching wheel for current
# configuration's Python version".
_PYTHON_VERSION = "3.12"

# Taken from the documentation: https://sphinx-test-reports.readthedocs.io/en/latest/pytest.html#declaring-the-properties
# Current version of sphinx-test-reports: 2.0.0
_TEST_REPORTS_PROPERTIES = [
    "partially_verifies = PartiallyVerifies, list",
    "fully_verifies = FullyVerifies, list",
    "test_type = TestType",
    "derivation_technique = DerivationTechnique",
]

def score_pytest(name, srcs, args = [], data = [], deps = [], env = {}, plugins = [], pytest_config = None, **kwargs):
    pytest_bootstrap = Label("@score_docs_as_code//score_pytest:main.py")

    if not pytest_config:
        pytest_config = Label("@score_docs_as_code//score_pytest:pytest.ini")

    if not srcs:
        fail("No source files provided for %s! (Is your glob empty?)" % name)

    plugins = ["-p sphinxcontrib.test_reports.pytest_plugin"] + ["-p %s" % plugin for plugin in plugins]

    # Everything score_pytest needs to run is injected here, so that consumers only
    # have to depend on this module via bazel. They do not have to add pytest or
    # sphinx-test-reports to their own requirements.
    # `requirement()` returns canonical labels (`@@rules_python++pip+docs_as_code_hub_env//...`),
    # which resolve from any module, independent of the caller's repo mapping.
    for pkg in ["pytest", "sphinx-test-reports"]:
        docs_dep = requirement(pkg)
        label_suffix = docs_dep[docs_dep.index("//"):]
        already_in_deps = False
        for dep in deps:
            if str(dep).endswith(label_suffix):
                # if str(dep) != docs_dep:
                #     fail("Please do not provide your own %s version. We want to use the same %s version everywhere." % (pkg, pkg))
                already_in_deps = True
        if not already_in_deps:
            deps = deps + [docs_dep]

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
               # Extra here so we can make sure they are appended last to the args
               [
                   "-o junit_family=xunit1",
                   "-o 'test_reports_properties=%s'" % "\n".join(_TEST_REPORTS_PROPERTIES),
               ] +
               plugins +
               ["$(location %s)" % x for x in srcs],
        deps = deps,  #["@score_docs_as_code//score_pytest:attribute_plugin"],
        data = [
            pytest_config,
        ] + data,
        env = env | {
            "PYTHONDONOTWRITEBYTECODE": "1",
        },
        python_version = _PYTHON_VERSION,
        **kwargs
    )
