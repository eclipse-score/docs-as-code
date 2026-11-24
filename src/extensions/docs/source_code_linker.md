<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

(source-code-linker)=
# Score Source Code Linker

A Sphinx extension for enabling **source code and test traceability** for requirements.
This extension integrates with **Bazel** and **sphinx-needs** to automatically generate traceability links between implementation, tests, and documentation.

---

## Overview

The feature is split into **two layers**:

1. **Bazel pre-processing (before Sphinx runs)**
   Generates and aggregates JSON caches containing the raw `source_code_link` findings (and, if available, repository metadata like `repo_name/hash/url`).
   Note that "hash" might also be a "version" tag.

2. **Sphinx extension (during the Sphinx build)**
   Reads the aggregated JSON, validates and adapts it, and finally injects the links into Sphinx needs.

This separation makes combo builds faster and more deterministic, because the expensive repository scanning/parsing happens **outside** the Sphinx process.

---

## How It Works

### Bazel Pre-processing: Source Code Integration (CodeLinks)

The Bazel parts are responsible for producing the **intermediate caches** that the source_code_linker extension later will consumes.

(step-1-per-repository-cache-generation)=
#### Step 1: Per-bundle cache generation

Each `docs_bundle` scans the source files selected by its `code_targets`
attribute. A *per bundle JSON cache* is then generated and saved; Bazel
reuses it until its source inputs change.
This script `scripts_bazel/generate_sourcelinks_cli.py` finds all codelinks per file, and gathers them into
one JSON cache per bundle.
A bundle can contain source files of several repositories, so each needlink records the repository of its own file.

Example of requirement tags:

```python
# Choose one or the other, both mentioned here to avoid detection
# req-Id/req-traceability: <NEED_ID>
```

- Extracts for each match:
  - File path
  - Line number
  - Tag + full line
  - Associated need ID
  - Repository Metadata:
    - repo_name (the local Bazel module, or the dependency module from the file path)
    - hash (at this stage always blank)
    - url (at this stage always blank)

##### Example JSON cache (per bundle)

```{code-block} json
[
  {
    "file": "src/extensions/score_metamodel/metamodel.yaml",
    "line": 17,
    "tag": "#--req-Id:",
    "need": "tool_req__docs_dd_link_source_code_link",
    "full_line": "#--req-Id: tool_req__docs_dd_link_source_code_link",
    "repo_name": "score_docs_as_code",
    "hash": "",
    "url": ""
  }
]
```

> Note: `--` is shown in the examples to avoid accidental detection by the parser.

---

#### Step 2: Cache merge step (multi-repo aggregation)

In a second Bazel step `scripts_bazel/merge_sourcelinks.py`, **all per-bundle caches** are merged into a **single combined JSON**.

- Input: N JSON caches (one per bundle)
- Output: 1 merged JSON containing all found source_code_links, in the same format as the input

This step also fills in url & hash of each link from the entry of its repository, if there is a known_good_json provided (e.g. in a combo build)

(repo-metadata-rules)=
#### Repo metadata rules

Here are some basic rules regarding the repo information (`RepoInfo` in `src/helper_lib/repo_info.py`)

In a combo build, provide `known_good.json` to resolve external source URLs.
The lookup lives in one function, `resolve_repo`, used by both `merge_sourcelinks.py` and the XML parser.
`known_good.json` is read once per run.
Without a Git pin, external links keep their module name and leave the hash and URL empty.
The documentation shows the source location or test name as text when there is no Git URL.

**External repository**

- `repo_name`: repository name (parsed from filepath in step 1)
- `hash`: revision/commit hash (as provided by the known_good_json)
- `url`: repository remote URL (as provided by the known_good_json)

**Local repository**

- `repo_name`: the root Bazel module. Bazel supplies it to the source scanner,
  and the JUnit parser reads it from the mount manifest.
- `hash`: stays empty
- `url`: stays empty

For the root module, the link URL is built from the local git checkout (remote URL + `HEAD`).
Git is asked once per build, not once per link.

---

### Source Code Linker Extension

All steps run on the Sphinx `env-updated` event, in this order:

