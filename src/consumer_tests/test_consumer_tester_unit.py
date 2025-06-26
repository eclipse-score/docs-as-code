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
"""
Unit tests for consumer tester functionality.

These tests validate the consumer test infrastructure without requiring
network access or actual consumer repositories.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Import pytest only if available (for bazel test runs)
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # Define a dummy pytest fixture decorator for when pytest is not available
    def pytest_fixture(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    pytest = type('pytest', (), {'fixture': pytest_fixture})

from .consumer_tester import ConsumerConfig, ConsumerTester, TestResult


class TestConsumerTester:
    """Unit tests for ConsumerTester class."""
    
    def test_consumer_config_creation(self):
        """Test creating ConsumerConfig objects."""
        config = ConsumerConfig(
            name="test_consumer",
            repo_url="https://github.com/test/test.git",
            commands=["test_command_1", "test_command_2"],
            branch="main",
            timeout=300
        )
        
        assert config.name == "test_consumer"
        assert config.repo_url == "https://github.com/test/test.git"
        assert config.commands == ["test_command_1", "test_command_2"]
        assert config.branch == "main"
        assert config.timeout == 300
    
    def test_test_result_creation(self):
        """Test creating TestResult objects."""
        result = TestResult(
            consumer_name="test_consumer",
            command="test_command",
            success=True,
            error_message=None,
            stdout="Build successful",
            stderr=""
        )
        
        assert result.consumer_name == "test_consumer"
        assert result.command == "test_command"
        assert result.success is True
        assert result.error_message is None
        assert result.stdout == "Build successful"
        assert result.stderr == ""
    
    def test_consumer_tester_initialization(self):
        """Test ConsumerTester initialization."""
        repo_path = Path.cwd()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            tester = ConsumerTester(repo_path, work_dir)
            
            assert tester.score_docs_as_code_path == repo_path.resolve()
            assert tester.work_dir == work_dir
    
    def test_default_consumers_config(self):
        """Test that default consumers are properly configured."""
        consumers = ConsumerTester.DEFAULT_CONSUMERS
        
        assert len(consumers) >= 3  # At least platform, process_description, module_template
        
        consumer_names = [c.name for c in consumers]
        assert "platform" in consumer_names
        assert "process_description" in consumer_names
        assert "module_template" in consumer_names
        
        # Check that each consumer has required fields
        for consumer in consumers:
            assert consumer.name
            assert consumer.repo_url
            assert consumer.commands
            assert isinstance(consumer.commands, list)
            assert len(consumer.commands) > 0
    
    def test_module_bazel_override(self):
        """Test MODULE.bazel override functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repo_path = temp_path / "fake_repo"
            consumer_path = temp_path / "consumer_repo"
            consumer_path.mkdir()
            
            # Create a test MODULE.bazel file
            module_bazel = consumer_path / "MODULE.bazel"
            module_bazel.write_text("""module(
    name = "test_consumer",
    version = "1.0.0",
)

bazel_dep(name = "rules_python", version = "1.4.1")
bazel_dep(name = "score_docs_as_code", version = "0.3.3")
""")
            
            tester = ConsumerTester(repo_path, temp_path)
            tester.override_module_bazel(consumer_path)
            
            # Check that the override was added
            modified_content = module_bazel.read_text()
            assert "local_path_override" in modified_content
            assert str(repo_path) in modified_content
            assert "score_docs_as_code" in modified_content
    
    def test_module_bazel_override_missing_dependency(self):
        """Test MODULE.bazel override when score_docs_as_code is not present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repo_path = temp_path / "fake_repo"
            consumer_path = temp_path / "consumer_repo"
            consumer_path.mkdir()
            
            # Create a test MODULE.bazel file without score_docs_as_code
            module_bazel = consumer_path / "MODULE.bazel"
            module_bazel.write_text("""module(
    name = "test_consumer",
    version = "1.0.0",
)

bazel_dep(name = "rules_python", version = "1.4.1")
""")
            
            tester = ConsumerTester(repo_path, temp_path)
            tester.override_module_bazel(consumer_path)
            
            # Check that both dependency and override were added
            modified_content = module_bazel.read_text()
            assert "bazel_dep(name = \"score_docs_as_code\"" in modified_content
            assert "local_path_override" in modified_content
            assert str(repo_path) in modified_content
    
    def test_generate_report(self):
        """Test report generation functionality."""
        repo_path = Path.cwd()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = ConsumerTester(repo_path, Path(temp_dir))
            
            # Create test results
            results = [
                TestResult("consumer1", "cmd1", True),
                TestResult("consumer1", "cmd2", False, "Error message 1", stderr="stderr1"),
                TestResult("consumer2", "cmd1", True),
                TestResult("consumer2", "cmd2", True),
            ]
            
            report = tester.generate_report(results)
            
            # Check summary
            assert report["summary"]["total_tests"] == 4
            assert report["summary"]["passed"] == 3
            assert report["summary"]["failed"] == 1
            assert report["summary"]["success_rate"] == 0.75
            
            # Check by_consumer breakdown
            assert "consumer1" in report["by_consumer"]
            assert "consumer2" in report["by_consumer"]
            assert report["by_consumer"]["consumer1"]["passed"] == 1
            assert report["by_consumer"]["consumer1"]["failed"] == 1
            assert report["by_consumer"]["consumer2"]["passed"] == 2
            assert report["by_consumer"]["consumer2"]["failed"] == 0
            
            # Check failed tests
            assert len(report["failed_tests"]) == 1
            assert report["failed_tests"][0]["consumer"] == "consumer1"
            assert report["failed_tests"][0]["command"] == "cmd2"
            assert report["failed_tests"][0]["error"] == "Error message 1"
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Build successful"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        repo_path = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = ConsumerTester(repo_path, Path(temp_dir))
            
            with tempfile.TemporaryDirectory() as consumer_dir:
                result = tester.run_command(Path(consumer_dir), "test_command")
                
                assert result.success is True
                assert result.error_message is None
                assert result.stdout == "Build successful"
                assert result.stderr == ""
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        # Mock failed subprocess result
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Build failed"
        mock_run.return_value = mock_result
        
        repo_path = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = ConsumerTester(repo_path, Path(temp_dir))
            
            with tempfile.TemporaryDirectory() as consumer_dir:
                result = tester.run_command(Path(consumer_dir), "test_command")
                
                assert result.success is False
                assert "Command failed with exit code 1" in result.error_message
                assert result.stderr == "Build failed"