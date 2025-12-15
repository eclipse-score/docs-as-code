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


.. Title contains a stop word
#EXPECT: feat_req__test__title_bad: contains a weak word: `must` in option: `title`. Please revise the wording.

.. feat_req:: This must work
   :id: feat_req__test__title_bad



.. Title contains no stop word
#EXPECT-NOT: feat_req__test__title_good: contains a weak word: `must` in option: `title`. Please revise the wording.

.. feat_req:: This is a test
   :id: feat_req__test__title_good



.. Title of an architecture element contains a stop word
#EXPECT: stkh_req__test_title_bad: contains a weak word: `must` in option: `title`. Please revise the wording.

.. stkh_req:: This must work
   :id: stkh_req__test_title_bad



#EXPECT-NOT: stkh_req__test_title_good: contains a weak word: `must` in option: `title`. Please revise the wording.

.. stkh_req:: This is a test
   :id: stkh_req__test_title_good




.. Description contains a weak word
#EXPECT: stkh_req__test__desc_bad: contains a weak word: `really` in option: `content`. Please revise the wording.

.. stkh_req:: This is a test
   :id: stkh_req__test__desc_bad

   This should really work



.. Description contains no weak word
#EXPECT-NOT: stkh_req__test__desc_good: contains a weak word: `really` in option: `content`. Please revise the wording.

.. stkh_req:: This is a test
   :id: stkh_req__test__desc_good

   This should work



.. Description of architecture view of type feat_arc_sta is not checked for weak words
#EXPECT-NOT: feat_arc_sta_desc_good: contains a weak word: `really` in option: `content`. Please revise the wording.

.. feat_arc_sta:: This is a test
   :id: feat_arc_sta_desc_good

   This should really work


#EXPECT: tool_req__docs_common_attr_desc_wording: contains a weak word: `just` in option: `content`. Please revise the wording.

.. tool_req:: Enforces description wording rules
  :id: tool_req__docs_common_attr_desc_wording
  :tags: Common Attributes
  :implemented: YES
  :satisfies:
    gd_req__req_desc_weak,
  :parent_covered: YES

  Docs-as-Code shall enforce that requirement descriptions do not contain the following weak words:
  just, about, really, some, thing, absolut-ely

  This rule applies to:

  * all requirement types defined in :need:`tool_req__docs_req_types`, except process requirements.
