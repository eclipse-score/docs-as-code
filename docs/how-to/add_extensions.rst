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
