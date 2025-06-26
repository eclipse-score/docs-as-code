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
Consumer regression tests for score_docs_as_code.

This module tests that changes to score_docs_as_code do not break
its main downstream consumers.
"""

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ConsumerConfig:
    """Configuration for a consumer repository."""
    
    name: str
    repo_url: str
    commands: List[str]
    branch: str = "main"
    timeout: int = 300  # 5 minutes default timeout


@dataclass
class TestResult:
    """Result of testing a consumer."""
    
    consumer_name: str
    command: str
    success: bool
    error_message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class ConsumerTester:
    """Test runner for score_docs_as_code consumers."""
    
    # Default consumer configurations
    DEFAULT_CONSUMERS = [
        ConsumerConfig(
            name="platform",
            repo_url="https://github.com/eclipse-score/score.git",
            commands=[
                "docs_incremental_latest",
                "docs_incremental_release", 
                "docs_live_preview_latest",
                "docs_live_preview_release",
                "docs_docs_latest",
                "docs_docs_release",
            ]
        ),
        ConsumerConfig(
            name="process_description",
            repo_url="https://github.com/eclipse-score/process_description.git",
            commands=[
                "docs_incremental_latest",
                "docs_incremental_release",
                "docs_live_preview_latest", 
                "docs_live_preview_release",
                "docs_docs_latest",
                "docs_docs_release",
            ]
        ),
        ConsumerConfig(
            name="module_template",
            repo_url="https://github.com/eclipse-score/module_template.git",
            commands=[
                "docs_incremental_latest",
                "docs_incremental_release",
                "docs_live_preview_latest",
                "docs_live_preview_release", 
                "docs_docs_latest",
                "docs_docs_release",
            ]
        ),
    ]
    
    def __init__(self, score_docs_as_code_path: Path, work_dir: Optional[Path] = None):
        """
        Initialize the consumer tester.
        
        Args:
            score_docs_as_code_path: Path to the local score_docs_as_code repository
            work_dir: Optional working directory for cloning repos (uses temp dir if None)
        """
        self.score_docs_as_code_path = Path(score_docs_as_code_path).resolve()
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix="consumer_tests_"))
        self.work_dir.mkdir(exist_ok=True)
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup work directory."""
        if self.work_dir.exists() and self.work_dir.name.startswith("consumer_tests_"):
            shutil.rmtree(self.work_dir)
    
    def clone_consumer(self, consumer: ConsumerConfig) -> Path:
        """
        Clone a consumer repository.
        
        Args:
            consumer: Consumer configuration
            
        Returns:
            Path to the cloned repository
        """
        repo_path = self.work_dir / consumer.name
        
        if repo_path.exists():
            shutil.rmtree(repo_path)
            
        cmd = ["git", "clone", "--depth", "1", "-b", consumer.branch, consumer.repo_url, str(repo_path)]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return repo_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone {consumer.name}: {e.stderr}")
    
    def override_module_bazel(self, repo_path: Path) -> None:
        """
        Override MODULE.bazel to use local score_docs_as_code.
        
        Args:
            repo_path: Path to the consumer repository
        """
        module_bazel_path = repo_path / "MODULE.bazel"
        
        if not module_bazel_path.exists():
            raise FileNotFoundError(f"MODULE.bazel not found in {repo_path}")
            
        # Read the current MODULE.bazel
        content = module_bazel_path.read_text()
        
        # Find the score_docs_as_code dependency line and add local_path_override
        lines = content.split('\n')
        modified_lines = []
        found_score_docs = False
        
        for line in lines:
            modified_lines.append(line)
            
            # Look for bazel_dep line with score_docs_as_code
            if 'bazel_dep' in line and 'score_docs_as_code' in line:
                found_score_docs = True
                # Add local_path_override after this line
                override_line = f'local_path_override(module_name = "score_docs_as_code", path = "{self.score_docs_as_code_path}")'
                modified_lines.append(override_line)
        
        if not found_score_docs:
            # If score_docs_as_code dependency not found, add it
            # Find a good place to insert (after module() declaration)
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith('module('):
                    # Find the closing parenthesis
                    depth = 0
                    for j in range(i, len(lines)):
                        if '(' in lines[j]:
                            depth += lines[j].count('(')
                        if ')' in lines[j]:
                            depth -= lines[j].count(')')
                        if depth == 0:
                            insert_idx = j + 1
                            break
                    break
            
            # Insert the dependency and override
            modified_lines.insert(insert_idx, "")
            modified_lines.insert(insert_idx + 1, 'bazel_dep(name = "score_docs_as_code", version = "0.0.0")')
            modified_lines.insert(insert_idx + 2, f'local_path_override(module_name = "score_docs_as_code", path = "{self.score_docs_as_code_path}")')
        
        # Write the modified content back
        modified_content = '\n'.join(modified_lines)
        module_bazel_path.write_text(modified_content)
        
        # Format the file to avoid formatting test failures
        try:
            subprocess.run(
                ["buildifier", str(module_bazel_path)],
                check=False,  # Don't fail if buildifier is not available
                capture_output=True
            )
        except FileNotFoundError:
            # buildifier not available, skip formatting
            pass
    
    def run_command(self, repo_path: Path, command: str, timeout: int = 300) -> TestResult:
        """
        Run a documentation command in a consumer repository.
        
        Args:
            repo_path: Path to the consumer repository
            command: Command to run (e.g., "docs_incremental_latest")
            timeout: Timeout in seconds
            
        Returns:
            TestResult with the outcome
        """
        # Use bazel run to execute the command
        full_command = ["bazel", "run", f"//docs:{command}"]
        
        try:
            result = subprocess.run(
                full_command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            error_message = None if success else f"Command failed with exit code {result.returncode}"
            
            return TestResult(
                consumer_name=repo_path.name,
                command=command,
                success=success,
                error_message=error_message,
                stdout=result.stdout,
                stderr=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                consumer_name=repo_path.name,
                command=command,
                success=False,
                error_message=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            return TestResult(
                consumer_name=repo_path.name,
                command=command,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def test_consumer(self, consumer: ConsumerConfig) -> List[TestResult]:
        """
        Test a single consumer.
        
        Args:
            consumer: Consumer configuration
            
        Returns:
            List of test results for each command
        """
        results = []
        
        try:
            # Clone the repository
            repo_path = self.clone_consumer(consumer)
            
            # Override MODULE.bazel
            self.override_module_bazel(repo_path)
            
            # Run each command
            for command in consumer.commands:
                # Check if the command target exists first
                check_cmd = ["bazel", "query", f"//docs:{command}"]
                check_result = subprocess.run(
                    check_cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                
                if check_result.returncode != 0:
                    # Command target doesn't exist, skip it
                    continue
                    
                result = self.run_command(repo_path, command, consumer.timeout)
                results.append(result)
                
        except Exception as e:
            # If consumer setup fails, create error results for all commands
            for command in consumer.commands:
                results.append(TestResult(
                    consumer_name=consumer.name,
                    command=command,
                    success=False,
                    error_message=f"Consumer setup failed: {str(e)}"
                ))
        
        return results
    
    def test_all_consumers(self, consumers: Optional[List[ConsumerConfig]] = None) -> List[TestResult]:
        """
        Test all configured consumers.
        
        Args:
            consumers: Optional list of consumers to test (uses default if None)
            
        Returns:
            List of all test results
        """
        if consumers is None:
            consumers = self.DEFAULT_CONSUMERS
            
        all_results = []
        
        for consumer in consumers:
            print(f"Testing consumer: {consumer.name}")
            results = self.test_consumer(consumer)
            all_results.extend(results)
            
        return all_results
    
    def generate_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """
        Generate a summary report of test results.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary containing the report
        """
        total_tests = len(results)
        failed_tests = [r for r in results if not r.success]
        passed_tests = [r for r in results if r.success]
        
        consumer_summary = {}
        for result in results:
            if result.consumer_name not in consumer_summary:
                consumer_summary[result.consumer_name] = {"passed": 0, "failed": 0, "errors": []}
                
            if result.success:
                consumer_summary[result.consumer_name]["passed"] += 1
            else:
                consumer_summary[result.consumer_name]["failed"] += 1
                consumer_summary[result.consumer_name]["errors"].append({
                    "command": result.command,
                    "error": result.error_message,
                    "stderr": result.stderr
                })
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "success_rate": len(passed_tests) / total_tests if total_tests > 0 else 0
            },
            "by_consumer": consumer_summary,
            "failed_tests": [
                {
                    "consumer": r.consumer_name,
                    "command": r.command, 
                    "error": r.error_message,
                    "stderr": r.stderr
                }
                for r in failed_tests
            ]
        }
    
    def print_report(self, results: List[TestResult]) -> None:
        """
        Print a human-readable report of test results.
        
        Args:
            results: List of test results
        """
        report = self.generate_report(results)
        
        print("\n" + "="*80)
        print("CONSUMER TEST RESULTS")
        print("="*80)
        
        summary = report["summary"]
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']:.1%}")
        
        print("\nBy Consumer:")
        print("-" * 40)
        for consumer, stats in report["by_consumer"].items():
            status = "✓" if stats["failed"] == 0 else "✗"
            print(f"{status} {consumer}: {stats['passed']} passed, {stats['failed']} failed")
        
        if report["failed_tests"]:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for failure in report["failed_tests"]:
                print(f"✗ {failure['consumer']}/{failure['command']}: {failure['error']}")
                if failure.get('stderr'):
                    # Print only the last few lines of stderr for brevity
                    stderr_lines = failure['stderr'].split('\n')
                    relevant_lines = [line for line in stderr_lines[-10:] if line.strip()]
                    if relevant_lines:
                        print(f"  Error details: {' | '.join(relevant_lines)}")
        
        print("\n" + "="*80)


def main():
    """Main entry point for running consumer tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run consumer tests for score_docs_as_code")
    parser.add_argument(
        "--score-docs-path",
        type=Path,
        default=Path.cwd(),
        help="Path to score_docs_as_code repository (default: current directory)"
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Working directory for cloning repos (default: temporary directory)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for JSON report"
    )
    parser.add_argument(
        "--consumer",
        action="append",
        help="Test only specific consumer(s). Can be repeated."
    )
    
    args = parser.parse_args()
    
    # Filter consumers if specified
    consumers = None
    if args.consumer:
        all_consumers = ConsumerTester.DEFAULT_CONSUMERS
        consumers = [c for c in all_consumers if c.name in args.consumer]
        if not consumers:
            print(f"Error: No consumers found matching: {args.consumer}")
            return 1
    
    with ConsumerTester(args.score_docs_path, args.work_dir) as tester:
        results = tester.test_all_consumers(consumers)
        
        # Print report
        tester.print_report(results)
        
        # Save JSON report if requested
        if args.output:
            report = tester.generate_report(results)
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to: {args.output}")
        
        # Exit with non-zero code if any tests failed
        failed_count = len([r for r in results if not r.success])
        return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    exit(main())