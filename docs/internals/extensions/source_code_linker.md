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
   Reads the aggregated JSON, validates and adapts it, and finally injects the links into Sphinx needs in the final layout (**RepoSourceLink**).

This separation makes combo builds faster and more deterministic, because the expensive repository scanning/parsing happens **outside** the Sphinx process.

---

## How It Works

### Bazel Pre-processing: Source Code Integration (CodeLinks)

The Bazel parts are responsible for producing the **intermediate caches** that the source_code_linker extension later will consumes.

(step-1-per-repository-cache-generation)=
#### Step 1: Per-repository cache generation

All files provided via the `scan_code` attribute to the docs macro will be scanned for the requirement tags.
A *per repository JSON cache* will be generated and saved.
This script `scripts_bazel/generate_sourcelinks_cli.py` finds all codelinks per file, and gathers them into
one JSON cache per repository.
It also adds metadata to each needlink that is needed in further steps.

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
    - repo_name (parsed from filepath) (local_repo if non combo build)
    - hash (at this stage always blank)
    - url (at this stage always blank)

##### Example JSON cache (per repository)

```{code-block} json
[
  {
    "file": "src/extensions/score_metamodel/metamodel.yaml",
    "line": 17,
    "tag": "#--req-Id:",
    "need": "tool_req__docs_dd_link_source_code_link",
    "full_line": "#--req-Id: tool_req__docs_dd_link_source_code_link",
    "repo_name": "local_repo",
    "hash": "",
    "url": ""
  }
]
```

> Note: `--` is shown in the examples to avoid accidental detection by the parser.

---

#### Step 2: Cache merge step (multi-repo aggregation)

In a second Bazel step `scripts_bazel/merge_sourcelinks.py`, **all per-repo caches** are merged into a **single combined JSON**.

- Input: N JSON caches (one per repo)
- Output: 1 merged JSON containing all found source_code_links

This step also fills in url & hash if there is a known_good_json provided (e.g. in a combo build)

(repo-metadata-rules)=
#### Repo metadata rules

Here are some basic rules regarding the MetaData information

In a combo build, a known_good_json **must** be provided.
If known_good_json is found then the hash & url will be filled for each need by the script.

Combo build:

- `repo_name`: repository name (parsed from filepath in step 1)
- `hash`: revision/commit hash (as provided by the known_good_json)
- `url`: repository remote URL (as provided by the known_good_json)

Local build:

- `repo_name`: 'local_repo'
- `hash`: will be empty at this point, and later filled via parsing the git commands
- `url`: will be empty at this point, and later filled via parsing the git commands

---

### Source Code Linker Extension

1a. **Reads the merged JSON** produced by Bazel
1b. **Reads test.xml files and generates testlinks JSON**
2. **Validates and adapts** both JSON cache files
3. **Merges and converts** them into the final structure: **RepoSourceLink**

#### Codelinks

Since these are all found in [Bazel step 1](#step-1-per-repository-cache-generation) this essentially does not run
anymore inside of the source_code_linker extension.

#### Testlinks

TestLink scans test result XMLs from Bazel (bazel-testlogs) or from the folder 'tests-report' and converts each test case with metadata into Sphinx external needs, allowing links from tests to requirements.
This depends on the `attribute_plugin` in our tooling repository, find it [here](https://github.com/eclipse-score/tooling/tree/main/python_basics/score_pytest)

:::attention
If TestLinks should be generated in a combo build please ensure that you have the known_good_json added to the docs macro.
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

1. **XML Parsing** (`xml_parser.py`)
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
     - `DataFromTestCase` (used for external needs)
     - `DataForTestLink` (used for linking tests to requirements)

> If there is a Classname then it gets combined with the function name for the displayed link as follows: `Classname__Functionname`

2. **Need Linking**
   - Generates external Sphinx needs from `DataFromTestCase`.
   - Creates `testlink` attributes on linked requirements.
   - Warns on missing need IDs.

#### Example JSON Cache (DataFromTestCase)

The DataFromTestCase depicts the information gathered about one testcase.

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
    "FullyVerifies": null
    "repo_name": "local_module",
    "hash": "",
    "url": "",
  }
]
```

---


### Early-Combined Links

During the Sphinx build process, both CodeLink and TestLink data are combined and grouped by needs.
This will allow us to have an easier time building the final JSON which will eliminate the metadata from each link,
and group all needs according to the appropriate repository.

This all is handled in `need_source_links.py`.

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
          "repo_name": "local_module",
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
          "repo_name": "local_module",
          "hash": "",
          "url": "",
        }
      ]
    }
  }
]
```

