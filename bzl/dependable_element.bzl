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
"""Prototype of ``dependable_element`` on Sphinx-Needs instead of TRLC/LOBSTER.

Requirements are taken from the ``needs.json`` export of ``docs_bundle``
targets. Unit tests run as build actions, so their ``test.xml`` files are
regular, cacheable artifacts. ``dependable_element`` turns both into a
``needs.json`` with ``testcase`` Needs and checks the traceability rules; the
``<name>_test`` target reports the result. ``docs(dependable_elements = [...])``
feeds the ``needs.json`` back into the documentation build.

Test targets are always ``testonly``; therefore ``component`` and
``dependable_element`` are ``testonly`` as well.
"""

ComponentNeedsInfo = provider(
    doc = "Requirement inventories and executed test reports of a component.",
    fields = {
        "label": "Label of the component.",
        "requirements": "Depset of needs.json files owned by the component.",
        "test_reports": "Depset of test.xml files of the component's tests.",
    },
)

DependableElementNeedsInfo = provider(
    doc = "Traceability outputs of a dependable element.",
    fields = {
        "needs_json": "needs.json with one testcase Need per executed test case.",
        "report": "JSON report of the traceability checks.",
        "summary": "Human-readable summary; the last line is 'RESULT: PASSED|FAILED'.",
    },
)

_INTEGRITY_LEVELS = ["QM", "A", "B", "C", "D"]

# Runs the test binary and keeps its test.xml even if test cases fail.
_RUN_TEST_SCRIPT = """\
set -u
exe="$1"; xml="$PWD/$2"; log="$3"; label="$4"
export TEST_TMPDIR="$(mktemp -d)"
export GTEST_OUTPUT="xml:$xml"
export XML_OUTPUT_FILE="$xml"
rc=0
"$exe" > "$log" 2>&1 || rc=$?
if [ ! -s "$xml" ]; then
  printf '<?xml version="1.0" encoding="UTF-8"?>\\n<testsuites><testsuite name="%s" tests="1" errors="1"><testcase name="%s" classname="%s"><error message="test binary exited with %s without writing test.xml"/></testcase></testsuite></testsuites>\\n' \
    "$label" "$label" "$label" "$rc" > "$xml"
fi
"""

def _bundle_needs_label(bundle):
    """Map a ``docs_bundle`` label to its local Needs export."""
    label = str(bundle)
    if label.startswith(":"):
        label = "//" + native.package_name() + label
    if ":" not in label or "__internal__" in label:
        fail("requirements entries must name docs_bundle targets, got %r" % label)
    return label + ".__internal__.needs_local"

def _run_test(ctx, test):
    # The report path contains "tests-report" so the docs-as-code test.xml
    # parser derives the repository and file path like for CI test reports.
    report_dir = "/".join([
        part
        for part in [ctx.label.name, "tests-report", test.label.workspace_root, test.label.package, test.label.name]
        if part
    ])
    xml = ctx.actions.declare_file(report_dir + "/test.xml")
    log = ctx.actions.declare_file(report_dir + "/test.log")
    files_to_run = test[DefaultInfo].files_to_run
    ctx.actions.run_shell(
        command = _RUN_TEST_SCRIPT,
        arguments = [files_to_run.executable.path, xml.path, log.path, str(test.label)],
        tools = [files_to_run],
        outputs = [xml, log],
        mnemonic = "ScoreComponentTest",
        progress_message = "Running %s for %s" % (test.label, ctx.label),
    )
    return xml, log

def _component_impl(ctx):
    reports = []
    logs = []
    for test in ctx.attr.tests:
        xml, log = _run_test(ctx, test)
        reports.append(xml)
        logs.append(log)
    return [
        DefaultInfo(files = depset(reports)),
        OutputGroupInfo(test_logs = depset(logs)),
        ComponentNeedsInfo(
            label = ctx.label,
            requirements = depset(ctx.files.requirements),
            test_reports = depset(reports),
        ),
    ]

_component = rule(
    implementation = _component_impl,
    attrs = {
        "requirements": attr.label_list(allow_files = [".json"]),
        "tests": attr.label_list(cfg = "target", providers = [DefaultInfo]),
        "implementation": attr.label_list(),
    },
)

