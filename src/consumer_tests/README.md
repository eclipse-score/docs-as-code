# Consumer Tests for score_docs_as_code

This directory contains regression tests for `score_docs_as_code` that ensure changes don't break downstream consumers.

## Overview

The consumer tests validate that changes to `score_docs_as_code` are compatible with its main consumers by:

1. Cloning consumer repositories
2. Overriding their `MODULE.bazel` to use the local version of `score_docs_as_code`
3. Running documentation build commands
4. Collecting and reporting any errors

## Usage

### Running Tests with Bazel

```bash
# Run all consumer tests
bazel test //src/consumer_tests:test_consumer_regression

# Run the consumer test script directly
bazel run //src/consumer_tests:run_consumer_tests

# Run tests for specific consumers only
CONSUMER_TEST_REPOS="platform,process_description" bazel test //src/consumer_tests:test_consumer_regression
```

### Running Tests with Python

```bash
# Install dependencies and run with pytest
python -m pytest src/consumer_tests/test_consumer_regression.py

# Run the consumer test script directly
python src/consumer_tests/consumer_tester.py --help

# Test specific consumers
python src/consumer_tests/consumer_tester.py --consumer platform --consumer process_description

# Save detailed report
python src/consumer_tests/consumer_tester.py --output consumer_test_report.json
```

## Default Consumers

The tests are configured to test the following consumers by default:

- **platform** (`eclipse-score/score`): Main S-CORE platform repository
- **process_description** (`eclipse-score/process_description`): Process documentation
- **module_template** (`eclipse-score/module_template`): Template for new modules

Each consumer is tested with these documentation commands (if they exist):
- `docs_incremental_latest`
- `docs_incremental_release`
- `docs_live_preview_latest`
- `docs_live_preview_release`
- `docs_docs_latest`
- `docs_docs_release`

## Adding New Consumers

### Method 1: Modify Default Configuration

Edit `consumer_tester.py` and add to the `DEFAULT_CONSUMERS` list:

```python
ConsumerConfig(
    name="my_new_consumer",
    repo_url="https://github.com/eclipse-score/my_new_consumer.git",
    commands=[
        "docs_incremental_latest",
        "docs_incremental_release",
        # Add other commands as needed
    ],
    branch="main",  # Optional: specify branch
    timeout=300     # Optional: specify timeout in seconds
)
```

### Method 2: Custom Test Function

Create a custom test in your own test file:

```python
from src.consumer_tests.test_consumer_regression import create_custom_consumer_test

def test_my_custom_consumer(consumer_tester):
    custom_consumer = create_custom_consumer_test(
        "my_repo",
        "https://github.com/myorg/my_repo.git", 
        ["docs_incremental_latest"]
    )
    results = consumer_tester.test_consumer(custom_consumer)
    
    failed_results = [r for r in results if not r.success]
    assert not failed_results, f"Custom consumer test failed: {failed_results}"
```

### Method 3: Environment Variable Configuration

Set the `CONSUMER_TEST_REPOS` environment variable to test only specific consumers:

```bash
export CONSUMER_TEST_REPOS="platform,my_new_consumer"
bazel test //src/consumer_tests:test_consumer_regression
```

## Configuration Options

### ConsumerConfig Parameters

- `name`: Unique name for the consumer
- `repo_url`: Git repository URL to clone
- `commands`: List of Bazel documentation commands to test
- `branch`: Git branch to checkout (default: "main")
- `timeout`: Timeout in seconds for each command (default: 300)

### Environment Variables

- `CONSUMER_TEST_REPOS`: Comma-separated list of consumer names to test
- `CONSUMER_TEST_WORK_DIR`: Working directory for cloning repositories

## How It Works

1. **Repository Cloning**: Each consumer repository is cloned to a temporary directory
2. **MODULE.bazel Override**: The `MODULE.bazel` file is modified to add:
   ```starlark
   local_path_override(module_name = "score_docs_as_code", path = "/path/to/local/repo")
   ```
3. **Command Execution**: Each configured documentation command is run via `bazel run //docs:{command}`
4. **Error Collection**: Only errors are collected and reported; successful runs are summarized
5. **Report Generation**: Results are presented in both human-readable and JSON formats

## Integration with CI

The consumer tests are designed to be integrated into CI workflows. They are tagged as:
- `manual`: Must be explicitly requested
- `integration`: Integration test category  
- `requires-network`: Needs network access to clone repositories

### GitHub Actions Integration

Add to your workflow:

```yaml
- name: Run Consumer Tests
  run: bazel test //src/consumer_tests:test_consumer_regression
  # Only run on specific events or manually
  if: github.event_name == 'release' || contains(github.event.pull_request.labels.*.name, 'test-consumers')
```

## Troubleshooting

### Common Issues

1. **Network Access**: Tests require internet access to clone repositories
2. **Bazel Version**: Consumer repositories may require specific Bazel versions
3. **Build Dependencies**: Consumers may have additional build requirements
4. **Command Availability**: Not all consumers may have all documentation commands

### Debug Mode

For detailed debugging, run the consumer test script directly:

```bash
python src/consumer_tests/consumer_tester.py --consumer platform --output debug_report.json
```

Check the `debug_report.json` file for detailed stdout/stderr from each command.

### Skipping Commands

If a consumer doesn't have a specific documentation command, it will be automatically skipped. The test checks for target existence before running commands.

## Contributing

When adding new consumers or modifying the test infrastructure:

1. Ensure the consumer has appropriate documentation commands
2. Test locally before submitting changes
3. Update this README if adding new configuration options
4. Consider the impact on CI runtime when adding new consumers

## Architecture

```
src/consumer_tests/
├── __init__.py                    # Package initialization
├── consumer_tester.py             # Main consumer testing logic
├── test_consumer_regression.py    # Pytest wrapper and test cases
├── BUILD                          # Bazel build configuration
└── README.md                      # This documentation
```

The main classes:

- `ConsumerConfig`: Configuration for a consumer repository
- `TestResult`: Result of running a single command
- `ConsumerTester`: Main test runner with context management
- `TestConsumerRegression`: Pytest test class