#### Final layout: RepoSourceLink

Instead of repeating `repo_name/hash/url` for every single link entry, the final output groups links **by repository**:

- Repository metadata appears **once per repository**
- All links belonging to that repository are stored beneath it

This somewhat looks like this:

```{code-block} json
[
  {
    "repo": {
      "name": "local_repo",
      "hash": "",
      "url": ""
    },
    "needs": [
      {
        "need": "tool_req__docs_common_attr_id_scheme",
        "links": {
          "CodeLinks": [
            {
              "file": "src/extensions/score_metamodel/checks/attributes_format.py",
              "line": 30,
              "tag": "# req-Id:",
              "need": "tool_req__docs_common_attr_id_scheme",
              "full_line": "# req-Id: tool_req__docs_common_attr_id_scheme"
            }
          ],
          "TestLinks": []
        }
      },
    ],
```
Due to not saving the `repo_name, url and hash` in each link but grouping them we can eleminate a lot of unnecessary
length to the JSON document here.

This is the structure the extension uses to attach links to needs (via the `source_code_link` attribute), while keeping the resulting data compact and normalized.

:::hint
Currently if the repo is the local one, SCL is still using the hash and url it gets from executing the git functions parsing.
This is a known inefficiency and will be improved upon later
:::

---

## Result: Traceability Links in Needs

During the Sphinx build process, the extension applies the computed links to needs:

- Each need’s `source_code_link` and `testlink` attribute is filled from the (repo-grouped) RepoSourceLink data where applicable.
- If a referenced need ID does not exist, a build warning will be raised.

---

## Known Limitations

### General

- In combo builds, known_good_json is required.
- inefficiencies in creating the links and saving the JSON caches
- Not compatible with **Esbonio/Live_preview**

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

1. **Bazel Script #1**: scan + parse → write **per-repo cache** (includes repo metadata if known)
2. **Bazel Script #2**: merge caches → write **single merged JSON**
3. **Sphinx Extension**: read merged JSON → adapt to **RepoSourceLink** → inject source_code_link and testlink into needs

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
├── merge_sourcelinks.py
└── tests
│   └── ...
```

The Sphinx extension

```text
score_source_code_linker/
├── __init__.py                   # Main Sphinx extension; combines CodeLinks + TestLinks
├── generate_source_code_links_json.py  # Most functionality moved to 'scripts_bazel/generate_sourcelinks_cli'
├── need_source_links.py         # Data model for combined links
├── repo_source_links.py         # Data model for Repo combined links (Final output JSON)
├── helpers.py                   # Misc. functions used throughout SCL
├── needlinks.py                 # CodeLink dataclass & JSON encoder/decoder
├── testlink.py                  # DataForTestLink definition & logic
├── xml_parser.py                # Parses XML files into test case data
├── tests/                       # Testsuite, containing unit & integration tests
│   └── ...
```

---

## Clearing Cache Manually

To clear the build cache, run:

```bash
rm -rf _build/
```

## Examples

To see working examples for CodeLinks & TestLinks, take a look at the Docs-As-Code documentation.

[Example CodeLink](https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_common_attr_id_scheme)
[Example CodeLink](https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_common_attr_status)

[Example TestLink](https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_dd_link_source_code_link)
