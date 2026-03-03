# score_metamodel

Sphinx extension that enforces the S-CORE metamodel on sphinx-needs documents.

It reads `metamodel.yaml` (the single source of truth for all need types, fields,
links, and constraints) and validates every need in the documentation against
those rules.

## What it does

1. **Registers need types** with sphinx-needs (directives like `feat_req`, `comp`,
   `workflow`, etc.) including their fields, links, and extra options.
2. **Generates `schemas.json`** from the metamodel so that sphinx-needs 6 can
   validate needs at parse time (required fields, regex patterns, link
   constraints). Because ubCode (the VS Code extension for sphinx-needs)
   evaluates these schemas during editing, **metamodel violations are shown
   as diagnostics directly in the IDE** -- catching errors early with
   lightweight, fast rendering, without needing a full Sphinx build.
3. **Runs post-build checks** that go beyond what JSON Schema can express
   (graph traversals, prohibited words, ID format rules).

## Metamodel overview

`metamodel.yaml` defines:

| Section | Purpose |
|---|---|
| `needs_types` | All need types (e.g. `feat_req`, `comp`, `document`) with their mandatory/optional fields and links |
| `needs_types_base_options` | Global optional fields applied to every type (e.g. `source_code_link`, `testlink`) |
| `needs_extra_links` | Custom link types (e.g. `satisfies`, `implements`, `mitigated_by`) |
| `prohibited_words_checks` | Forbidden words in titles/descriptions (e.g. "shall", "must") |
| `graph_checks` | Cross-need constraints (e.g. safety level decomposition rules) |

Each need type can specify:

- **`mandatory_options`** -- fields that must be present, with a regex pattern
  the value must match (e.g. `status: ^(valid|invalid)$`).
- **`optional_options`** -- fields that, if present, must match a pattern.
- **`mandatory_links`** -- links that must have at least one target. The value
  is either a plain type name (`stkh_req`) or a regex (`^logic_arc_int__.+$`).
- **`optional_links`** -- links that are allowed but not required.

## Validation layers

### Schema validation (sphinx-needs >6)

`sn_schemas.py` translates the metamodel into a `schemas.json` file that
sphinx-needs evaluates at parse time. Each schema entry has:

- **`select`** -- matches needs by their `type` field.
- **`validate.local`** -- JSON Schema checking the need's own properties
  (required fields, regex patterns on option values, mandatory links with
  `minItems: 1`). Regex patterns on **link IDs** (e.g. checking that
  `includes` entries match `^logic_arc_int(_op)*__.+$`) are not yet
  validated here; the schema only enforces that at least one link exists.
  ID-pattern checking is still done by the Python `validate_links()` in
  `check_options.py`.
- **`validate.network`** -- validates that linked needs have the expected
  `type` (e.g. `satisfies` targets must be `stkh_req`). Uses the
  sphinx-needs `items.local` format so each linked need is checked
  individually. Only **mandatory** links are checked here; optional link
  type violations are left to the Python `validate_links()` check, which
  treats them as informational (`treat_as_info=True`) rather than errors.
  Fields that mix regex and plain targets (e.g.
  `complies: std_wp, ^std_req__aspice_40__iic.*$`) are also excluded
  because the `items` schema would incorrectly require all linked needs
  to match the plain type.

### Post-build S-Core metamodel checks

Checks in `checks/` run after the Sphinx build and cover rules that
JSON Schema cannot express:

| Check | File | What it validates |
|---|---|---|
| `check_options` | `check_options.py` | Mandatory/optional field presence and patterns (legacy, overlaps with schema validation) |
| `check_extra_options` | `check_options.py` | Warns about fields not defined in the metamodel |
| `check_id_format` | `attributes_format.py` | ID structure (`<type>__<abbrev>__<element>`, part count) |
| `check_for_prohibited_words` | `attributes_format.py` | Forbidden words in titles |
| `check_metamodel_graph` | `graph_checks.py` | Cross-need constraints (e.g. ASIL_B needs must link to non-QM requirements) |
| `check_id_contains_feature` | `id_contains_feature.py` | Need IDs must contain the feature abbreviation from the file path |
| `check_standards` | `standards.py` | Standard compliance link validation |

### Coverage comparison

Schema column: **yes** = implemented, **feasible** = could be added, **--** = not possible.

| Rule | Schema (`sn_schemas.py` + sphinx-needs) | S-Core metamodel (`checks/`) | Notes |
|---|:---:|:---:|---|
| ID required | yes | -- | `needs_id_required` (sphinx-needs built-in) |
| ID basic regex | yes | -- | `needs_id_regex` (sphinx-needs built-in) |
| Dead link detection | yes | -- | `allow_dead_links` (sphinx-needs built-in) |
| Mandatory field presence | yes | yes | Both enforce `required` |
| Mandatory field regex | yes | yes | Same pattern from metamodel |
| Optional field regex | yes | yes | Schema: only if field present |
| Mandatory link presence | yes | yes | Schema: `minItems: 1` in local |
| Mandatory link target type | yes | yes | Schema: `validate.network` |
| Mandatory link ID regex | feasible | yes | Can add `items.pattern` in local; TODO in code |
| Optional link target type | feasible | yes (info) | Split into separate schema with `severity: "info"` |
| Optional link ID regex | feasible | yes (info) | Same split-severity approach |
| Mixed regex+plain link type | -- | yes | `ValidateSchemaType` has no `anyOf`/`oneOf` |
| ID structure (parts count) | feasible | yes | Per-type pattern from `parts` field; cannot check file-path part |
| Prohibited words | feasible | yes | Negative lookahead regex on `title`; less precise than Python |
| Graph constraints | -- | yes | Cross-need traversals beyond JSON Schema |
| Undefined extra options | -- | yes | `unevaluatedProperties` would reject sphinx-needs internal fields |

