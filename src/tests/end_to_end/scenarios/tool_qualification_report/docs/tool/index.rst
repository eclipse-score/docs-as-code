..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
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

Tool Qualification Report
=========================

.. doc_tool:: Example tool
   :id: doc_tool__example
   :status: evaluated
   :version: 1
   :tool_version: v1
   :security_affected: NO
   :post_template: tool_qualification_report

   Evaluates an example tool.

Use cases
---------

One malfunction needs qualification, the other cannot affect safety.

.. tool_usecase:: Prepare a release artifact
   :id: tool_usecase__tool__prepare
   :version: 1
   :belongs_to: doc_tool__example

   The tool prepares an artifact that is released without further checks.

   .. potential_tool_malfunction:: Wrong artifact content
      :id: potential_tool_malfunction__tool__content
      :version: 1
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: None
      :violates: tool_req__example_checked

.. tool_usecase:: Prepare an informative overview
   :id: tool_usecase__tool__overview
   :version: 1
   :belongs_to: doc_tool__example

   The tool prepares an overview that nobody relies on.

   .. potential_tool_malfunction:: Wrong overview
      :id: potential_tool_malfunction__tool__overview
      :version: 1
      :safety_affected: NO
      :violates: tool_req__example_informative

Tool requirements
-----------------

.. tool_req:: Checked capability
   :id: tool_req__example_checked
   :version: 1
   :satisfies: gd_req__tool_attr_uid[version==1]

   Violated by the malfunction that needs qualification.

.. tool_req:: Informative capability
   :id: tool_req__example_informative
   :version: 1
   :satisfies: gd_req__tool_attr_uid[version==1]

   Violated only by the malfunction that cannot affect safety.

.. tool_req:: Unreached capability
   :id: tool_req__example_unreached
   :version: 1
   :satisfies: gd_req__tool_attr_uid[version==1]

   Belongs to this module, but no malfunction of the report violates it.

Testcases
---------

Every result a verifying testcase can have, once each, and two passed ones.
An unexpected result is named, not counted as missing.

.. testcase:: Passed with design metadata
   :id: testcase__tool__passed_metadata
   :version: 1
   :result: passed
   :fully_verifies: tool_req__example_checked
   :test_type: interface-test
   :derivation_technique: boundary-values

.. testcase:: Passed partially
   :id: testcase__tool__passed_partially
   :version: 1
   :result: passed
   :partially_verifies: tool_req__example_checked

.. testcase:: Failed
   :id: testcase__tool__failed
   :version: 1
   :result: failed
   :fully_verifies: tool_req__example_checked

.. testcase:: Skipped
   :id: testcase__tool__skipped
   :version: 1
   :result: skipped
   :fully_verifies: tool_req__example_checked

.. testcase:: Disabled
   :id: testcase__tool__disabled
   :version: 1
   :result: disabled
   :fully_verifies: tool_req__example_checked

.. testcase:: Errored
   :id: testcase__tool__errored
   :version: 1
   :result: error
   :fully_verifies: tool_req__example_checked

.. testcase:: Without result
   :id: testcase__tool__without_result
   :version: 1
   :fully_verifies: tool_req__example_checked

Testcases the qualification does not need:

.. testcase:: Verifies the informative capability
   :id: testcase__tool__informative
   :version: 1
   :result: failed
   :fully_verifies: tool_req__example_informative

.. testcase:: Verifies the unreached capability
   :id: testcase__tool__unreached
   :version: 1
   :result: passed
   :fully_verifies: tool_req__example_unreached

.. testcase:: Verifies nothing
   :id: testcase__tool__unlinked
   :version: 1
   :result: passed

Imported Needs
--------------

An imported tool requirement without a module belongs to the module of its
inventory, not to the module of this page.

.. needimport:: imported_needs.json
