Use Any Folder for Documentation
================================

Generally, your documentation must be ``docs/``,
but the RST files for a module may live closer to the code they describe,
for example in ``src/my_module/docs/``.
You can symlink the folders by adding to your ``conf.py``:

.. code-block:: python

   score_any_folder_mapping = {
       "../score/containers/docs": "component/containers",
   }

With this configuration, all files in ``score/containers/docs/`` become available at ``docs/component/containers/``.

If you have ``docs/component/overview.rst``, for example,
you can include the component documentation via ``toctree``:

.. code-block:: rst

   .. toctree::

      containers/index

Only relative links are allowed.

The symlinks will show up in your sources.
**Don't commit the symlinks to git!**
