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

load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("//:bzl/mount_rules.bzl", "create_composition_manifest")
load("//:docs.bzl", "docs", "docs_bundle")
load(":custom_generator.bzl", "custom_source_generator")
load(":dependency_probe.bzl", "dependency_probe")

exports_files([
    "child/example.cc",
    "child/example_api.h",
])

docs_bundle(
    name = "child",
    code_targets = [
        ":example_binary",
        ":example_executable",
        ":external_dependency_probe",
        ":dependency_entrypoint",
        ":generated_implementation",
        ":custom_generated_implementation",
        ":custom_generated_assembly",
        ":mixed_py_sources",
        ":mixed_genrule_outputs",
        ":mixed_filegroup_sources",
        ":nested_mixed_filegroup_sources",
        ":local_dependency_probe",
        ":nested_filegroup_sources",
        ":selected_with_sibling_files",
        "//src/tests/docs_bzl/scenarios/basic_docs:nested_bundles_outside_gateway",
    ],
    entry_doc = "landing",
    source_dir = "child",
)

filegroup(
    name = "filegroup_sources",
    srcs = ["child/filegroup_source.py"],
)

# Repeat paths, cross a subpackage, and verify traversal stops at siblings.
filegroup(
    name = "nested_filegroup_sources",
    srcs = [
        ":example_library",
        ":filegroup_sources",
        "//src/tests/docs_bzl/scenarios/nested_bundles/subpackage:sub_dependency",
    ],
)

# Simulated generated doc output consumed via the `data` attribute.
filegroup(
    name = "generated_doc_output",
    srcs = ["generated/generated_output.txt"],
    visibility = ["//visibility:private"],
)

py_binary(
    name = "example_binary",
    srcs = ["child/example.py"],
    main = "child/example.py",
)

cc_library(
    name = "example_library",
    srcs = ["child/example.cc"],
    hdrs = ["child/example_api.h"],
    visibility = ["//visibility:public"],
)

# Only reachable through a dependency in a sibling package; it must be omitted
# when that out-of-boundary dependency cuts off the traversal branch.
cc_library(
    name = "branch_only_library",
    srcs = ["child/example_main.cc"],
    visibility = ["//visibility:public"],
)

# Generated sources and headers are the implementation artifacts. The inputs
# below are generator data and must not be exported in this target's file list.
genrule(
    name = "generated_component_source",
    srcs = ["child/example.cc"],
    outs = ["generated/generated_component.cc"],
    cmd = "cp $< $@",
)

genrule(
    name = "generated_component_header",
    srcs = ["child/example_api.h"],
    outs = ["generated/generated_component.h"],
    cmd = "cp $< $@",
)

cc_library(
    name = "generated_implementation",
    srcs = [":generated_component_source"],
    hdrs = [":generated_component_header"],
)

# Custom Starlark generators publish generated code through DefaultInfo.files.
# Their srcs are inputs used to create those files, not implementation files.
custom_source_generator(
    name = "custom_generated_source",
    srcs = ["child/example_main.cc"],
    out = "generated/custom_generated_component.cc",
)

custom_source_generator(
    name = "custom_generated_header",
    srcs = ["child/example_api.h"],
    out = "generated/custom_generated_component.h",
)

# Assembly output has a different extension from the generator input. The
# source file list and sourcelink cache must contain the generated artifact,
# not the text input that the generator reads.
custom_source_generator(
    name = "custom_generated_assembly",
    srcs = ["child/generator_input.txt"],
    out = "generated/custom_generated_component.S",
)

# aspect_rules_py forwards all py_library srcs through DefaultInfo.files. Keep
# one handwritten module beside a generated module to ensure the collector
# retains both files when a library consumes generator output.
custom_source_generator(
    name = "mixed_py_generated",
    srcs = ["child/mixed_py_manual.py"],
    out = "generated/mixed_py_generated.py",
)

py_library(
    name = "mixed_py_sources",
    srcs = [
        "child/mixed_py_manual.py",
        ":mixed_py_generated",
    ],
)

# This generated file is reachable only through the mixed filegroups below.
# Its unique path lets the source-link golden prove that filegroups forward
# generator outputs instead of contributing only their ordinary source files.
custom_source_generator(
    name = "filegroup_generated_assembly",
    srcs = ["child/generator_input.txt"],
    out = "generated/filegroup_generated_component.S",
)

