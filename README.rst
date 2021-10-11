Enaml coverage plugin
=====================

.. image:: https://github.com/MatthieuDartiailh/enaml_coverage_plugin/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/MatthieuDartiailh/enaml_coverage_plugin/actions/workflows/ci.yml

Coverage to plugin to provide coverage reports for Enaml files (.enaml).

Usage
-----

To enable the plugin, one simply needs to add the following snippet under the
``run``  section of a project coverage configuration file:

.. code::

    plugins =
        enaml_coverage_plugin

.. note::

    Branch coverage is always on so in order to be able to combine reports, branch
    coverage need to be enabled for Python files. The can be done by specifying
    ``branch=True`` under the ``run`` section of your coverage configuration.
