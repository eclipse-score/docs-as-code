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

Subcomponent
============

.. comp:: Seat heating sensor
   :id: comp__seat_heating_sensor
   :version: 1
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__seat_heating

.. comp_req:: Sensor temperature measurement
   :id: comp_req__subcomponent__temp_measure
   :version: 1
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :derived_from: feat_req__module__seat_heating
   :satisfied_by: comp__seat_heating_sensor

   The sensor reports the measured seat temperature.
