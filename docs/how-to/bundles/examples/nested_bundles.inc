# BEGIN docs-bundle-howto: parent-composition
docs_bundle(
    name = "parent",
    source_dir = "parent",
    bundles = [{
        "bundle": ":child",
        "mount_at": "child",
    }],
    data = [":generated_doc_output"],
    visibility = ["//visibility:public"],
)
# END docs-bundle-howto: parent-composition
