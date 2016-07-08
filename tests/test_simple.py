# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin providing coverage support for enaml files.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml
from enaml.qt.qt_application import QtApplication

from .plugin_test import EnamlPluginTestCase


def process_app_events():
    """Manually run the Qt event loop so that windows are shown and event
    propagated.

    """
    qapp = QtApplication.instance()._qapp
    qapp.flush()
    qapp.processEvents()
    qapp.sendPostedEvents()


# TODO understand why we lose the last line on first read,
# TODO clean module after test so that we truly import it each time
# TODO find a way to access the main object config.
class TestSimpleEnaml(EnamlPluginTestCase):

    def test_no_interaction(self):

        def create_and_show():
            with enaml.imports():
                from .enaml.test_simple import Main
                w = Main()
                w.show()
                process_app_events()
                w.close()

        self.run_enaml_coverage(create_and_show)
        print(self.measured_files())
        ex, missed = self.get_analysis('tests/enaml/test_simple.enaml')
        print('executable_lines: %s' % ex)
        print('missed lines: %s' % missed)
        print('executed lines: %s' %
              self.get_line_data('tests/enaml/test_simple.enaml'))
        assert False

    def test_with_interaction(self):

        def create_and_show():
            with enaml.imports():
                from .enaml.test_simple import Main
                w = Main()
                w.show()
                process_app_events()
                btn = w.central_widget().widgets()[-1]
                btn.clicked = True
                w.should_answer = False
                btn.clicked = True
                w.close()

        self.run_enaml_coverage(create_and_show)
        print(self.measured_files())
        ex, missed = self.get_analysis('tests/enaml/test_simple.enaml')
        print('executable_lines: %s' % ex)
        print('missed lines: %s' % missed)
        print('executed lines: %s' %
              self.get_line_data('tests/enaml/test_simple.enaml'))
        assert False
