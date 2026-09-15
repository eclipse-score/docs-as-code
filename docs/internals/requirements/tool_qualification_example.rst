..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # See the NOTICE file(s) distributed with this work for additional
   # information regarding copyright ownership.
   #
   # This program and the accompanying materials are made available under the
   # terms of the Apache License 2.0 which is available at
   # https://www.apache.org/licenses/LICENSE-2.0
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

.. _tool_qualification_example:

Tool Qualification Report Example
==================================

This page demonstrates the machine-readable model used for a Docs-as-Code tool
qualification report. The content is based on the published
`S-CORE Doc-as-Code Tool Verification Report
<https://eclipse-score.github.io/score/main/score_tools/tools_documentation/doc_as_code.html#pr-review>`_.

The evaluation considers build and CI behavior, pull-request review, and
derived views. A malfunction is represented as a nested Need below the use case
where it occurs. Its ``safety_measure`` is intentionally free text. Generated
testcase Needs can link back to a malfunction through the existing verification
links.

.. doc_tool:: Docs-as-Code Tool Qualification
   :id: doc_tool__docs_as_code
   :status: evaluated
   :safety_affected: YES
   :security_affected: YES
   :tcl: LOW
   :tool_version: v7.0.1
   :realizes: wp__tool_verification_report[version==1]
   :version: 2
   :post_template: tool_qualification_report

   This report evaluates the Docs-as-Code toolchain as a qualified tool for
   producing and verifying safety-relevant documentation.

.. tool-usecase:: Build and CI behavior
   :id: tool_usecase__docs_as_code__build_ci
   :version: 1

   The repository contents are the source of truth and gated CI evaluates
   the generated documentation and traceability data.

   .. tool-malfunction:: Document metamodel enforcement
      :id: tool_malfunction__docs_as_code__metamodel
      :safety_affected: YES
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Repository contents are the source of truth and every change is reviewed by a committer.
      :violates: tool_req__docs_doc_types
      :version: 1

      A silent false negative can result from a permissive regular
      expression or a defect in a metamodel check.

   .. tool-malfunction:: Safety-critical linking enforcement
      :id: tool_malfunction__docs_as_code__safety_links
      :safety_affected: YES
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Pull-request review checks changes to safety-critical links before merge.
      :violates: tool_req__docs_common_attr_safety_link_check
      :version: 1

      A silent false negative could allow an unsafe derivation or other
      invalid safety-critical link to pass the build.

   .. tool-malfunction:: Requirements coverage statistics
      :id: tool_malfunction__docs_as_code__coverage
      :safety_affected: YES
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Coverage results are reviewed as part of the tool qualification evidence.
      :violates: tool_req__docs_test_linkage_metrics
      :version: 1

      A defect in the statistics calculation can produce an incorrect
      coverage result while leaving the build green.

   .. tool-malfunction:: Test linkage
      :id: tool_malfunction__docs_as_code__test_linkage
      :safety_affected: YES
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Test metadata and requirement links are reviewed when the test suite changes.
      :violates: tool_req__docs_test_link_testcase
      :version: 1

      The safety case may incorrectly conclude that a requirement is tested
      if a testcase link is missing or points to the wrong need.

   .. tool-malfunction:: Test reference check
      :id: tool_malfunction__docs_as_code__test_refs
      :safety_affected: YES
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Pull-request review checks that referenced requirements remain current.
      :violates: tool_req__docs_test_link_testcase
      :version: 1

      A missing or outdated requirement reference can invalidate the test
      evidence without causing a CI failure.

   .. tool-malfunction:: Listing assumptions of use
      :id: tool_malfunction__docs_as_code__aou_listing
      :safety_affected: YES
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Each change to an assumption of use is reviewed by a committer.
      :violates: tool_req__docs_req_link_covers_aou
      :version: 1

      A missing or incorrect assumption of use can lead to an incomplete
      safety argument.

.. tool-usecase:: Derived views
   :id: tool_usecase__docs_as_code__derived_views
   :version: 1

   Derived views are generated from the machine-readable Need model and are
   not the source of truth.

   .. tool-malfunction:: Architecture visualization
      :id: tool_malfunction__docs_as_code__arch_view
      :safety_affected: YES
      :detection_sufficient: YES
      :additional_safety_measure_required: NO
      :safety_measure: The generated architecture view is inspected during pull-request review.
      :violates: tool_req__docs_arch_views
      :version: 1

      An incorrect visualization can misrepresent the architecture. The
      result is detected by inspecting the derived view.

   .. tool-malfunction:: Backlinks
      :id: tool_malfunction__docs_as_code__backlinks
      :safety_affected: NO
      :detection_sufficient: NO
      :additional_safety_measure_required: YES
      :safety_measure: Backlinks are covered by the generated documentation checks.
      :violates: tool_req__docs_verification_report_need
      :version: 1

      A generated backlink can be missing or point to the wrong Need.

   .. tool-malfunction:: Documentation generation
      :id: tool_malfunction__docs_as_code__generation
      :safety_affected: NO
      :detection_sufficient: YES
      :additional_safety_measure_required: NO
      :safety_measure: The generated HTML is inspected as a derived view.
      :violates: tool_req__docs_doc_types
      :version: 1

      The generated HTML can be incomplete, outdated, or rendered
      incorrectly. The issue is detected by inspecting the derived view.
