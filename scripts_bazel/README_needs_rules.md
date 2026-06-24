# Sphinx-needs processing rules (playground)

> **WIP / demonstration only.** This branch (`ankr_rules_score_playground`) is a
> proof of concept to explore how `rules_score` could post-process sphinx-needs
> data. It is **not** production ready and is shared for demonstration purposes.

## Why these changes

The documentation build already produces a `needs.json` file that contains every
sphinx-needs element (requirements, assumptions of use, ...). Downstream tooling
often needs only a *subset* of that data, or the data in a *different format*.

This change adds a small set of Bazel macros (in [docs.bzl](../docs.bzl)) plus
the backing Python tools (in this folder) to:

1. **Filter** a `needs.json` down to selected element types and/or components.
2. **Render** the selected elements as a human readable Markdown document.
3. **Convert** S-CORE requirement elements into [TRLC](https://github.com/bmw-software-engineering/trlc)
   data targeting the S-CORE requirements metamodel.

The goal is to show how requirements managed as sphinx-needs can be bridged to
other consumers (review docs, TRLC-based tooling) without manual copying.

## What was added

### Bazel macros (`docs.bzl`)

| Macro | Output | Purpose |
| --- | --- | --- |
| `filtered_needs_json` | `<name>.json` | Keep only needs matching the given `types` / `components`. |
| `component_requirements` | `<name>.json` | Convenience wrapper for `comp_req` elements. |
| `feature_requirements` | `<name>.json` | Convenience wrapper for `feat_req` elements. |
| `assumptions_of_use` | `<name>.json` | Convenience wrapper for `aou_req` elements. |
| `sphinx_needs_to_md` | `<name>.md` | Render needs as a Markdown document. |
| `sphinx_needs_to_trlc` | `<name>.trlc` | Convert S-CORE requirements to TRLC. |

### Python tools (`scripts_bazel/`)

- [filter_needs_json.py](filter_needs_json.py) — extract a subset of needs.
- [sphinx_needs_to_md.py](sphinx_needs_to_md.py) — render needs as Markdown.
- [sphinx_needs_to_trlc.py](sphinx_needs_to_trlc.py) — convert needs to TRLC.

The matching `py_binary` targets are declared in [BUILD](BUILD).

## How to use

In a `BUILD` file that already has a `needs_json` target, load the macros and
chain them:

```starlark
load("@docs-as-code//:docs.bzl", "feature_requirements", "sphinx_needs_to_md", "sphinx_needs_to_trlc")

# 1. Filter: keep only the feature requirements of one feature.
feature_requirements(
    name = "my_feature_reqs",
    src = "//:needs_json",
    feature = "my_feature",
)

# 2. Render the filtered set as Markdown.
sphinx_needs_to_md(
    name = "my_feature_reqs_md",
    src = ":my_feature_reqs",
    title = "My feature requirements",
)

# 3. Convert the filtered set to TRLC.
sphinx_needs_to_trlc(
    name = "my_feature_reqs_trlc",
    src = ":my_feature_reqs",
    package = "MyFeature",
)
```

Build any of the targets to produce the corresponding output file:

```bash
bazel build //path/to:my_feature_reqs_md
bazel build //path/to:my_feature_reqs_trlc
```

You can also call `filtered_needs_json` directly for full control over the
`types`, `components`, and `component_attr` filters.
