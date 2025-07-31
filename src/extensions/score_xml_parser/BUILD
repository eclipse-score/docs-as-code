load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@pip_process//:requirements.bzl", "all_requirements")

py_library(
    name = "score_xml_parser",
    srcs = glob(
        ["*.py"],
    ),
    imports = ["."],
    visibility = ["//visibility:public"],
    # TODO: Figure out if all requirements are needed or if we can break it down a bit
    deps = all_requirements + ["@score_docs_as_code//src/extensions/score_source_code_linker:score_source_code_linker"]
)
