# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Pytest tests for consumer regression testing."""

import os
import tempfile
from pathlib import Path
from typing import List

import pytest

from .consumer_tester import ConsumerConfig, ConsumerTester


@pytest.fixture(scope="session")
def score_docs_path() -> Path:
    """Get the path to the score_docs_as_code repository."""
    # Try to determine the repository root from the test file location
    current_dir = Path(__file__).parent
    repo_root = current_dir
    
    # Walk up until we find MODULE.bazel
    while repo_root != repo_root.parent:
        if (repo_root / "MODULE.bazel").exists():
            break
        repo_root = repo_root.parent
    else:
        # Fallback to current working directory
        repo_root = Path.cwd()
    
    return repo_root


@pytest.fixture(scope="session")
def consumer_tester(score_docs_path: Path) -> ConsumerTester:
    """Create a ConsumerTester instance."""
    # Use a temporary directory for testing
    work_dir = Path(tempfile.mkdtemp(prefix="pytest_consumer_tests_"))
    
    with ConsumerTester(score_docs_path, work_dir) as tester:
        yield tester


@pytest.fixture(scope="session")
def test_consumers() -> List[ConsumerConfig]:
    """
    Get the list of consumers to test.
    
    Can be overridden via environment variable CONSUMER_TEST_REPOS
    as a comma-separated list of consumer names.
    """
    # Allow filtering consumers via environment variable
    filter_consumers = os.environ.get("CONSUMER_TEST_REPOS", "").strip()
    
    all_consumers = ConsumerTester.DEFAULT_CONSUMERS
    
    if filter_consumers:
        consumer_names = [name.strip() for name in filter_consumers.split(",")]
        consumers = [c for c in all_consumers if c.name in consumer_names]
        if not consumers:
            pytest.skip(f"No consumers found matching filter: {consumer_names}")
        return consumers
    
    return all_consumers


class TestConsumerRegression:
    """Test class for consumer regression tests."""
    
    def test_all_consumers(self, consumer_tester: ConsumerTester, test_consumers: List[ConsumerConfig]):
        """
        Test all configured consumers.
        
        This test ensures that score_docs_as_code changes don't break downstream consumers.
        """
        results = consumer_tester.test_all_consumers(test_consumers)
        
        # Generate and print report
        consumer_tester.print_report(results)
        
        # Check for failures
        failed_results = [r for r in results if not r.success]
        
        if failed_results:
            # Create a detailed failure message
            failure_messages = []
            for result in failed_results:
                msg = f"{result.consumer_name}/{result.command}: {result.error_message}"
                if result.stderr:
                    # Include relevant error details
                    stderr_lines = result.stderr.split('\n')
                    relevant_lines = [line for line in stderr_lines[-5:] if line.strip()]
                    if relevant_lines:
                        msg += f" | {' | '.join(relevant_lines)}"
                failure_messages.append(msg)
            
            pytest.fail(
                f"Consumer regression tests failed. "
                f"{len(failed_results)} out of {len(results)} tests failed:\n" +
                "\n".join(f"  - {msg}" for msg in failure_messages)
            )
    
    @pytest.mark.parametrize("consumer", ConsumerTester.DEFAULT_CONSUMERS, ids=lambda c: c.name)
    def test_individual_consumer(self, consumer_tester: ConsumerTester, consumer: ConsumerConfig):
        """
        Test individual consumers.
        
        This allows running tests for specific consumers and provides better
        granularity in test reporting.
        """
        # Check if this consumer should be tested
        filter_consumers = os.environ.get("CONSUMER_TEST_REPOS", "").strip()
        if filter_consumers:
            consumer_names = [name.strip() for name in filter_consumers.split(",")]
            if consumer.name not in consumer_names:
                pytest.skip(f"Consumer {consumer.name} not in test filter")
        
        results = consumer_tester.test_consumer(consumer)
        
        # Check for failures
        failed_results = [r for r in results if not r.success]
        
        if failed_results:
            failure_messages = []
            for result in failed_results:
                msg = f"{result.command}: {result.error_message}"
                if result.stderr:
                    stderr_lines = result.stderr.split('\n')
                    relevant_lines = [line for line in stderr_lines[-3:] if line.strip()]
                    if relevant_lines:
                        msg += f" | {' | '.join(relevant_lines)}"
                failure_messages.append(msg)
            
            pytest.fail(
                f"Consumer {consumer.name} tests failed. "
                f"{len(failed_results)} out of {len(results)} commands failed:\n" +
                "\n".join(f"  - {msg}" for msg in failure_messages)
            )


# Utility functions for custom test configurations

def create_custom_consumer_test(name: str, repo_url: str, commands: List[str], branch: str = "main"):
    """
    Create a custom consumer test configuration.
    
    This function can be used to add additional consumers without modifying the main code.
    
    Example:
        def test_my_custom_consumer(consumer_tester):
            custom_consumer = create_custom_consumer_test(
                "my_repo",
                "https://github.com/myorg/my_repo.git",
                ["docs_incremental_latest"]
            )
            results = consumer_tester.test_consumer(custom_consumer)
            # Check results...
    """
    return ConsumerConfig(
        name=name,
        repo_url=repo_url,
        commands=commands,
        branch=branch
    )