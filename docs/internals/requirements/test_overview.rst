.. _testing_stats:

Testing Statistics
==================


.. needtable:: SUCCESSFUL TESTS
   :filter: result == "passed"
   :tags: TEST
   :columns: name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique;id as "link"

.. needtable:: FAILED TESTS
   :filter: result == "failed"
   :tags: TEST
   :columns: name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique;id as "link"


.. needtable:: SKIPPED/DISABLED TESTS
   :filter: result != "failed" and result != "passed"
   :tags: TEST
   :columns: name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique;id as "link"


.. needpie:: Requirements That Have A Linked Test
   :labels: requirement not implemeted, not tested, tested
   :colors: red,yellow, green
   :legend:

   type == 'tool_req' and implemented == 'NO'
   type == 'tool_req' and testlink == '' and (implemented == 'YES' or implemented == 'PARTIAL')
   type == 'tool_req' and testlink != '' and (implemented == 'YES' or implemented == 'PARTIAL')


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
