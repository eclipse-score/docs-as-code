.. _testing_stats:

TESTING STATISTICS
==================


.. needtable:: SUCCESSFUL TEST
   :filter: result == "passed"
   :tags: TEST
   :columns: external_url as "source_link"; name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique


.. needtable:: FAILED TEST
   :filter: result == "failed"
   :tags: TEST
   :columns: external_url as "source_link"; name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique


.. needtable:: OTHER TEST
   :filter: result != "failed" and result != "passed"
   :tags: TEST
   :columns: external_url as "source_link"; name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique


.. needpie:: Test Results
   :labels: passed, failed, skipped
   :colors: green, red, orange
   :legend:

   type == 'testcase' and result == 'passed'
   type == 'testcase' and result == 'failed'
   type == 'testcase' and result == 'skipped'


.. needpie:: Test Types Used In Testcases
   :labels: fault-injection, interface-test, requirements-based, resource-usage
   :legend:

   type == 'testcase' and test_type == 'fault-injection'
   type == 'testcase' and test_type == 'interface-test'
   type == 'testcase' and test_type == 'requirements-based'
   type == 'testcase' and test_type == 'resource-usage'


.. needpie:: Derivation Techniques Used In Testcases
   :labels: requirements-analysis, design-analysis, boundary-values, equivalence-classes, fuzz-testing, error-guessing, explorative-testing
   :legend:

   type == 'testcase' and derivation_technique == 'requirements-analysis'
   type == 'testcase' and derivation_technique == 'design-analysis'
   type == 'testcase' and derivation_technique == 'boundary-values'
   type == 'testcase' and derivation_technique == 'equivalence-classes'
   type == 'testcase' and derivation_technique == 'fuzz-testing'
   type == 'testcase' and derivation_technique == 'error-guessing'
   type == 'testcase' and derivation_technique == 'explorative-testing'
