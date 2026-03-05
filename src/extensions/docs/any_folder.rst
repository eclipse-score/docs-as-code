Any Folder
==========

The extension ``score_any_folder`` allows documentation roots to stay in ``docs/``
while pulling in source files from anywhere else in the repository.

It does this by creating symlinks inside the Sphinx source directory (``confdir``) that point to the configured external directories.
Sphinx then discovers and buildsthose files as if they were part of ``docs/`` from the start.

The extension hooks into the ``builder-inited`` event,
which fires before Sphinx reads any documents.

Difference to Sphinx-Collections
--------------------------------

The extension `sphinx-collections <https://sphinx-collections.readthedocs.io/>`_
is very similar to this extension.
We use it for including external modules
as it allows conditional inclusion
and we need to switch between "normal" and "combo" builds.

The relevant difference is that this extension allows to include folders to anywhere
and is not restricted to a ``_collections/`` folder.
We consider this additional control over folder placement necessary.
