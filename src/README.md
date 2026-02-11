# S-CORE Project Tooling Development Guide

*This document is meant for *developers* of doc-as-code.*
It should be treated as a 'get-started' guide, giving you all needed information to get up and running.

## Quick Start

1. Clone the repository
2. Setup the environment
- *No Devcontainer*
    1. Install Bazelisk (version manager for Bazel)
    2. Create the Python virtual environment:
   ```bash
   bazel run //your-docs-dir:ide_support
   ```
    3. Select `.venv_docs/bin/python` as the python interpreter inside your IDE
    *Note: This virtual environment does **not** have pip, therefore `pip install` is not available.*
<br>

- *With Devcontainer (VSCode)*
    1. Click the `reopen current folder in dev container` prompt
        -  If no prompt appears: `ctrl+shift+p` => `Dev Containers: Reopen in Containers`


## Development Environment Requirements

- **Operating System**: Linux (required)
- **Core Tools**:
  - Bazel
  - Python
  - Git
  - **VSCode** (Optional)
    - Several integrations and guides are developed primarily with VS Code in mind.



### Key external tools used inside `_tooling`

1. **Bazel Build System**
   - Primary build orchestrator
   - Handles dependency management
   - Coordinates testing and documentation
   - Manages multi-repository setup

2. **Documentation Tools**
   - Sphinx with custom extensions
   - Esbonio for IDE integration
   - Real-time documentation validation

3. **Development Tools**
   - Gitlint for commit message standards
   - Pytest for testing infrastructure
   - Custom formatters and linters



## score_docs_as_code Directory Architecture

```
src/
├── assets/           # Documentation styling (CSS)
├── decision_records/ # Architecture Decision Records (ADRs)
├── extensions/       # Custom Sphinx extensions
│   └── score_metamodel/
│       ├── checks/   # Sphinx-needs validation
│       └── tests/    # Extension test suite
└── templates/        # HTML templates
```


Find all important Bazel commands in the [project README](/README.md)

Find everything related to testing and how to add your own test suite [here](/src/tests/README.md)

## Developing new tools

1. Place code in appropriate directory or create new ones. E.g. sphinx-extensions inside `extensions`
2. Create a dedicated test directory
3. Include an appropriate README in markdown

> If you want to develop your own Sphinx extension, check out the [extensions guide](/src/extensions/README.md)

## Updating dependencies

The file [requirements.in](./requirements.in) is a [PIP requirements file](https://pip.pypa.io/en/stable/reference/requirements-file-format/) that describe first level dependencies.

The file [requirements.txt](./requirements.txt) is a [pip-compile lock file](https://pip-tools.readthedocs.io/en/latest/cli/pip-compile/) that holds
the pinned dependency tree calculated from [requirements.in](./requirements.in).

To update dependencies (e.g. after adding a dependency), run:
```
bazel run //src:requirements.update
```

To update the full dependency tree, run
```
bazel run //src:requirements.update -- --upgrade
```

## Best Practices

1. **Documentation**
   - Keep READMEs up-to-date
   - Document architectural decisions in `decision_records/`
   - Include examples in extension documentation

2. **Testing**
   - Write tests for all new functionality
   - Use appropriate test sizes (small/medium/large)
   - Include both positive and negative test cases

3. **Code Organization**
   - Follow existing directory structure
   - Keep extensions modular and focused
   - Use consistent naming conventions

## Troubleshooting

Common issues and solutions:

1. **Bazel Build Failures**
   - Check Bazel version compatibility
   - Verify Python environment
   - Review recent changes to BUILD files

2. **Documentation Build Issues**
   - Validate Sphinx configuration
   - Check for RST syntax errors
   - Verify extension dependencies

## Additional Resources
- [Sphinx extension guide](/src/extensions/README.md)
- [S-CORE Metamodel Documentation](/src/extensions/score_metamodel/README.md)
- [Pytest Integration Guide](/tools/testing/pytest/README.md)
