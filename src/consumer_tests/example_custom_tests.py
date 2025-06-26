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
Example script showing how to extend consumer tests for custom consumers.

This demonstrates how to:
1. Create custom consumer configurations
2. Test additional repositories
3. Run custom test scenarios
"""

from pathlib import Path

from consumer_tester import ConsumerConfig, ConsumerTester


def test_custom_consumer():
    """Example of testing a custom consumer repository."""
    
    # Define a custom consumer configuration
    custom_consumer = ConsumerConfig(
        name="my_custom_repo",
        repo_url="https://github.com/my-org/my-repo.git",
        commands=[
            "docs_incremental_latest",
            "docs_custom_command",
        ],
        branch="develop",  # Test against develop branch
        timeout=600        # Longer timeout for complex builds
    )
    
    # Run the test
    score_docs_path = Path.cwd()  # Assume running from score_docs_as_code root
    
    with ConsumerTester(score_docs_path) as tester:
        print(f"Testing custom consumer: {custom_consumer.name}")
        
        results = tester.test_consumer(custom_consumer)
        
        # Generate and print report
        tester.print_report(results)
        
        # Check if any tests failed
        failed_results = [r for r in results if not r.success]
        if failed_results:
            print(f"\n❌ {len(failed_results)} tests failed!")
            return False
        else:
            print(f"\n✅ All {len(results)} tests passed!")
            return True


def test_multiple_custom_consumers():
    """Example of testing multiple custom consumers."""
    
    custom_consumers = [
        ConsumerConfig(
            name="repo_a",
            repo_url="https://github.com/org/repo-a.git",
            commands=["docs_incremental_latest"]
        ),
        ConsumerConfig(
            name="repo_b", 
            repo_url="https://github.com/org/repo-b.git",
            commands=["docs_incremental_latest", "docs_docs_latest"]
        ),
    ]
    
    score_docs_path = Path.cwd()
    
    with ConsumerTester(score_docs_path) as tester:
        all_results = []
        
        for consumer in custom_consumers:
            print(f"\nTesting consumer: {consumer.name}")
            results = tester.test_consumer(consumer)
            all_results.extend(results)
        
        # Generate combined report
        print("\n" + "="*80)
        print("COMBINED TEST RESULTS")
        print("="*80)
        tester.print_report(all_results)
        
        # Save detailed report
        report = tester.generate_report(all_results)
        import json
        with open("custom_consumer_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: custom_consumer_report.json")


def test_filtered_commands():
    """Example of testing only specific commands."""
    
    # Create a consumer config with only specific commands
    filtered_consumer = ConsumerConfig(
        name="platform",
        repo_url="https://github.com/eclipse-score/score.git",
        commands=[
            "docs_incremental_latest",  # Only test the most important command
        ]
    )
    
    score_docs_path = Path.cwd()
    
    with ConsumerTester(score_docs_path) as tester:
        print("Testing only critical commands...")
        
        results = tester.test_consumer(filtered_consumer)
        tester.print_report(results)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run custom consumer tests")
    parser.add_argument("--test", choices=["single", "multiple", "filtered"],
                        default="single", help="Which test to run")
    
    args = parser.parse_args()
    
    if args.test == "single":
        print("Running single custom consumer test...")
        success = test_custom_consumer()
    elif args.test == "multiple":
        print("Running multiple custom consumers test...")
        test_multiple_custom_consumers()
        success = True
    elif args.test == "filtered":
        print("Running filtered commands test...")
        test_filtered_commands()
        success = True
    
    exit(0 if success else 1)