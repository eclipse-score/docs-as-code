# Docs-As-Code Consumer Tests

This test validates that changes to the docs-as-code system don't break downstream consumers.
It tests both local changes and git-based overrides against real consumer repositories.

## Use in CI

If you want to start the consumer tests on a PR inside `docs-as-code`, then all you have to do is comment
`/consumer-test` on the PR and this should trigger them.

## Quick Start

```bash
# Create the virtual environment
bazel run //:ide_support

# Run with std. configuration
.venv_docs/bin/python -m pytest -s src/tests

# Run with more verbose output (up to -vvv)
.venv_docs/bin/python -m pytest -s -v src/tests

# Run specific repositories only
.venv_docs/bin/python -m pytest -s src/tests --repo=score

# Disable the persistent cache
.venv_docs/bin/python -m pytest -s src/tests --disable-cache

# Or combine both options
.venv_docs/bin/python -m pytest -s src/tests --disable-cache --repo=score
```

## Verbosity Levels

The test suite supports different levels of output detail:

- **No flags**: Basic test results and summary table
- **`-v`**: Shows detailed warnings breakdown by logger type
- **`-vv`**: Adds full stdout/stderr output from build commands
- **`-vvv`**: Streams build output in real-time (useful for debugging hanging builds)

## Command Line Options

### `--disable-cache`
Disabled persistent caching for clean testing cycle.

**What the test normaly do:**
- Uses `~/.cache/docs_as_code_consumer_tests` instead of temporary directories
- Reuses cloned repositories between runs (with git updates)
- Significantly speeds up subsequent test runs

**This option disables the above mentioned behaviour and clones the repositories fresh**

**When to use:** During development when you need to ensure testing is done on a fresh env.

### `--repo`
Filters which repositories to test.

**Usage:**
```bash
# Test only the 'score' repository
.venv_docs/bin/python -m pytest -s src/tests --repo=score

# Test multiple repositories
.venv_docs/bin/python -m pytest -s src/tests --repo=score,module_template

# Invalid repo names fall back to testing all repositories
.venv_docs/bin/python -m pytest -s src/tests --repo=nonexistent
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
bazel run //:ide_support

# First run - clones everything fresh
.venv_docs/bin/python -m pytest -s -v src/tests --repo=score

# Make changes to docs-as-code...

# Subsequent runs - much faster due to caching
.venv_docs/bin/python -m pytest -s -v src/tests --repo=score

# Final validation - test all repos without cache
.venv_docs/bin/python -m pytest -s -v src/tests --disable-cache
```
