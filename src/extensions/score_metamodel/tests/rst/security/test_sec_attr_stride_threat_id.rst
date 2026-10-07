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

.. test_metadata::
   :id: test_metadata__sec_attr_stride_threat_id
   :fully_verifies_list: tool_req__docs_sec_attr_stride_threat_id[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that STRIDE threat needs (feat_sec_threat, comp_sec_threat,
   plat_sec_threat) have a mandatory threat_id attribute which must match the
   STRIDE identifier pattern.  Each type is checked with:
   - a valid threat_id, expecting no warning
   - a missing threat_id, expecting the mandatory-attribute warning
   - a threat_id that does not follow the STRIDE pattern, expecting a pattern
     warning


.. feat_sec_threat:: Valid threat id
   :id: feat_sec_threat__tid__good_001
   :version: 1
   :threat_id: AU_01_01
   :status: valid
   :expect_not: is missing required attribute: `threat_id`

   Valid feature STRIDE threat with a proper threat id.


.. feat_sec_threat:: Missing threat id
   :id: feat_sec_threat__tid__missing_001
   :version: 1
   :status: valid
   :expect: is missing required attribute: `threat_id`

   Feature STRIDE threat without a threat id.


.. feat_sec_threat:: Invalid threat id pattern
   :id: feat_sec_threat__tid__bad_001
   :version: 1
   :threat_id: XX_99_99
   :status: valid
   :expect: does not follow pattern

   Feature STRIDE threat whose threat id is not a valid STRIDE identifier.


.. comp_sec_threat:: Valid threat id
   :id: comp_sec_threat__tid__good_001
   :version: 1
   :threat_id: CT_01_01
   :status: valid
   :expect_not: is missing required attribute: `threat_id`

   Valid component STRIDE threat with a proper threat id.


.. comp_sec_threat:: Missing threat id
   :id: comp_sec_threat__tid__missing_001
   :version: 1
   :status: valid
   :expect: is missing required attribute: `threat_id`

   Component STRIDE threat without a threat id.


.. comp_sec_threat:: Invalid threat id pattern
   :id: comp_sec_threat__tid__bad_001
   :version: 1
   :threat_id: AU_01_09
   :status: valid
   :expect: does not follow pattern

   Component STRIDE threat whose threat id is out of the valid STRIDE range.


.. plat_sec_threat:: Valid threat id
   :id: plat_sec_threat__tid__good_001
   :version: 1
   :threat_id: MT_01_07
   :status: valid
   :expect_not: is missing required attribute: `threat_id`

   Valid platform STRIDE threat with a proper threat id.


.. plat_sec_threat:: Missing threat id
   :id: plat_sec_threat__tid__missing_001
   :version: 1
   :status: valid
   :expect: is missing required attribute: `threat_id`

   Platform STRIDE threat without a threat id.


.. plat_sec_threat:: Invalid threat id pattern
   :id: plat_sec_threat__tid__bad_001
   :version: 1
   :threat_id: MT_99_01
   :status: valid
   :expect: does not follow pattern

   Platform STRIDE threat whose threat id is not a valid STRIDE identifier.
