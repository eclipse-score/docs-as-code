# BEGIN docs-bundle-howto: external-bundle
docs(
    source_dir = "host_docs",
    test_sources = ["src/tests/docs_bzl/scenarios/external_bundle"],
    bundles = [{
        "bundle": "@score_process_description//:docs_bundle",
        "mount_at": "process",
    }],
)
# END docs-bundle-howto: external-bundle
