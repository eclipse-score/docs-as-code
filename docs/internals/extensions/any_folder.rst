Any Folder
==========

The extension ``score_any_folder`` allows documentation roots to stay in ``docs/``
while pulling in source files from anywhere else in the repository.

It does this by creating symlinks inside the Sphinx source directory (``confdir``) that point to the configured external directories.
Sphinx then discovers and buildsthose files as if they were part of ``docs/`` from the start.

The extension hooks into the ``builder-inited`` event,
which fires before Sphinx reads any documents.
