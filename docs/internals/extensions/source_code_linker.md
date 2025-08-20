(source-code-linker)=
# Score Source Code Linker

A Sphinx extension for enabling **source code and test traceability** for requirements.  
This extension integrates with **Bazel** and **sphinx-needs** to automatically generate traceability links between implementation, tests, and documentation.

---

## Overview

The extension is split into two main components:

- **CodeLink** – Parses source files for template strings and links them to needs.
- **TestLink** – Parses test.xml outputs inside `bazel-testlogs` to link test cases to requirements.

Each component stores intermediate data in JSON caches under `_build/` to optimize performance and speed up incremental builds.

---

## How It Works

### ✅ CodeLink: Source Code Integration

CodeLink scans repository files (excluding `_`, `.`, and binary formats) for requirement tags such as:

```python
# Choose one or the other, both mentioned here to avoid detection
# req-Id/req-traceability: <NEED_ID>
```

These tags are extracted and matched to Sphinx needs via the `source_code_link` attribute. If a need ID does not exist, a build warning will be raised.

#### Data Flow

1. **File Scanning** (`generate_source_code_links_json.py`)
   - Filters out files starting with `_`, `.`, or ending in `.pyc`, `.so`, `.exe`, `.bin`.
   - Searches for template tags: `#<!-- comment prevents parsing this occurance --> req-Id:` and `#<!-- comment prevents parsing this occurance --> req-traceability:`.
   - Extracts:
     - File path
     - Line number
     - Tag and full line
     - Associated need ID
   - Saves data as JSON via `needlinks.py`.

2. **Link Creation**
   - Git info (file hash) is used to build a GitHub URL to the line in the source file.
   - Links are injected into needs via the `source_code_link` attribute during the Sphinx build process.

#### Example JSON Cache (CodeLinks)

```
[
  {
    "file": "src/extensions/score_metamodel/metamodel.yaml",
    "line": 17,
    "tag": "#--req-Id:", # added `--` to avoid detection
    "need": "tool_req__docs_dd_link_source_code_link",
    "full_line": "#--req-Id: tool_req__docs_dd_link_source_code_link" # added `--` to avoid detection
  }
]
```

---

### ✅ TestLink: Test Result Integration

TestLink scans test result XMLs from Bazel and converts each test case with metadata into Sphinx external needs, allowing links from tests to requirements.
This depends on the `attribute_plugin` in our tooling repository, find it [here](https://github.com/eclipse-score/tooling/tree/main/python_basics/score_pytest)
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
   - Scans `bazel-testlogs/` for `test.xml` files.
   - Parses test cases and extracts:
     - Name
     - File path
     - Line
     - Result (e.g. passed, failed, skipped)
     - Result text (if failed/skipped will check if message was attached to it)
     - Verifications (`PartiallyVerifies`, `FullyVerifies`)

   - Cases without metadata are logged out as info (not errors).
   - Test cases with metadata are converted into:
     - `DataFromTestCase` (used for external needs)
     - `DataForTestLink` (used for linking tests to requirements)

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
  }
]
```

---

## 🔗 Combined Links

During the Sphinx build process, both CodeLink and TestLink data are combined and applied to needs.

This is handled in `__init__.py` using the `NeedSourceLinks` and `SourceCodeLinks` dataclasses from `need_source_links.py`.

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
          "full_line": "#--req-Id: tool_req__docs_common_attr_title" # added `--` to avoid detection
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
          "result_text": ""
        }
      ]
    }
  }
]
```


---

## ⚠️ Known Limitations

### CodeLink

- ❌ Not compatible with **Esbonio/Live_preview**
- 🔗 GitHub links may 404 if the commit isn’t pushed
- 🧪 Tags must match exactly (e.g. #<!-- comment prevents parsing this occurance --> req-Id)
- 👀 `source_code_link` isn’t visible until the full Sphinx build is completed

### TestLink

- ❌ Not compatible with **Esbonio/Live_preview**
- 🔗 GitHub links may 404 if the commit isn’t pushed
- 🧪 XML structure must be followed exactly (e.g. `properties & attributes`)
- 🗂 Relies on test to be executed first



---

## 🏗️ Internal Module Overview

```
score_source_code_linker/
├── __init__.py                   # Main Sphinx extension; combines CodeLinks + TestLinks
├── generate_source_code_links_json.py  # Parses source files for tags
├── need_source_links.py         # Data model for combined links
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

## Examples:
To see working examples for CodeLinks & TestLinks, take a look at the Docs-As-Code documentation.

[Example CodeLink](https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_common_attr_id_scheme)
[Example CodeLink](https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_common_attr_status)

[Example TestLink](https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_dd_link_source_code_link)

## Flow-Overview
```{mermaid}
flowchart TD
    %% Entry Point
    A[source_code_linker] --> B{Check for Grouped JSON Cache}

    %% If cache exists
    B -->|Yes| C[Load Grouped JSON Cache]
    %% Cache does not exist
    B --> N9[NO]

    %% --- NeedLink Path ---
    N9 --> D1[needslink.py<br><b>NeedLink</b>]
    D1 --> E1{Check for CodeLink JSON Cache}

    E1 -->|Yes| F1[Load CodeLink JSON Cache]
    F1 --> Z[Grouped JSON Cache]

    E1 -->|No| G1[Parse all files in repository]
    G1 --> H1[Build & Save<br>CodeLink JSON Cache]
    H1 --> Z

    %% --- TestLink Path ---
    N9 --> D2[testlink.py<br><b>DFTL</b>]
    D2 --> E2{Check for DFTL Cache}

    E2 -->|Yes| F2[Load DFTL JSON Cache]
    F2 --> J2[Load DOTC JSON Cache]
    J2 --> K2[Add as External Needs to project]

    E2 -->|No| G2[Parse test.xml Files]
    G2 --> H2[Convert Each TestCase<br>to DOTC Format]
    H2 --> I2[Build & Save<br>DOTC JSON Cache]
    H2 --> K2

    H2 --> M2[Convert to<br>DFTL]
    M2 --> N2[Build & Save<br>DFTL JSON Cache]


    %% Final step
    N2 --> Z[Build & Save<br><b>Grouped JSON Cache</b>]
    Z --> FINAL[<b>Add testlinks to requirements</b>]

    %% Legend
    subgraph Legend[" "]
        direction TB
        L1[NeedLink Operations]
        L2[TestLink Operations]
        L4[DTFL = DataForTestLink]
        L3[TestCaseNeed Operations]
        L5[DOTC = DataOfTestCase]
        L1 ~~~ L2
        L2 ~~~ L4
        L4 ~~~ L3
        L3 ~~~ L5
    end

    %% Styling
    classDef needlink fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af
    classDef testlink fill:#e0e7ff,stroke:#7c3aed,stroke-width:2px,color:#5b21b6
    classDef dotc fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e

    class D1,E1,F1,G1,H1 needlink
    class D2,E2,F2,G2,M2,N2 testlink
    class J2,H2,I2,K2 dotc
    
    %% Apply legend styling
    class L1 needlink
    class L2,L4 testlink
    class L3,L5 dotc


    %% Styling
    classDef needlink fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af
    classDef testlink fill:#e0e7ff,stroke:#7c3aed,stroke-width:2px,color:#5b21b6
    classDef dotcn fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e

    class D1,E1,F1,G1,H1 needlink
    class D2,E2,F2,G2,M2,N2 testlink
    class J2,H2,I2,K2 dotcn
```