#### Rule explanations

**ID required** --
Every need directive must have a manually set ID (e.g. `.. feat_req:: feat_req__my_feature__001`).
Enforced by sphinx-needs' `needs_id_required = True` in `__init__.py`.

**ID basic regex** --
The ID must match `^[A-Za-z0-9_-]{6,}` (at least 6 alphanumeric/underscore/hyphen characters).
Enforced by sphinx-needs' `needs_id_regex` in `__init__.py`. The build stops if a need
has an invalid ID.

**Dead link detection** --
A link like `satisfies: nonexistent_need_id` that points to a need that does not exist
triggers a sphinx-needs warning. Controlled per link type via `allow_dead_links` in
`needs_extra_links`.

**Mandatory field presence** --
A `feat_req` must have a `status` field. If it is missing, both the schema
(`"required": ["status"]`) and the Python check flag it.

**Mandatory field regex** --
The `status` field on `feat_req` must match `^(valid|invalid)$`. Both the schema
(`"pattern": "^(valid|invalid)$"`) and the Python check validate this. Writing
`status: approved` is rejected.

**Optional field regex** --
`document` has `optional_options: { author: ^.*$ }`. If `author` is present, it must
match the pattern. If absent, no error. The schema includes it in `properties` but
not in `required`.

**Mandatory link presence** --
`feat_req` has `mandatory_links: { satisfies: stkh_req }`. At least one target must
be provided. The schema enforces this with `"satisfies": {"type": "array", "minItems": 1}`
in `validate.local`.

**Mandatory link target type** --
`feat_req.satisfies` must point to a need of type `stkh_req`. The schema enforces
this with `validate.network`: each linked need is checked for
`{"type": {"const": "stkh_req"}}`. If a `feat_req` links to a `comp` via `satisfies`,
the schema rejects it.

**Mandatory link ID regex** (feasible) --
`feat` has `mandatory_links: { includes: ^logic_arc_int(_op)*__.+$ }`. The link
target IDs (strings like `logic_arc_int__something`) must match this regex.
Currently the schema only enforces that at least one link exists (`minItems: 1`),
not the ID pattern. *Feasible*: add `"items": {"pattern": "^logic_arc_int(_op)*__.+$"}`
to the local schema. There is a TODO in the code for this.

**Optional link target type** (feasible) --
`tool_req` has `optional_links: { satisfies: gd_req, stkh_req }`. If provided, targets
should be `gd_req` or `stkh_req`. The Python check validates this but treats violations
as informational (non-fatal). The schema currently skips this because all schema entries
use `severity: "violation"` and there is no way to set a different severity for one
rule within the same schema entry. *Feasible*: create a second schema entry for the
same need type with `severity: "info"` that only checks optional link targets.

**Optional link ID regex** (feasible) --
Same as above, but for regex-based link IDs on optional links (e.g.
`optional_links: { links: ^.*$ }` on `tsf`). Same severity-split approach would work.

**Mixed regex+plain link type** (not possible) --
`workproduct` has `optional_links: { complies: std_wp, ^std_req__aspice_40__iic.*$ }`.
A `complies` target is valid if it is either a need of type `std_wp` OR has an ID
matching the regex. The `validate.network` `items` schema applies to ALL linked needs
identically, so it cannot express "match type X *or* match regex Y".
sphinx-needs' `ValidateSchemaType` does not support `anyOf`/`oneOf`.
These mixed fields are validated only by the Python check.

**ID structure (parts count)** (feasible) --
`feat_req` has `parts: 3`, meaning its ID must have 3 segments separated by `__`
(e.g. `feat_req__my_feature__001`). The Python check (`check_id_format`) splits on
`__` and counts parts. *Feasible*: generate a per-type regex like
`^feat_req__[^_]+(__[^_]+){1}$` in the schema. However, the Python check also
validates that the ID contains the feature abbreviation from the file path
(`check_id_contains_feature`), which depends on runtime context and cannot be
expressed in a schema.

**Prohibited words** (feasible) --
The metamodel forbids words like "shall", "must", "will" in need titles (for
requirement types). The Python check splits the title into words and checks each one.
*Feasible*: add a negative lookahead regex on the `title` field, e.g.
`^(?!.*\b(shall|must|will)\b).*$`. This is less precise than the Python check
(which normalizes case, strips punctuation) but catches most violations.

**Graph constraints** (not possible) --
`graph_checks` in the metamodel define rules like "an ASIL_B need must link to at
least one non-QM requirement via `satisfies`". This requires traversing the need
graph across multiple levels, which is fundamentally beyond what JSON Schema can
express. Only the Python check (`check_metamodel_graph`) can do this.

**Undefined extra options** (not possible) --
The Python check (`check_extra_options`) warns when a need has fields not defined
in the metamodel (e.g. a typo like `saftey` instead of `safety`). In theory,
`unevaluatedProperties: false` could reject unknown fields. In practice, sphinx-needs
adds many internal fields to needs (e.g. `docname`, `lineno`, `is_external`, computed
fields from dynamic functions) that are not in the metamodel. Enabling this would
cause false positives on every need.

## File layout

```
score_metamodel/
  __init__.py          # Sphinx extension entry point (setup, check orchestration)
  metamodel.yaml       # The S-CORE metamodel definition
  metamodel_types.py   # Type definitions (ScoreNeedType, etc.)
  yaml_parser.py       # Parses metamodel.yaml into MetaModelData
  sn_schemas.py        # Generates schemas.json for sphinx-needs 6
  log.py               # CheckLogger for structured warning output
  external_needs.py    # External needs integration
  checks/              # Post-build validation checks
  tests/               # Unit and integration tests
```
