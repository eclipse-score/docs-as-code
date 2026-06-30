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
4. **Validate** a reviewable *requirement / architecture checklist* against the
   build output it was reviewed against, by pinning a SHA256 hash on a
   `mod_insp` inspection record and failing the build when the output drifts.

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
| `requirements_checklist` | `<name>.sha256` | Validate a `mod_insp` record against its requirements target output via SHA256. |
| `architecture_checklist` | `<name>.sha256` | Validate a `mod_insp` record against its architecture target output via SHA256. |
| `dfa_checklist` | `<name>.sha256` | Validate a `mod_insp` DFA record against its DFA target output via SHA256. |
| `fmea_checklist` | `<name>.sha256` | Validate a `mod_insp` FMEA record against its FMEA target output via SHA256. |
| `verification_report` | `<name>.sha256` | Validate a `mod_ver_report` record against its target output via SHA256. |
| `score_component` | aggregate (`filegroup`) | Bundle a component's requirement + architecture checklists. |
| `score_module` | aggregate (`filegroup`) | Bundle a feature's checklists (incl. DFA/FMEA), docs and all of its components. |

### Python tools (`scripts_bazel/`)

- [filter_needs_json.py](filter_needs_json.py) — extract a subset of needs.
- [sphinx_needs_to_md.py](sphinx_needs_to_md.py) — render needs as Markdown.
- [sphinx_needs_to_trlc.py](sphinx_needs_to_trlc.py) — convert needs to TRLC.
- [validate_checklist.py](validate_checklist.py) — validate a checklist hash.

The matching `py_binary` targets are declared in [BUILD](BUILD).

### Metamodel

