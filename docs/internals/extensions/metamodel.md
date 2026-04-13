(metamodel)=
# score_metamodel

The `score_metamodel` extension is a core extension/component of the Docs-As-Code.
It provides metamodel definitions, validation checks, and project layout management for Sphinx documentation.

## Overview

This extension serves multiple critical functions:

- **Metamodel Definition**: Houses the project's metamodel schema and configuration
- **Validation System**: Implements comprehensive checks to ensure documentation compliance
- **External Needs Management**: Imports external needs from dependencies
- **Project Layout**: Manages the rendering, look and feel of documentation
- **Integration Testing**: Provides RST-based tests to validate metamodel behavior

## Core Components

### Metamodel Definition
The extension contains:
- `metamodel.yaml`: The main metamodel definition
- `metamodel-schema.json`: JSON schema for validation
- Setting configuration parameters based on input that get passed on to sphinx-needs

### Validation System
The extension implements a multi-tier checking system:

**Local Checks**: Validate individual needs using only their own data
- Run faster as they don't require the full needs graph
- Examples: ID format validation, prohibited words, attribute formatting

**Graph-Based Checks**: Validate needs in the context of their relationships
- Require access to the complete needs graph
- Examples: Link validation, dependency checking, cross-reference verification

This extension comes with Docs-As-Code.
Add `score_metamodel` to your extensions in `conf.py`:

```python
extensions = [
    ...
    'score_metamodel',
    ...
]
```

## need types

Each type of needs is defined in the `needs_types` section of the `metamodel.yaml` file. Each need type has attributes, links, tags, and other properties that define its structure and behavior within the documentation system.

Each need type is introduced via `<type-name>:` followed by its properties indented under it.

Properties:
- **title**: The title of the need type.
- **prefix**: A unique prefix used to identify the need type. Default is the type name followed by `__`.
- **mandatory_options**: A list of mandatory options that must be provided for the need type.
  `id` is worth mentioning as it is automatically included and must be unique. Default is the prefix followed by `[a-z0-9_]`.
- **optional_options**: A list of optional options that can be provided for the need type.
- **mandatory_links**: A list of mandatory links to other need types that must be included.
- **optional_links**: A list of optional links to other need types that can be included.
- **tags**: A list of tags associated with the need type.
- **parts**: The number of parts (separated by `__`) within the need ID.

## Creating New Validation Checks

The extension automatically discovers checks from the `checks/` directory and the metamodel.yaml config. There are several types of checks you can implement:

### 1. Need-Local Checks (Configuration-Based)
These checks validate individual needs using regex patterns. They're defined in `metamodel.yaml` and are the easiest to create.

All definitions are parsed as regex and evaluated as such, keep that in mind.
They can be found inside the metamodel.yml and are how we define needs. See an example here:

```yaml
needs_types:
  gd_req:
    title: Process Requirements
    prefix: gd_req__
    # All options&links defined below are checked if they follow the defined regex in the need itself
    mandatory_options:
      id: ^gd_req__[0-9a-z_]*$
      status: ^(valid|draft)$
      content: ^[\s\S]+$ # multiline non empty matching
    optional_links:
      satisfies: ^wf__.*$
      complies: ^std_req__(iso26262|isosae21434|isopas8926|aspice_40)__.*$ #can only be one of these
    tags:
      - requirement # grouping of similar needs together in order to make some other checks easier to write
    parts: 2 # has to have exactly one `__` inside the ID
```

### 2. Generic Graph Checks (Configuration-Based)
Generic graph checks are defined in the metamodel.yaml under `graph_checks`.
These checks follow the same structure:

```yaml
<name of the check>:
  needs:
    include: <need1>, <need2> #list of your needs
    condition: <your condition(s) that need to be fulfilled>
  check:
    <link attribute to check>: <condition to be checked in each need inside the link attribute>
  explanation: <A short sentence that explains what is required to be adhered to. This will be
              < part of the error message if the check fails>
```

> *Note:* You can also use multiple conditions or negate conditions in either the needs or check part.

A complete example might look like so:

