# Docs-As-Code Consumer Tests

This test validates that changes to the docs-as-code system don't break downstream consumers. 
It tests both local changes and git-based overrides against real consumer repositories.

## Quick Start

```bash
# Create the virtual environment
bazel run //docs:ide_support

# Run with std. configuration
.venv_docs/bin/python -m pytest -s src/tests

# Run with more verbose output (up to -vvv)
.venv_docs/bin/python -m pytest -s -v src/tests 

# Run specific repositories only
.venv_docs/bin/python -m pytest -s src/tests --repo-tests=score

# Use persistent cache for faster subsequent runs
.venv_docs/bin/python -m pytest -s src/tests --keep-temp

# Or combine both option
.venv_docs/bin/python -m pytest -s src/tests --keep-temp --repo-tests=score
```

## Verbosity Levels

The test suite supports different levels of output detail:

- **No flags**: Basic test results and summary table
- **`-v`**: Shows detailed warnings breakdown by logger type
- **`-vv`**: Adds full stdout/stderr output from build commands
- **`-vvv`**: Streams build output in real-time (useful for debugging hanging builds)

## Command Line Options

### `--keep-temp`
Enables persistent caching for faster development cycles.

**What it does:**
- Uses `~/.cache/docs_as_code_consumer_tests` instead of temporary directories
- Reuses cloned repositories between runs (with git updates)
- Significantly speeds up subsequent test runs

**When to use:** During development when running tests multiple times.

### `--repo-tests`
Filters which repositories to test.

**Usage:**
```bash
# Test only the 'score' repository
.venv_docs/bin/python -m pytest -s src/tests --repo-tests=score

# Test multiple repositories
.venv_docs/bin/python -m pytest -s src/tests --repo-tests=score,module_template

# Invalid repo names fall back to testing all repositories
.venv_docs/bin/python -m pytest -s src/tests --repo-tests=nonexistent
```

**Available repositories:** Check `REPOS_TO_TEST` in the test file for current list.

## Currently tested repositories

- [score](https://github.com/eclipse-score/score)
- [process_description](https://github.com/eclipse-score/process_description)
- [module_template](https://github.com/eclipse-score/module_template)

## What Gets Tested

For each repository, the test:
1. Clones the consumer repository
2. Tests with **local override** (your current changes)
3. Tests with **git override** (current commit from remote)
4. Runs build commands and test commands
5. Analyzes warnings and build success

## Example Development Workflow

```bash
# Create the virtual environment
bazel run //docs:ide_support

# First run - clones everything fresh
.venv_docs/bin/python -m pytest -s src/tests --keep-temp --repo-tests=score -v

# Make changes to docs-as-code...

# Subsequent runs - much faster due to caching
.venv_docs/bin/python -m pytest -s src/tests --keep-temp --repo-tests=score -v

# Final validation - test all repos
.venv_docs/bin/python -m pytest -s src/tests --keep-temp -v
```