def component(name, requirements, tests, implementation = [], **kwargs):
    """A component: requirements from docs bundles, verified by its unit tests.

    Args:
      name: Target name.
      requirements: ``docs_bundle`` targets whose Needs belong to this component.
      tests: Test targets (e.g. ``cc_test`` with GoogleTest); they are executed
        as build actions to obtain their ``test.xml``.
      implementation: Implementation targets of the component.
      **kwargs: Common attributes such as ``visibility``.
    """
    kwargs["testonly"] = True
    _component(
        name = name,
        requirements = [_bundle_needs_label(r) for r in requirements],
        tests = tests,
        implementation = implementation,
        **kwargs
    )

def _dependable_element_impl(ctx):
    components = [c[ComponentNeedsInfo] for c in ctx.attr.components]
    manifest = ctx.actions.declare_file(ctx.label.name + "/manifest.json")
    ctx.actions.write(manifest, json.encode({
        "label": str(ctx.label),
        "integrity_level": ctx.attr.integrity_level,
        "release": ctx.attr.release,
        "requirements": [f.path for f in ctx.files.requirements],
        "components": [
            {
                "label": str(c.label),
                "requirements": [f.path for f in c.requirements.to_list()],
                "test_reports": [f.path for f in c.test_reports.to_list()],
            }
            for c in components
        ],
    }))

    needs_json = ctx.actions.declare_file(ctx.label.name + "/needs.json")
    report = ctx.actions.declare_file(ctx.label.name + "/trace_report.json")
    summary = ctx.actions.declare_file(ctx.label.name + "/trace_report.txt")
    ctx.actions.run(
        executable = ctx.executable._trace_tool,
        arguments = [
            "--manifest",
            manifest.path,
            "--needs-out",
            needs_json.path,
            "--report-out",
            report.path,
            "--summary-out",
            summary.path,
        ],
        inputs = depset(
            [manifest] + ctx.files.requirements,
            transitive = [c.requirements for c in components] + [c.test_reports for c in components],
        ),
        outputs = [needs_json, report, summary],
        mnemonic = "ScoreDependableElementTrace",
        progress_message = "Checking traceability of %s" % ctx.label,
    )
    return [
        DefaultInfo(files = depset([needs_json])),
        OutputGroupInfo(report = depset([report, summary])),
        DependableElementNeedsInfo(needs_json = needs_json, report = report, summary = summary),
    ]

_dependable_element = rule(
    implementation = _dependable_element_impl,
    attrs = {
        "components": attr.label_list(providers = [ComponentNeedsInfo], mandatory = True),
        "requirements": attr.label_list(allow_files = [".json"]),
        "integrity_level": attr.string(mandatory = True, values = _INTEGRITY_LEVELS),
        "release": attr.bool(default = False),
        "_trace_tool": attr.label(
            default = Label("//scripts_bazel:dependable_element_trace"),
            cfg = "exec",
            executable = True,
        ),
    },
)

def _dependable_element_test_impl(ctx):
    summary = ctx.attr.dependable_element[DependableElementNeedsInfo].summary
    script = ctx.actions.declare_file(ctx.label.name + ".sh")
    ctx.actions.write(
        script,
        "#!/usr/bin/env bash\ncat '{s}'\ntail -n 1 '{s}' | grep -qx 'RESULT: PASSED'\n".format(
            s = summary.short_path,
        ),
        is_executable = True,
    )
    return [DefaultInfo(executable = script, runfiles = ctx.runfiles(files = [summary]))]

_dependable_element_test = rule(
    implementation = _dependable_element_test_impl,
    attrs = {
        "dependable_element": attr.label(providers = [DependableElementNeedsInfo], mandatory = True),
    },
    test = True,
)

def dependable_element(
        name,
        components,
        integrity_level,
        requirements = [],
        release = False,
        **kwargs):
    """A dependable element with Sphinx-Needs based traceability.

    Creates ``<name>`` (``needs.json`` with the executed test cases, report in
    output group ``report``) and the test ``<name>_test``.

    Args:
      name: Target name.
      components: ``component`` targets of this element.
      integrity_level: One of QM, A, B, C, D. Requirements with a higher
        ``safety`` level are reported as errors.
      requirements: Additional ``docs_bundle`` targets (e.g. feature
        requirements) used to resolve references of the test cases.
      release: When False, unverified requirements are warnings; when True,
        they fail ``<name>_test``.
      **kwargs: Common attributes such as ``visibility``.
    """
    kwargs["testonly"] = True
    _dependable_element(
        name = name,
        components = components,
        integrity_level = integrity_level,
        requirements = [_bundle_needs_label(r) for r in requirements],
        release = release,
        **kwargs
    )
    _dependable_element_test(
        name = name + "_test",
        dependable_element = ":" + name,
        visibility = kwargs.get("visibility"),
        tags = kwargs.get("tags", []),
    )
