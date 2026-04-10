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

Add Extensions
===================

The docs-as-code module defines its own Python environment in ``MODULE.bazel``
and as a user you cannot extend that.
If you want to add Sphinx extensions,
you must duplicate the Python environment first.

Once you have your own Python environment,
supply all necessary packages to ``docs`` via the ``deps`` attribute.

.. code-block:: starlark
   :caption: In your BUILD file

    load("@your_python_env//:requirements.bzl", "all_requirements")

    docs(
        # ...other attributes...
        deps = all_requirements
    )

Inside ``docs()``, the docs-as-code module will check if you have supplied all necessary dependencies.

How to Create a Python Environment?
-----------------------------------

The general documentation is `in the rules_python documentation <https://rules-python.readthedocs.io/en/latest/toolchains.html>`_.

You can also peek into `this docs-as-code repo's MODULE.bazel file <https://github.com/eclipse-score/docs-as-code/blob/main/MODULE.bazel>`_
how ``docs_as_code_hub_env`` is defined and use it as a template for ``your_python_env``.

Recommendation:
Use `compile_pip_requirements <https://rules-python.readthedocs.io/en/latest/api/rules_python/python/pip.html#compile_pip_requirements>`_
because it is a solid practice anyways.
Next, get ``@score_docs_as_code//src:requirements.in`` as one of the inputs
to ensure you have all the necessary dependencies for docs-as-code.

.. code-block:: starlark
   :caption: Example BUILD file snippet

    load("@rules_python//python:pip.bzl", "compile_pip_requirements")

    compile_pip_requirements(
        name = "requirements",
        srcs = [
            "@score_docs_as_code//src:requirements.in",
            "requirements.in",
        ],
        requirements_txt = "requirements_lock.txt",
        visibility = ["//visibility:public"],
    )
