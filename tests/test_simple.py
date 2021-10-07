# -----------------------------------------------------------------------------
# Copyright 2016-2021 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin providing coverage support for enaml files.

"""
import pathlib

import coverage
import enaml
from enaml.core.parser import parse
from enaml.core.enaml_compiler import EnamlCompiler
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window

from plugin_test import EnamlPluginTestCase


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

    def load_module_main(self, module_name: str) -> Window:
        path = pathlib.Path(__file__).parent / "data" / module_name
        with open(path) as f:
            source = f.read()
        ast = parse(source, str(path))
        code = EnamlCompiler.compile(ast, str(path))
        globs = {}
        with enaml.imports():
            exec(code, globs)
        return globs["Main"]

    def test_plugin_loaded(self):
        self.cov = coverage.Coverage()
        self.cov.set_option("run:plugins", ["enaml_coverage_plugin"])
        import enaml_coverage_plugin

        proof = False

        def temp(reg, options):
            nonlocal proof
            proof = True

        old = enaml_coverage_plugin.coverage_init
        enaml_coverage_plugin.coverage_init = temp

        try:
            self.cov.start()
            self.cov.stop()
        finally:
            enaml_coverage_plugin.coverage_init = old

        assert proof

    def test_no_interaction(self):
        def create_and_show():
            Main = self.load_module_main("test_simple.enaml")
            w = Main()
            w.show()
            process_app_events()
            w.close()

        self.run_enaml_coverage(create_and_show)
        print(self.measured_files())
        ex, missed = self.get_analysis("tests/data/test_simple.enaml")
        executed = self.get_line_data("tests/data/test_simple.enaml")
        print("executable_lines: %s" % ex)
        print("missed lines: %s" % missed)
        print(
            "executed lines: %s" % self.get_line_data("tests/data/test_simple.enaml")
        )
        assert set(ex) == (set(missed) | set(executed))
        for l in (25, 31, 32, 34):  # FIXME 35 should be in but is not
            assert l in missed

    def test_with_interaction(self):
        def create_and_show():
            Main = self.load_module_main("test_simple.enaml")
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
        ex, missed = self.get_analysis("tests/data/test_simple.enaml")
        print("executable_lines: %s" % ex)
        print("missed lines: %s" % missed)
        print(
            "executed lines: %s" % self.get_line_data("tests/data/test_simple.enaml")
        )
        assert not missed
