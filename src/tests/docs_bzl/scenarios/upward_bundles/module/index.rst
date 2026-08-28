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

Module
======

The module-level feature requirement is reviewed against
:need:`feat_req__platform__seat_heating` from the platform bundle.

.. feat:: Seat heating
   :id: feat__seat_heating
   :version: 1
   :security: NO
   :safety: QM
   :status: valid

.. feat_req:: Seat heating availability
   :id: feat_req__module__seat_heating
   :version: 1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__seat_heating

   The seat heating feature is available to the vehicle user.

.. mod:: Seat heating module
   :id: mod__seat_heating_module
   :version: 1
   :includes: comp__seat_heating_controller
