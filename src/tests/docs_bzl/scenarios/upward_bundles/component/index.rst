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

Component
=========

.. comp:: Seat heating controller
   :id: comp__seat_heating_controller
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__seat_heating
   :consists_of: comp__seat_heating_sensor

.. comp_req:: Controller temperature control
   :id: comp_req__component__temperature_control
   :version: 1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :derived_from: feat_req__module__seat_heating
   :satisfied_by: comp__seat_heating_controller

   The controller regulates the requested heating level.
