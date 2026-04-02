load(
    "@score_tooling//bazel/rules/rules_score:sphinx_toolchain.bzl",
    "sphinx_toolchain",
)
# ============================================================================
# Toolchain for the score build
# ============================================================================
py_binary(
    name = "score_build",
    srcs = ["@score_tooling//bazel/rules/rules_score:src/sphinx_wrapper.py"],
    data = [],
    env = {
        "SOURCE_DIRECTORY": "",
        "DATA": "",
        "ACTION": "check",
    },
    main = "@score_tooling//bazel/rules/rules_score:src/sphinx_wrapper.py",
    visibility = ["//visibility:public"],
    deps = [
        "@score_docs_as_code//src:plantuml_for_python",
        "@score_docs_as_code//src/extensions/score_sphinx_bundle",
        "@score_tooling//bazel/rules/rules_score:sphinx_module_ext",
    ],
)

sphinx_toolchain(
    name = "score_sphinx_toolchain",
    conf_template = "@score_tooling//bazel/rules/rules_score:templates/conf.template.py",
    sphinx = ":score_build",
)

toolchain(
    name = "score_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    toolchain = ":score_sphinx_toolchain",
    toolchain_type = "@score_tooling//bazel/rules/rules_score:toolchain_type",
    visibility = ["//visibility:public"],
)
