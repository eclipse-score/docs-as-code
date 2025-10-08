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
#CHECK: check_validity_consistency


#EXPECT: feat_req__random_id1: inconsistent validity: valid_from (v1.0) >= valid_until (v0.5).

.. feat_req:: from after until
   :id: feat_req__random_id1
   :valid_from: v1.0
   :valid_until: v0.5


#EXPECT-NOT: feat_req__random_id2: inconsistent validity: valid_from (v0.5) >= valid_until (v1.0).

.. feat_req:: until after from
   :id: feat_req__random_id2
   :valid_from: v0.5
   :valid_until: v1.0


#EXPECT: stkh_req__random_id1: inconsistent validity: valid_from (v1.0.1) >= valid_until (v0.5).

.. stkh_req:: from after until for stakeholder requirement
   :id: stkh_req__random_id1
   :valid_from: v1.0.1
   :valid_until: v0.5