The `mod_insp` inspection record need type in
[metamodel.yaml](../src/extensions/score_metamodel/metamodel.yaml) carries an
optional `sha256` attribute (the reviewed build output hash), a mandatory
`checklist` link to the rendered checklist document, and an `inspects` link to
the inspected artifacts. The same need type is validated by both
`requirements_checklist` and `architecture_checklist`.

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
`types` and `names` filters.

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
- A `requirements_checklist` (or `architecture_checklist`) re-validates whenever
  the full `needs.json` changes, but it only **fails** when the elements it pins
  — the roots in `deps` *or any of their transitive dependencies* (see
  [Transitive dependencies](#transitive-dependencies)) — really change. Edits to
  unrelated, unreachable elements leave its hash untouched.

## Checklists

A *checklist* couples a human review (a checklist `.rst` document) with the exact
build output that was reviewed. The state of that output is pinned via a SHA256
hash stored on a sphinx-needs element. When the output later changes, the
checklist is considered stale and the build fails until it is re-reviewed and the
hash updated.

There are two checklist kinds. They behave identically and differ only in the
macro that validates them; both pin the reviewed state on a `mod_insp`
inspection record:

| Kind | Need type | Validating macro | Pins the reviewed state of … |
| --- | --- | --- | --- |
| Requirements | `mod_insp` | `requirements_checklist` | extracted requirements (`component_requirements` / `feature_requirements`) and, by default, their transitive dependencies |
| Architecture | `mod_insp` | `architecture_checklist` | extracted architecture (`component_architecture` / `feature_architecture`) and, by default, their transitive dependencies |
| DFA | `mod_insp` | `dfa_checklist` | the architecture/requirements the DFA covers (passed in `deps`) and, by default, their transitive dependencies |
| FMEA | `mod_insp` | `fmea_checklist` | the architecture/requirements the FMEA covers (passed in `deps`) and, by default, their transitive dependencies |
| Verification report | `mod_ver_report` | `verification_report` | the verified elements passed in `deps` and, by default, their transitive dependencies |

The flow below is a complete, real example from the
[baselibs](https://github.com/eclipse-score/baselibs) repository, which wires
both kinds for its `bitmanipulation` component. You can copy it directly.

### 1. Declare the inspection record need

Add the `mod_insp` inspection record next to the inspection `.rst`. It links the
inspected artifacts (`inspects`), the filled checklist document (`checklist`)
and stores the expected hash. On the first build leave the `sha256` as the
placeholder (all zeros) and pin the real value afterwards.

Requirements (`mod_insp`):

```rst
.. mod_insp:: Bitmanipulation Component Requirements Inspection Record
   :id: mod_insp__bitmanipulation__comp_req
   :status: valid
   :safety: ASIL_B
   :security: YES
   :inspection_type: requirements
   :inspection_state: approved
   :checklist_template: gd_chklst__req_inspection
   :reviewers: mihajlo-k
   :belongs_to: mod__baselibs
   :inspects: comp_req__bitmanipulation__bit_operations
   :checklist: doc__bitmanipulation_req_inspection
   :sha256: 0000000000000000000000000000000000000000000000000000000000000000
```

Architecture (`mod_insp`):

```rst
.. mod_insp:: Bitmanipulation Component Architecture Inspection Record
   :id: mod_insp__bitmanipulation__comp_arc
   :status: valid
   :safety: ASIL_B
   :security: YES
   :inspection_type: architecture
   :inspection_state: approved
   :checklist_template: gd_chklst__arch_inspection_checklist
   :reviewers: aschemmel-tech
   :belongs_to: mod__baselibs
   :inspects: comp_arc_sta__bitmanipulation__component_view
   :checklist: doc__bitmanipulation_arc_inspection
   :sha256: 0000000000000000000000000000000000000000000000000000000000000000
```

### 2. Declare the validation target

Extract the reviewed output (`component_*` wrapper) and validate it against the
checklist need.

Requirements `BUILD`:

```starlark
load("@docs-as-code//:docs.bzl", "component_requirements", "requirements_checklist")

component_requirements(
    name = "bitmanipulation_comp_reqs",
    component = "bitmanipulation",
)

requirements_checklist(
    name = "bitmanipulation_req_checklist",
    mod_insp_id = "mod_insp__bitmanipulation__comp_req",
    deps = [":bitmanipulation_comp_reqs"],
    # Resolve upstream stakeholder requirements so changes to them are detected.
    extra_needs = ["@score_platform//:needs_json"],
)
```

Architecture `BUILD`:

```starlark
load("@docs-as-code//:docs.bzl", "component_architecture", "architecture_checklist")

component_architecture(
    name = "bitmanipulation_comp_arch",
    component = "bitmanipulation",
)

architecture_checklist(
    name = "bitmanipulation_arch_checklist",
    mod_insp_id = "mod_insp__bitmanipulation__comp_arc",
    deps = [":bitmanipulation_comp_arch"],
    # Resolve upstream (feature/stakeholder) requirements so changes are detected.
    extra_needs = ["@score_platform//:needs_json"],
)
```

Use the `feature_requirements` / `feature_architecture` wrappers instead of the
`component_*` ones to validate a whole feature rather than a single component.

The `extra_needs` argument is explained in
[Resolving external needs (`extra_needs`)](#resolving-external-needs-extra_needs)
below; drop it if all transitively linked elements live in the same repository.

### 3. Validate

```bash
bazel build //:bitmanipulation_req_checklist
bazel build //:bitmanipulation_arch_checklist
```

The build hashes the `deps` output and compares it to the `sha256` on the
checklist need. On the first run (placeholder hash) the build **fails** and
prints the actual hash — review the checklist, then paste that hash into the
`sha256` attribute. From then on the build passes until the validated
requirements/architecture change again, at which point it fails and asks for a
re-review.

### Transitive dependencies

By default neither `requirements_checklist` nor `architecture_checklist` hash
only the elements in `deps`; they also follow the elements' sphinx-needs links
recursively and include every reachable element in the hash. The followed link
fields are configurable via the `link_fields` argument:

| Macro | Default `link_fields` |
| --- | --- |
| `requirements_checklist` | `derived_from`, `satisfies`, `covers` |
| `architecture_checklist` | `fulfils`, `includes`, `uses`, `provides`, `derived_from`, `satisfies`, `covers` |
| `dfa_checklist` | `mitigates`, `violates`, `fulfils`, `includes`, `uses`, `provides`, `derived_from`, `satisfies`, `covers` |
| `fmea_checklist` | `mitigates`, `violates`, `fulfils`, `includes`, `uses`, `provides`, `derived_from`, `satisfies`, `covers` |
| `verification_report` | `mitigates`, `violates`, `fulfils`, `includes`, `uses`, `provides`, `derived_from`, `satisfies`, `covers` |

The mechanism is generic and works for any element type and any link fields:

- **Feature requirements** → linked **stakeholder requirements** (via
  `derived_from`/`satisfies`) are part of the hash.
- **Component requirements** → linked **feature requirements** (and their
  stakeholder requirements in turn) are part of the hash. Just point `deps` at a
  `component_requirements` target; the defaults already cover the
  `comp_req → feat_req → stkh_req` chain.
- **Architecture elements** → the requirements they `fulfils` (and those
  requirements' parents) plus structurally linked architecture elements
  (`includes`/`uses`/`provides`) are part of the hash.

This means a checklist also goes out of date when an **upstream** dependency
changes — e.g. when a stakeholder requirement that a feature requirement is
`derived_from` is edited. The roots (the elements in `deps`) define the entry
points; the validator walks the link graph in the full `needs.json` (`src`) and
hashes the canonical serialization of the whole closure (roots + all
transitively linked elements). Link targets carrying a version constraint
(`stkh_req__foo[version==1]`) are matched against the plain need id.

```starlark
# Component requirements: transitively pins feature + stakeholder requirements.
requirements_checklist(
    name = "bitmanipulation_req_checklist",
    mod_insp_id = "mod_insp__bitmanipulation__comp_req",
    deps = [":bitmanipulation_comp_reqs"],
    # default: link_fields = ["derived_from", "satisfies", "covers"]
)

# Architecture: transitively pins fulfilled requirements (and their parents).
architecture_checklist(
    name = "bitmanipulation_arch_checklist",
    mod_insp_id = "mod_insp__bitmanipulation__comp_arc",
    deps = [":bitmanipulation_comp_arch"],
)
```

Pass `link_fields = []` to restore the old behaviour of hashing only the
elements in `deps`. The full need dict of every element in the closure is
hashed, so any change to a linked element — its content, attributes *or* links
(including newly added/removed back-links) — triggers a re-review.

### Resolving external needs (`extra_needs`)

The transitive closure is walked through the link graph of the checklist's
`src` (`//:needs_json` by default). When a linked element lives in **another
repository** — e.g. a component requirement is `derived_from` a stakeholder
requirement that is imported from an upstream repo — that element's full content
is not contained in the local `needs.json`. The validator then hashes it as
`<MISSING>`, so **changes to such upstream elements go undetected** and the
checklist does not go stale even though one of its (transitive) parents changed.

Pass the upstream `needs_json` build outputs via `extra_needs` so the validator
can resolve the full content of those external needs and include them in the
hash. Typically these are the same upstream `needs_json` targets you already
pass as `data` to `docs(...)`:

```starlark
requirements_checklist(
    name = "bitmanipulation_req_checklist",
    mod_insp_id = "mod_insp__bitmanipulation__comp_req",
    deps = [":bitmanipulation_comp_reqs"],
    extra_needs = ["@score_platform//:needs_json"],
)

architecture_checklist(
    name = "bitmanipulation_arch_checklist",
    mod_insp_id = "mod_insp__bitmanipulation__comp_arc",
    deps = [":bitmanipulation_comp_arch"],
    extra_needs = ["@score_platform//:needs_json"],
)
```

`extra_needs` is available on both `requirements_checklist` and
`architecture_checklist` (and on `dfa_checklist`, `fmea_checklist` and
`verification_report`) and only fills in needs that are *missing* locally: the
main `src` keeps precedence for local content, and the extracted root elements
in `deps` keep precedence over both. You only need it when the closure reaches
elements that are not defined in the checklist's own repository — if everything
is local, leave it at its default (`[]`).

## Safety analysis checklists (DFA / FMEA)

`dfa_checklist` (Dependent Failure Analysis) and `fmea_checklist` (Failure Modes
and Effects Analysis) work exactly like `requirements_checklist` /
`architecture_checklist`: each pins the reviewed state of its safety-analysis
elements on the `sha256` attribute of a `mod_insp` inspection record and fails
the build when a validated element — or any of its transitive dependencies —
changes after the last review.

They differ only in their default `link_fields`: in addition to the architecture
and requirement links, they also follow the safety links `mitigates` and
`violates`, so an analysis goes stale when the architecture/requirements it
mitigates or the failure modes it describes change. Wire them against the
feature's architecture and requirements outputs:

```starlark
load("@docs-as-code//:docs.bzl", "feature_architecture", "feature_requirements", "dfa_checklist", "fmea_checklist")

feature_architecture(
    name = "baselibs_feature_arch",
    src = "@score_platform//:needs_json",
    feature = "baselibs",
)

feature_requirements(
    name = "baselibs_feature_reqs",
    src = "@score_platform//:needs_json",
    feature = "baselibs",
)

dfa_checklist(
    name = "baselibs_dfa_checklist",
    mod_insp_id = "mod_insp__baselibs__feat_dfa",
    deps = [":baselibs_feature_arch", ":baselibs_feature_reqs"],
    extra_needs = ["@score_platform//:needs_json"],
)

fmea_checklist(
    name = "baselibs_fmea_checklist",
    mod_insp_id = "mod_insp__baselibs__feat_fmea",
    deps = [":baselibs_feature_arch", ":baselibs_feature_reqs"],
    extra_needs = ["@score_platform//:needs_json"],
)
```

The `mod_insp` record is declared exactly like the requirements/architecture
ones (see [Declare the inspection record need](#1-declare-the-inspection-record-need)),
using `:inspection_type: dfa` / `fmea` and the matching
`:checklist_template:` / `:inspects:` links. Validate and pin the hash the same
way (build the target, paste the printed hash into `:sha256:`).

## Verification report (`verification_report`)

`verification_report` behaves identically to the safety-analysis checklists but
validates a `mod_ver_report` record instead of a `mod_insp` one (pass its id via
`mod_ver_report_id`). Use it to pin the reviewed state of the elements a module
verification report covers:

```starlark
load("@docs-as-code//:docs.bzl", "verification_report")

verification_report(
    name = "baselibs_verification_report",
    mod_ver_report_id = "mod_vrep__baselibs__module",
    deps = [],
    extra_needs = ["@score_platform//:needs_json"],
)
```

## Module and component aggregates (`score_module` / `score_component`)

`score_component` and `score_module` are convenience aggregates that bundle the
individual checklist targets so a single `bazel build` covers a whole component
or feature. Because building the aggregate builds every referenced checklist,
the build fails when **any** of them drifts from its reviewed inspection record.

- `score_component` bundles a component's requirement and architecture
  checklists (`req_chklst`, `arch_chklst`) plus optional `dfa` / `fmea`
  targets.
- `score_module` bundles a feature's requirement and architecture checklists,
  its `docs`, optional `dfa` / `fmea` / `verif_report` targets, and every
  `score_component` listed in `components`. Building the module therefore builds
  every component too.

```starlark
load("@docs-as-code//:docs.bzl", "score_component", "score_module")

score_component(
    name = "bitmanipulation",
    req_chklst = [":bitmanipulation_req_checklist"],
    arch_chklst = [":bitmanipulation_arch_checklist"],
    dfa = ":bitmanipulation_dfa_checklist",
    fmea = ":bitmanipulation_fmea_checklist",
    visibility = ["//visibility:private"],
)

score_module(
    name = "baselibs",
    docs = ":docs",
    req_chklst = [":baselibs_req_checklist"],
    arch_chklst = [":baselibs_arch_checklist"],
    components = [":bitmanipulation"],
    dfa = ":baselibs_dfa_checklist",
    fmea = ":baselibs_fmea_checklist",
    # verif_report = ":baselibs_verification_report",
    visibility = ["//visibility:public"],
)
```

```bash
# Build the whole module (feature checklists + docs + DFA/FMEA + all components).
bazel build //:baselibs
```

### Sub-target aliases (`<name>.<arg>`)

Both aggregates keep their underlying checklist targets private while still
exposing each part individually. For every argument that is actually provided,
a `<name>.<arg>` sub-target is generated with the aggregate's visibility:

| Aggregate | Sub-targets |
| --- | --- |
| `score_component` | `<name>.req_chklst`, `<name>.arch_chklst`, `<name>.dfa`, `<name>.fmea` |
| `score_module` | `<name>.docs`, `<name>.req_chklst`, `<name>.arch_chklst`, `<name>.components`, `<name>.dfa`, `<name>.fmea`, `<name>.verif_report` |

Single-label arguments (`docs`, `dfa`, `fmea`, `verif_report`) become an
`alias`; label-list arguments (`req_chklst`, `arch_chklst`, `components`) become
a `filegroup`. A sub-target only exists when its argument is part of the
aggregate, so referencing `<name>.fmea` on a module without an FMEA fails.

This lets you build a single part through the module without depending on the
private checklist target directly:

```bash
# Just the FMEA of the baselibs module.
bazel build //:baselibs.fmea

# Just the DFA, or just the docs.
bazel build //:baselibs.dfa
bazel build //:baselibs.docs

# Just the requirement checklists of a component.
bazel build //:bitmanipulation.req_chklst
```


### Gotcha: the feature/component filter matches on the need ID

`component_requirements` / `component_architecture` /
`feature_requirements` / `feature_architecture` keep only needs whose ID
encodes the requested feature/component name. Need IDs follow the
`<type>__<name>__<rest>` naming convention, so the second `__`-separated
segment is the feature/component name (see
[filtered_needs_json](filter_needs_json.py), `--name`). For example, the
following all belong to `bitmanipulation`:

```text
comp_req__bitmanipulation__shift
feat_arc_sta__bitmanipulation__static_view
```

The `comp_arc_sta` and `comp_arc_dyn` types are an exception: their IDs follow
`<type>__<feature name>__<component name>`, so the *third* segment holds the
component name used for matching. For example, the following belongs to the
`filesystem` component:

```text
comp_arc_sta__baselibs__filesystem
```

No tags or `needextend` injection are required — extraction is driven purely by
the ID. Just make sure each element's ID follows the convention with the
intended feature/component name as its name segment. If a `component_*` /
`feature_*` target unexpectedly extracts `0 needs`, check that the element IDs
use the expected name segment.
