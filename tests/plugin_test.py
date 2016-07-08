# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tools for testing th eplugin providing coverage measurement for enaml files.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import contextlib
import os
import os.path

from unittest import TestCase

#from unittest_mixins import StdStreamCapturingMixin

import coverage

from enaml.application import Application

from enaml_coverage_plugin.plugin import EnamlCoveragePlugin


class EnamlPluginTestCase(TestCase):
    """A base class for all our tests."""

    def setUp(self):
        super(EnamlPluginTestCase, self).setUp()
        if Application.instance() is None:
            from enaml.qt.qt_application import QtApplication
            self.app = QtApplication()

    def run_enaml_coverage(self, enaml_exec, options=None):
        """Run an enaml file under coverage.

       enaml_exec is a callable taking no argument and running some test on an
       enaml file.

        If `options` is provided, they are kwargs for the Coverage
        constructor, which default to source=["."].

        Returns:
            str: the text produced by the template.

        """
        if options is None:
            options = {'source': ["."], 'branch': True}

        self.cov = coverage.Coverage(**options)
        self.append_config("run:plugins", "enaml_coverage_plugin")
        if 0:
            self.append_config("run:debug", "trace")
        self.cov.start()
        enaml_exec()
        self.cov.stop()
        self.cov.save()
        # Warning! Accessing secret internals!
        for pl in self.cov.plugins:
            if isinstance(pl, EnamlCoveragePlugin):
                if not pl._coverage_enabled:
                    raise PluginDisabled()

    def append_config(self, option, value):
        """Append to a configuration option."""
        val = self.cov.config.get_option(option)
        val.append(value)
        self.cov.config.set_option(option, val)

    def get_line_data(self, path):
        """Get the executed-line data for a template.

        Returns:
            list: the line numbers of lines executed in the template.

        """
        return self.cov.data.lines(os.path.realpath(path))

    def get_analysis(self, path):
        """Get the coverage analysis for an enaml file.

        Returns:
            list, list: the line numbers of executable lines, and the line
                numbers of missed lines.

        """
        analysis = self.cov.analysis2(os.path.abspath(path))
        _, executable, _, missing, _ = analysis
        return executable, missing

    def measured_files(self):
        """Get the list of measured files, in relative form."""
        return [os.path.relpath(f) for f in self.cov.data.measured_files()]

    def assert_analysis(self, executable, missing=None, name=None):
        """Assert that the analysis for `name` is right."""
        actual_executable, actual_missing = self.get_analysis(name)
        self.assertEqual(
            executable,
            actual_executable,
            "Executable lines aren't as expected: %r != %r" % (
                executable, actual_executable,
            ),
        )
        self.assertEqual(
            missing or [],
            actual_missing,
            "Missing lines aren't as expected: %r != %r" % (
                missing, actual_missing,
            ),
        )

    def get_html_report(self, path):
        """Get the html report for a template.

        Returns:
            float: the total percentage covered.

        """
        html_coverage = self.cov.html_report(os.path.abspath(path))
        return html_coverage

    def get_xml_report(self, name=None):
        """Get the xml report for a template.

        Returns:
            float: the total percentage covered.

        """
        path = self._path(name)
        xml_coverage = self.cov.xml_report(os.path.abspath(path))
        return xml_coverage

    @contextlib.contextmanager
    def assert_plugin_disabled(self, msg):
        """Assert that our plugin was disabled during an operation."""
        # self.run_django_coverage will raise PluginDisabled if the plugin
        # was disabled.
        with self.assertRaises(PluginDisabled):
            yield
        stderr = self.stderr()
        self.assertIn(
            "Coverage.py warning: "
            "Disabling plugin 'enaml_coverage_plugin.EnamlCoveragePlugin' "
            "due to an exception:",
            stderr
        )
        self.assertIn(
            "EnamlCoveragePluginException: " + msg,
            stderr
        )


class PluginDisabled(Exception):
    """Raised if we find that our plugin has been disabled."""
    pass
