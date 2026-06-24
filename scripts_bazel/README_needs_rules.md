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
4. **Validate** a reviewable *requirement checklist* against the build output it
   was reviewed against, by pinning a SHA256 hash in a `req_chklst` sphinx-needs
   element and failing the build when the output drifts.

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
| `feature_architecture` | `<name>.json` | Convenience wrapper for `feat_arc_sta` / `feat_arc_dyn` elements. |
| `component_architecture` | `<name>.json` | Convenience wrapper for `comp_arc_sta` / `comp_arc_dyn` elements. |
| `sphinx_needs_to_md` | `<name>.md` | Render needs as a Markdown document. |
| `sphinx_needs_to_trlc` | `<name>.trlc` | Convert S-CORE requirements to TRLC. |
| `requirements_checklist` | `<name>.sha256` | Validate a `req_chklst` need against its target output via SHA256. |
| `architecture_checklist` | `<name>.sha256` | Validate an `arch_chklst` need against its target output via SHA256. |

### Python tools (`scripts_bazel/`)

- [filter_needs_json.py](filter_needs_json.py) — extract a subset of needs.
- [sphinx_needs_to_md.py](sphinx_needs_to_md.py) — render needs as Markdown.
- [sphinx_needs_to_trlc.py](sphinx_needs_to_trlc.py) — convert needs to TRLC.
- [validate_checklist.py](validate_checklist.py) — validate a checklist hash.

The matching `py_binary` targets are declared in [BUILD](BUILD).

### Metamodel

A new `req_chklst` need type is added in
[metamodel.yaml](../src/extensions/score_metamodel/metamodel.yaml). It carries a
mandatory `sha256` attribute, an optional `targets` attribute (the Bazel labels
it validates), and an optional `checklist` link to the rendered checklist
document.

The analogous `arch_chklst` need type (validated by `architecture_checklist`)
is defined in the same file and works the same way for feature/component
architecture outputs.

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

## Incremental builds and caching

Because every step is a separate Bazel target, Bazel only re-runs the work that
is actually affected by a change. Edit any `.rst` file and the documentation
build (the `needs_json` target) is re-executed, because its inputs changed.

However, the filtering, rendering, conversion and checklist targets sit
*downstream* of `needs_json` and Bazel compares their inputs before re-running
them. If your edit does not touch a given subset — for example you change an
unrelated feature and the `component_requirements` output for a component stays
byte-for-byte identical — then that `component_requirements` target produces the
same output as before, and **every target that depends on it
(`sphinx_needs_to_md`, `sphinx_needs_to_trlc`, `requirements_checklist`, ...) is
not re-executed**. Bazel serves their previous results from cache instead.

In practice this means:

- Changing an `.rst` file only re-runs the doc build plus the filtered targets
  whose content actually changed.
- A `requirements_checklist` (or `architecture_checklist`) only re-validates —
  and can only fail — when the requirements/architecture it pins really change.
  Unrelated edits elsewhere in the documentation leave it untouched.

## Requirement checklists

A *requirement checklist* couples a human review (a checklist `.rst` document)
with the exact build output that was reviewed. The state of that output is
pinned via a SHA256 hash stored on a `req_chklst` sphinx-needs element. When the
output later changes, the checklist is considered stale and the build fails
until the checklist is re-reviewed and the hash updated.

### 1. Declare the checklist need

Add a `req_chklst` element (e.g. next to the checklist `.rst`). It references the
checklist document, the validated Bazel target(s), and the expected hash:

```rst
.. req_chklst:: Bitmanipulation Component Requirements Checklist
   :id: req_chklst__bitmanipulation__comp_req
   :status: valid
   :checklist: doc__bitmanipulation_req_inspection
   :targets: //:bitmanipulation_comp_reqs
   :sha256: 0000000000000000000000000000000000000000000000000000000000000000
```

### 2. Declare the validation target

```starlark
load("@docs-as-code//:docs.bzl", "component_requirements", "requirements_checklist")

component_requirements(
    name = "bitmanipulation_comp_reqs",
    component = "bitmanipulation",
)

requirements_checklist(
    name = "bitmanipulation_req_checklist",
    checklist_id = "req_chklst__bitmanipulation__comp_req",
    deps = [":bitmanipulation_comp_reqs"],
)
```

### 3. Validate

```bash
bazel build //:bitmanipulation_req_checklist
```

The build hashes the `deps` output and compares it to the `sha256` on the
checklist need. On the first run (placeholder hash) the build **fails** and
prints the actual hash — review the checklist, then paste that hash into the
`sha256` attribute. From then on the build passes until the validated
requirements change again, at which point it fails and asks for a re-review.

## Architecture checklists

