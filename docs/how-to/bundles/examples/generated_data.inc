# BEGIN docs-bundle-howto: generated-data
genrule(
    name = "generated_page",
    srcs = [],
    outs = ["generated/index.rst"],
    cmd = """echo 'Generated Data Page
===================' > $@""",
)

# Pure-data bundle: the genrule output lives in ``bazel-out/``, not the tree.
docs_bundle(
    name = "data_bundle",
    data = [":generated_page"],
    entry_doc = "index",
    visibility = ["//visibility:public"],
)

docs(
    source_dir = "docs",
    bundles = [{
        "bundle": ":data_bundle",
        "mount_at": "data_test",
        "attach_to": "index",
    }],
)
# END docs-bundle-howto: generated-data
