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
   # Assisted-by: Anthropic Claude-opus-4.6
   # *******************************************************************************

.. _metamodel_reference:

Metamodel Schema Reference
==========================

The S-CORE documentation metamodel is defined in a YAML file.
It declares all Sphinx-Needs types (directives), their mandatory and optional options,
link relationships, and validation rules used across S-CORE documentation repositories.

For details on the extension internals, validation checks, and how to add new need
types, see the :doc:`score_metamodel extension guide </internals/extensions/metamodel>`.

Schema
------

Below is the JSON Schema that validates the structure of ``metamodel.yaml``.

.. jsonschema:: ../../src/extensions/score_metamodel/metamodel-schema.json

Quick example
-------------

A minimal type definition in ``metamodel.yaml`` looks like this:

.. code-block:: yaml

   needs_types:
     feat_req:
       title: Feature Requirement
       prefix: feat_req__
       mandatory_options:
         id: ^feat_req__[0-9a-z_]*$
         status: ^(valid|draft)$
       optional_links:
         satisfies: ^std_req__.*$
       tags:
         - requirement
       parts: 2

Each option value is a regex pattern that the corresponding field must match.
The ``parts`` key specifies how many segments (separated by ``__``) the need ID contains.