# This action produces both a commonly listed C++ source and an assembly
# source. Treat both outputs as implementation files and omit its text input.
genrule(
    name = "mixed_genrule_outputs",
    srcs = ["child/generator_input.txt"],
    outs = [
        "generated/genrule_component.cc",
        "generated/genrule_component.S",
    ],
    cmd = "cp $< $(location :generated/genrule_component.cc) && " +
          "cp $< $(location :generated/genrule_component.S)",
)

# A filegroup forwards its ordinary source and generated assembly output. Both
# must remain in the bundle manifest and the source-link collection.
filegroup(
    name = "mixed_filegroup_sources",
    srcs = [
        "child/filegroup_manual.cc",
        ":filegroup_generated_assembly",
    ],
)

# A second filegroup layer verifies that forwarding behavior is preserved
# through nested filegroups as well as for the directly selected target above.
filegroup(
    name = "nested_mixed_filegroup_sources",
    srcs = [
        "child/example_api.h",
        ":mixed_filegroup_sources",
    ],
)

cc_library(
    name = "custom_generated_implementation",
    srcs = [":custom_generated_source"],
    hdrs = [":custom_generated_header"],
)

# Source and header declarations resolve through sibling-package filegroups.
# Their files belong to this selected implementation despite those labels.
cc_library(
    name = "selected_with_sibling_files",
    srcs = ["//src/tests/docs_bzl/scenarios/basic_docs:nested_bundles_source_files"],
    hdrs = ["//src/tests/docs_bzl/scenarios/basic_docs:nested_bundles_header_files"],
)

# An in-boundary dependency owns these source and header declarations even
# though their nested filegroups live in a sibling package. Its selected
# entrypoint must retain both files while stopping traversal at those groups.
cc_library(
    name = "dependency_with_sibling_files",
    srcs = ["//src/tests/docs_bzl/scenarios/basic_docs:nested_bundles_source_files"],
    hdrs = ["//src/tests/docs_bzl/scenarios/basic_docs:nested_bundles_header_files"],
)

cc_library(
    name = "dependency_entrypoint",
    deps = [":dependency_with_sibling_files"],
)

# This local target reaches a sibling-package dependency that points back into
# the bundle package. The sibling source and its branch_only_library dependency
# must both be excluded from this target's file list.
cc_library(
    name = "local_dependency_probe",
    srcs = ["child/example.cc"],
    deps = ["//src/tests/docs_bzl/scenarios/basic_docs:nested_bundles_sibling_bridge"],
)

# The custom probe permits a filegroup dependency from another repository so
# the manifest verifies that repository boundaries stop dependency traversal.
dependency_probe(
    name = "external_dependency_probe",
    deps = ["@bazel_tools//tools:bzl_srcs"],
)

cc_binary(
    name = "example_executable",
    srcs = ["child/example_main.cc"],
    visibility = ["//visibility:public"],
    deps = [":example_library"],
)

# The child is nested below the parent bundle before the parent itself is
# mounted into the synthetic host tree below.
# BEGIN docs-bundle-howto: parent-composition
docs_bundle(
    name = "parent",
    bundles = [{
        "bundle": ":child",
        "mount_at": "child",
    }],
    data = [":generated_doc_output"],
    source_dir = "parent",
    visibility = ["//visibility:public"],
)
# END docs-bundle-howto: parent-composition

# An aggregator deliberately has no source_dir. It only propagates its child
# and must preserve the declaration order in the generated manifest.
docs_bundle(
    name = "ordered_aggregate",
    bundles = [
        {
            "bundle": ":other",
            "mount_at": "first",
        },
        {
            "bundle": ":child",
            "mount_at": "second",
        },
    ],
)

docs_bundle(
    name = "other",
    source_dir = "other",
)

create_composition_manifest(
    name = "ordered_aggregate_manifest",
    bundle = ":ordered_aggregate",
)

# A complete docs() invocation is the synthetic host project driven by the
# pytest integration test in //src/tests/docs_bzl.
docs(
    bundles = [{
        "bundle": ":parent",
        "mount_at": "concepts/example_bundle",
        # Attach to the second toctree (index 1) of concepts/index.rst.
        "toctree_index": 1,
    }],
    code_targets = [":example_binary"],
    source_dir = "host_docs",
    test_sources = ["src/tests/docs_bzl/scenarios/nested_bundles"],
)
