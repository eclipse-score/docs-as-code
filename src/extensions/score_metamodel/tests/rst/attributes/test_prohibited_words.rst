..
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
#CHECK: check_for_prohibited_words


.. test_metadata:: Test Prohibeted Words
   :id: test_metadata__check_prohibeted_words
   :partially_verifies_list: tool_req__docs_common_attr_title, tool_req__docs_common_attr_desc_wording
   :test_type: requirements_based
   :derivation_technique: requirements_based
   :check: check_for_prohibited_words
   
   Tests if that the check of titles and descriptions for have probhieted words works as intended



.. Title contains a stop word
#EXPECT[+2]: feat_req__test__title_bad: contains a weak word: `must` in option: `title`. Please revise the wording.

.. feat_req:: This must work
   :id: feat_req__test__title_bad
   :expect: feat_req__test__title_bad: contains a weak word: `must` in option: `title`. Please revise the wording.



.. Title contains no stop word

.. feat_req:: This is a test
   :id: feat_req__test__title_good
   :expect_not: title contains



.. Title of an architecture element contains a stop word

.. stkh_req:: This must work
   :id: stkh_req__test__title_bad
   :expect: stkh_req__test__title_bad: contains a weak word: `must` in option: `title`. Please revise the wording.




.. stkh_req:: This is a test
   :id: stkh_req__test__title_good
   :expect_not: title contains




.. Description contains a weak word

.. stkh_req:: This is a test
   :id: stkh_req__test__desc_bad
   :expect: stkh_req__test__desc_bad: contains a weak word: `really` in option: `content`. Please revise the wording.

   This should really work



.. Description contains no weak word

.. stkh_req:: This is a test
   :id: stkh_req__test__desc_good
   :expect_not: contains a weak word

   This should work



.. Description of architecture view of type feat_arc_sta is not checked for weak words

.. feat_arc_sta:: This is a test
   :id: feat_arc_sta__desc_good
   :expect-not: content

   This should really work



.. tool_req:: Enforces description wording rules
  :id: tool_req__docs_common_attr_desc_wording
  :tags: Common Attributes
  :implemented: YES
  :satisfies:
    gd_req__req_desc_weak,
  :parent_covered: YES
  :expect: tool_req__docs_common_attr_desc_wording: contains a weak word: `just` in option: `content`. Please revise the wording.

  Docs-as-Code shall enforce that requirement descriptions do not contain the following weak words:
  just, about, really, some, thing, absolut-ely

  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process requirements.