An *architecture checklist* works exactly like a requirement checklist, but
pins the reviewed state of an *architecture* output (a feature or component
architecture) instead of requirements. The review (a checklist `.rst`
document) is coupled to the extracted architecture via a SHA256 hash stored on
an `arch_chklst` sphinx-needs element. When the architecture later changes, the
checklist is considered stale and the build fails until it is re-reviewed and
the hash updated.

### 1. Declare the checklist need

Add an `arch_chklst` element (e.g. next to the architecture `.rst`). It
references the checklist document, the validated Bazel target(s), and the
expected hash:

```rst
.. arch_chklst:: Baselibs Feature Architecture Checklist
   :id: arch_chklst__baselibs__feat_arc
   :status: valid
   :checklist: doc__baselibs_architecture
   :targets: //:baselibs_feature_arch
   :sha256: 0000000000000000000000000000000000000000000000000000000000000000
```

### 2. Declare the validation target

```starlark
load("@docs-as-code//:docs.bzl", "feature_architecture", "architecture_checklist")

feature_architecture(
    name = "baselibs_feature_arch",
    feature = "baselibs",
)

architecture_checklist(
    name = "baselibs_feat_arch_checklist",
    checklist_id = "arch_chklst__baselibs__feat_arc",
    deps = [":baselibs_feature_arch"],
)
```

Use `component_architecture` instead of `feature_architecture` to validate a
single component's architecture.

### 3. Validate

```bash
bazel build //:baselibs_feat_arch_checklist
```

The build hashes the `deps` output and compares it to the `sha256` on the
checklist need. On the first run (placeholder hash) the build **fails** and
prints the actual hash — review the checklist, then paste that hash into the
`sha256` attribute. From then on the build passes until the validated
architecture changes again, at which point it fails and asks for a re-review.

## Worked example: bitmanipulation (baselibs)

The [baselibs](https://github.com/eclipse-score/baselibs) repository wires both
checklist kinds for its `bitmanipulation` component. The flow below is a
complete, real example that you can copy.

### Requirements checklist

`BUILD`:

```starlark
component_requirements(
    name = "bitmanipulation_comp_reqs",
    component = "bitmanipulation",
)

requirements_checklist(
    name = "bitmanipulation_req_checklist",
    checklist_id = "req_chklst__bitmanipulation__comp_req",
    deps = [":bitmanipulation_comp_reqs"],
)
```

Checklist need (next to the requirements inspection `.rst`):

```rst
.. req_chklst:: Bitmanipulation Component Requirements Checklist
   :id: req_chklst__bitmanipulation__comp_req
   :status: valid
   :checklist: doc__bitmanipulation_req_inspection
   :targets: //:bitmanipulation_comp_reqs
   :sha256: <pinned after first build>
```

### Architecture checklist

`BUILD`:

```starlark
component_architecture(
    name = "bitmanipulation_comp_arch",
    component = "bitmanipulation",
)

architecture_checklist(
    name = "bitmanipulation_arch_checklist",
    checklist_id = "arch_chklst__bitmanipulation__comp_arc",
    deps = [":bitmanipulation_comp_arch"],
)
```

Checklist need (next to the architecture inspection `.rst`):

```rst
.. arch_chklst:: Bitmanipulation Component Architecture Checklist
   :id: arch_chklst__bitmanipulation__comp_arc
   :status: valid
   :checklist: doc__bitmanipulation_arc_inspection
   :targets: //:bitmanipulation_comp_arch
   :sha256: <pinned after first build>
```

### Gotcha: the component filter matches on `tags`

`component_requirements` / `component_architecture` keep only needs whose
`tags` contain the requested component name (see
[filtered_needs_json](filter_needs_json.py), `--component-attr tags`). In
baselibs that tag is *not* set on each element directly — it is injected for a
whole document via `needextend`, e.g. for the requirements:

```rst
.. needextend:: "__bitmanipulation__" in id
   :+tags: baselibs, bitmanipulation
```

The architecture view ids do **not** contain `__bitmanipulation__` (they read
`comp_arc_sta__baselibs__bit_manipulation`), so that `needextend` does not tag
them and `component_architecture(component = "bitmanipulation")` would extract
*zero* needs. Add a matching `needextend` in the architecture document so the
views get the component tag:

```rst
.. needextend:: docname is not None and "bitmanipulation" in docname and "architecture" in docname and type in ["comp_arc_sta", "comp_arc_dyn"]
   :+tags: baselibs, bitmanipulation
```

After that, `bazel build //:bitmanipulation_comp_arch` keeps the architecture
view(s) and the checklist validates as expected. If a `component_*` target
unexpectedly extracts `0 needs`, check the `tags` of the elements first.