1. **Priority 505: testcases.** `xml_parser.py` parses the `test.xml` files (no Sphinx needed).
   `testcase_needs.py` adds a `testcase` need per testcase and writes the testlinks to
   `score_xml_parser_cache.json`.
2. **Priority 525: links.** `inject_links_into_needs` (`__init__.py`) reads the JSON produced by Bazel
   and the testlinks, groups them by need in memory, renders each link with its own repository
   and writes `source_code_link` / `testlink` into the needs.

#### Codelinks

Since these are all found in [Bazel step 1](#step-1-per-repository-cache-generation) this essentially does not run
anymore inside of the source_code_linker extension.

#### Testlinks

TestLink scans test result XMLs from Bazel (bazel-testlogs) or from the folder 'tests-report' and converts each test case with metadata into Sphinx external needs, allowing links from tests to requirements.
This depends on the `attribute_plugin` in our tooling repository, find it [here](https://github.com/eclipse-score/tooling/tree/main/python_basics/score_pytest)

:::attention
To render GitHub links for external tests in a combo build, supply
`known_good` to the `docs()` macro.
:::

#### Test Tagging Options

```python
# Import the decorator
from attribute_plugin import add_test_properties

# Add the decorator to your test
@add_test_properties(
    partially_verifies=["tool_req__docs_common_attr_title", "tool_req__docs_common_attr_description"],
    test_type="interface-test",
    derivation_technique="boundary-values"
)
def test_feature():
    """
    Mandatory docstring that contains a description of the test
    """
    ...

```

> Note: If you use the decorator, it will check that you have specified a docstring inside the function.

#### Data Flow

1. **XML Parsing** (`xml_parser.py`, no Sphinx needed)
   - Scans `bazel-testlogs/` or `tests-report` for `test.xml` files.
   - Parses test cases and extracts:
     - Name & Classname
     - File path
     - Line
     - Result (e.g. passed, failed, skipped)
     - Result text (if failed/skipped will check if message was attached to it)
     - Verifications (`PartiallyVerifies`, `FullyVerifies`)
     - Also parses metadata according to the [metadata rules](#repo-metadata-rules)

   - Cases without metadata are logged out as info (not errors).
   - Test cases with metadata are converted into:
     - `DataOfTestCase` (used for external needs)
     - `DataForTestLink` (used for linking tests to requirements)

> If there is a Classname then it gets combined with the function name for the displayed link as follows: `Classname__Functionname`

2. **Need Linking** (`testcase_needs.py` and `__init__.py`)
   - Generates external Sphinx needs from `DataOfTestCase`.
   - Creates `testlink` attributes on linked requirements.
   - Warns on missing need IDs.

#### Example JSON Cache (DataOfTestCase)

The DataOfTestCase depicts the information gathered about one testcase.

```json
[
  {
    "name": "test_cache_file_with_encoded_comments",
    "file": "src/extensions/score_source_code_linker/tests/test_codelink.py",
    "line": "340",
    "result": "passed",
    "TestType": "interface-test",
    "DerivationTechnique": "boundary-values",
    "result_text": "",
    "PartiallyVerifies": "tool_req__docs_common_attr_title, tool_req__docs_common_attr_description",
    "FullyVerifies": null,
    "repo_name": "score_docs_as_code",
    "hash": "",
    "url": ""
  }
]
```

---


### Combined Links

During the Sphinx build process, both CodeLink and TestLink data are combined and grouped by needs.
A need can have links from several repositories.

Grouping by need is `group_by_need` in `need_source_links.py`, called from `inject_links_into_needs`.

The grouping runs in memory on every build, from the sourcelinks JSON and `score_xml_parser_cache.json`.
With Sphinx debug verbosity (`-vv`), `score_scl_grouped_cache.json` is also written to `_build` for debugging;
the build never reads it back.

### Combined JSON Example

```
[
  {
    "need": "tool_req__docs_common_attr_title",
    "links": {
      "CodeLinks": [
        {
          "file": "src/extensions/score_metamodel/metamodel.yaml",
          "line": 33,
          "tag": "#--req-Id:",# added `--` to avoid detection
          "need": "tool_req__docs_common_attr_title",
          "full_line": "#--req-Id: tool_req__docs_common_attr_title", # added `--` to avoid detection
          "repo_name": "score_docs_as_code",
          "hash": "",
          "url": "",

        }
      ],
      "TestLinks": [
        {
          "name": "test_cache_file_with_encoded_comments",
          "file": "src/extensions/score_source_code_linker/tests/test_codelink.py",
          "line": 340,
          "need": "tool_req__docs_common_attr_title",
          "verify_type": "partially",
          "result": "passed",
          "result_text": "",
          "repo_name": "score_docs_as_code",
          "hash": "",
          "url": "",
        }
      ]
    }
  }
]
```

:::hint
If the repo is the local one, the hash and url come from the local git checkout (see [repo metadata rules](#repo-metadata-rules)).
All link URLs are decided in one function, `get_github_link` in `src/helper_lib/repo_info.py`.
:::

---

## Result: Traceability Links in Needs

During the Sphinx build process, the extension applies the computed links to needs:

- Each need’s `source_code_link` and `testlink` attribute contains the links from all repositories that refer to it.
- If a referenced need ID does not exist, a build warning will be raised.

---

## Known Limitations

### General

- For GitHub links to dependencies in a combo build, pass `known_good = "//:known_good.json"` to `docs()`.
  The file supplies the repository URL and revision for each dependency.
- inefficiencies in creating the links
- Not compatible with **Esbonio**
- Live preview: Bazel regenerates the sourcelinks JSON when the preview starts, but unchanged pages can still show old links if Sphinx reuses its previous build.
  Clean `_build` and restart the preview to refresh all pages and test results.

### Codelinks

- GitHub links may 404 if the commit isn’t pushed
- Tags must match exactly (e.g. #<!-- comment prevents parsing this occurance --> req-Id)
- `source_code_link` isn’t visible until the full Sphinx build is completed

### TestLink

- GitHub links may 404 if the commit isn’t pushed
- XML structure must be followed exactly (e.g. `properties & attributes`)
- Relies on test to be executed first

---

## High-level Data Flow Summary

1. **Bazel Script #1**: scan + parse → write **per-bundle cache** (each link names its repository)
2. **Bazel Script #2**: merge caches + fill url & hash per link → write **single merged JSON**
3. **Sphinx Extension**: parse test XMLs → add testcase needs → read merged JSON + testlinks → group by need in memory → inject source_code_link and testlink into needs

---

## Clearing Cache Manually

To clear the build cache, run:

```bash
rm -rf _build/
```

## Internal  Overview

The bazel part:

```text
scripts_bazel/
├── BUILD   # Declare libraries and filegroups needed for bazel
├── generate_sourcelinks_cli.py # Bazel step 1 => Parses sourcefiles for tags
├── source_code_link_parser.py # Source-file parser used by the generator
├── merge_sourcelinks.py
└── tests
│   └── ...
```

The Sphinx extension

```text
score_source_code_linker/
├── __init__.py                   # Main Sphinx extension; combines CodeLinks + TestLinks
├── need_source_links.py         # Data model for combined links
├── testlink.py                  # DataForTestLink definition & logic
├── xml_parser.py                # Parses XML files into test case data (no Sphinx)
├── testcase_needs.py            # Turns parsed test cases into testcase needs
├── testcase_annotations.py      # Adds result annotations to GitHub testcase links
├── tests/                       # Testsuite, containing unit & integration tests
│   └── ...
```

Shared parts in `src/helper_lib/` (also used by the Bazel scripts):

```text
helper_lib/
├── needlinks.py                 # CodeLink (NeedLink) dataclass & JSON encoder/decoder
├── repo_info.py                 # RepoInfo, known_good lookup (resolve_repo), GitHub link URLs (get_github_link)
```

---

## Examples

To see working examples for CodeLinks & TestLinks, take a look at the Docs-As-Code documentation.

[Example CodeLink](https://eclipse-score.github.io/docs-as-code/main/internals/requirements/requirements.html#tool_req__docs_common_attr_id_scheme)
[Example CodeLink](https://eclipse-score.github.io/docs-as-code/main/internals/requirements/requirements.html#tool_req__docs_common_attr_status)

[Example TestLink](https://eclipse-score.github.io/docs-as-code/main/internals/requirements/requirements.html#tool_req__docs_dd_link_source_code_link)
