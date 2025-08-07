#load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

#
py_library(
    name = "testrstwriter",
    srcs = ["test_xml_parser/testrstwriter.py"],
    imports = ["."],
    visibility = [
        "//visibility:public",
    ],
)
#
# py_binary(
#     name = "docs_with_testing_info",
#     srcs = [
#         "__init__.py",
#         "test_xml_parser/__init__.py",
#         "test_xml_parser/docs_with_testing_info.py",
#         "test_xml_parser/testrstwriter.py",
#     ],
#     imports = ["."],
#     main = "test_xml_parser/docs_with_testing_info.py",
#     visibility = [
#         "//visibility:public",
#     ],
#     deps = [
#         requirement("junitparser"),
#         ":testrstwriter",
#         requirement("sphinx"),
#     ],
# )
#
# exports_files(
#     ["test_xml_parser/docs_with_testing_info.py"],
#     visibility = ["//visibility:public"],
# )