```yaml
graph_checks:
  tool_req__docs_req_arch_link_safety_to_arch:
    needs:
      include: feat_arc_sta, logic_arc_int, logic_arc_int_op, comp_arc_sta, real_arc_int, real_arc_int_op
      condition:
        and:
          - safety != QM
          - status == valid
    check:
      implements:
        and:
          - safety != QM
          - status == valid
    explanation: A safety architecture element can only link other safety architecture elements.
```

Purpose of this check:
This check will go through each of the needs mentioned in 'include' that match the condition, and then for every single one of them check the needs that are linked inside the 'implements' attribute. Check whether those needs also fulfill the condition.
If one of them does not fulfill the condition the check fails and will let you know with a warning that it did so.

### 3. Prohibited Word Checks (Configuration-Based)
For preventing specific words for specific needs in certain attributes.
This is also defined in metamodel and follows the following schema:

```yaml
prohibited_words_checks:
  <check name>:
    types[OPTIONAL]: # If you skip this, all needs will be checked.
        - < you can specify here that only needs with this tag will get checked for this check>
    <attribute to check>:
        - < word to forbid >
        - < word to forbid >
```

An example might look like this:
```yaml
prohibited_words_checks:
  content_check:
    types:
      - requirement_excl_process
    content:
      - just
      - about
      - really
      - some
      - thing
      - absolutely
```

For all needs that have the `tag` 'requirement_excl_process' **inside the metamodel.yaml** this check will now verify that the `content` or the `description` does not contain any of the mentioned words in the list.

### 4. Custom Local Checks (Python Code)
If you need something that the generic local or graph checks can not fulfill, then you can also add a custom check.
Ensure this check is inside a python file that is placed in the `check` folder in this extension.
Do not forget to add the applicable decorator to the function.

This means all validations can be done using only the information within the need itself, and you do not need access to any of the linked needs or other needs inside the documentation.

Your function will receive the Sphinx `app`, the current `need` to check and a `log` to log messages.

```python
from score_metamodel.checks import local_check

@local_check
def my_local_check(app, need, log):
    # Validate individual need properties
    # Example: If option_a == '2' then option_b is required to be not empty
    pass
```

> Check existing files in the `checks/` folder for real examples.

### 5. Custom Graph Checks (Python Code)
These checks need to access linked needs in order to fully verify the specified behavior.
The signature is similar to that of local_check, but instead of one need, you will get `all_needs`.

```python
from score_metamodel.checks import graph_check

@graph_check
def my_custom_graph_check(app, all_needs, log):
    # Complex validation with full graph access
    # Example: if option_a == '2' then each linked requirement needs to also have option_a == '2'
    pass
```

> Check existing files in the `checks/` folder for real examples.

## File Structure Reference

```
score_metamodel/
├── BUILD
├── __init__.py
├── checks
│   ├── __init__.py
│   ├── attributes_format.py
│   ├── check_options.py
│   ├── graph_checks.py
│   ├── id_contains_feature.py
│   └── standards.py
├── external_needs.py
├── log.py
├── metamodel-schema.json
├── metamodel.yaml
└── tests
    ├── __init__.py
    ├── rst
    │   ├── attributes
    │   │   └── ...
    │   ├── conf.py
    │   ├── graph
    │   │   └── test_metamodel_graph.rst
    │   ├── id_contains_feature
    │   │   └── test_id_contains_feature.rst
    │   └── options
    │       └── test_options_options.rst
    └── ...
```

## Testing Your Changes

The extension is setup for comprehensive testing:

To add tests for new checks:
- **Unit Tests**: Test individual additions, if they are not covered by the present unit-tests
- **Integration Tests**: Add RST-based tests in `tests/rst/` that validate the metamodel in realistic scenarios. Make sure to have at least one good and one bad case.

1. Add unit tests in the appropriate `test_*.py` file
2. Create RST integration tests in `tests/rst/` to verify behavior in Sphinx. Ensure thematically it's in the right folder

## Architecture Decision: Local vs Graph-Based Checks

While sphinx-needs provides a powerful warning mechanism, it's limited to need-local checks. This extension implements a custom multi-tier system because:

- **Performance**: Local checks run faster and can provide immediate feedback
- **Flexibility**: Graph-based checks enable complex relationship validation
- **Control**: Custom implementation allows for more elaborate validation logic
- **Future-proofing**: Provides foundation for advanced validation features
