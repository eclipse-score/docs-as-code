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
   constraints).
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

### Post-build Python checks

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
