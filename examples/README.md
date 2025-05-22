## Examples

These examples show how to use the 'docs' macro in order to build without outgoing links, establish links to a latest (main branch) or a (module) release.


| Folder | Description |
|-----------|-------------|
| `simple` | Build documentation without links to another sphinx documentations | 
| `linking-latest` | Build documentation with links to another documentation via URL |
| `linking-release` | Build documentation with links to another documentation via MODULE import |

---
In order to enable linking against an imported Modules needs make sure you have imported it into the MODULE.bazel via 
`bazel_dep(...)`. 

Then have a look how the BUILD file is setup, and mimic it with the changes needed for your specific case. 
Underneath are some explanations regarding the different key-value pairs and their function.

Here is a more general overview

```python
load("@score_docs_as_code//docs.bzl", "docs")

docs(
    conf_dir = "<your sphinc conf dir>",
    source_dir = "<your sphinx source dir>",
    docs_targets = [
        {
            "suffix": "<target suffix>",  # 'release' for example
            "target": ["<needs.json target of the module you want to link to>"], # '@score_platform//docs:docs_needs
            "external_needs_info": [
                {
                    "base_url": "<URL to the documentation>",
                    "json_path/url": "<place where the needs.json is located>", # local_path OR a URL
                    "version": "<version of the needs.json you want to use", # 0.1
                    #  This is an UPPERCASE PREFIX that gets put before all external needs from the needs.json above.
                    #  This comes from sphinx-needs internally see here: https://github.com/useblocks/sphinx-needs/blob/master/sphinx_needs/external_needs.py#L119
                    "id_prefix": "<prefix for external needs>", 
                },
            ],
        },
    ],
    source_files_to_scan_for_needs_links = [
        # Note: you can add file groups, globs, or entire targets here.
        "<your targets that the source code linker should scan>"
    ],
)
```

`docs_targets` is a list of dictionaries, it accepts the following key-value pairs.

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `suffix` | suffix that gets appended to target definitions. E.g. `release` | yes | '' |
| `target` | Target to be build/executed beforehand in order to build 'needs.json'. E.g. `@score_platform//docs:docs_needs` | No | [] |
| `external_needs_info` | List of dictionaries that contains all available builds | yes | - |
| `base_url` | URL of the documentation that external needs of the following json should point to | Yes | - |
| `json_path\json_url` | A local relative path or URL that points to the needs.json file | yes | '' |
| `id_prefix` | prefix that all exeternal ID's from this needs.json will get. Will be in UPPERCASE | No | '' |

The `external_needs_info` is based on external needs, which can be explored more in detail [here](https://sphinx-needs.readthedocs.io/en/latest/configuration.html#needs-external-needs)

--- 

The targets available in the examples are 
```python
bazel build //examples/linking-release:docs_release
bazel run //examples/linking-release:incremental_release
bazel run //examples/linking-release:livew_preview_release
```
