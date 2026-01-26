.. _statistics:

Implementation State Statistics
================================

Overview
--------

.. needpie:: Requirements Status
   :labels: not implemented, implemented but not tested, implemented and tested
   :colors: red,yellow, green

   type == 'tool_req' and implemented == 'NO'
   type == 'tool_req' and testlink == '' and (implemented == 'YES' or implemented == 'PARTIAL')
   type == 'tool_req' and testlink != '' and (implemented == 'YES' or implemented == 'PARTIAL')

In Detail
---------

.. grid:: 2
   :class-container: score-grid

   .. grid-item-card::

      .. needpie:: Requirements marked as Implemented
         :labels: not implemented, partial, implemented
         :colors: red, orange, green

         type == 'tool_req' and implemented == 'NO'
         type == 'tool_req' and implemented == 'PARTIAL'
         type == 'tool_req' and implemented == 'YES'

   .. grid-item-card::

      .. needpie:: Requirements with Codelinks
         :labels: no codelink, with codelink
         :colors: red, green

         type == 'tool_req' and source_code_link == ''
         type == 'tool_req' and source_code_link != ''

   .. grid-item-card::

      .. needpie:: Test Results
         :labels: passed, failed, skipped
         :colors: green, red, orange

         type == 'testcase' and result == 'passed'
         type == 'testcase' and result == 'failed'
         type == 'testcase' and result == 'skipped'

.. grid:: 2

   .. grid-item-card::

      Failed Tests

      *Hint: this table is empty by definition, as PRs with failing tests are not allowed to be merged in docs-as-code repo.*

      .. needtable:: FAILED TESTS
         :filter: result == "failed"
         :tags: TEST
         :columns: name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique;id as "link"

   .. grid-item-card::

      Skipped / Disabled Tests

      *Hint: this table is empty by definition, as we do not allow skipped or disabled tests in docs-as-code repo.*

      .. needtable:: SKIPPED/DISABLED TESTS
         :filter: result != "failed" and result != "passed"
         :tags: TEST
         :columns: name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique;id as "link"




All passed Tests
-----------------

.. needtable:: SUCCESSFUL TESTS
   :filter: result == "passed"
   :tags: TEST
   :columns: name as "testcase";result;fully_verifies;partially_verifies;test_type;derivation_technique;id as "link"


Details About Testcases
------------------------
*Data is not filled out yet within the test cases.*

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
