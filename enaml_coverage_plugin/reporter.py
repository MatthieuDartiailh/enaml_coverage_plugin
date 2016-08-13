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

import os.path
import types

from coverage import files
from coverage.misc import (contract, CoverageException, expensive,
                           join_regex, isolate_module)
from coverage.plugin import FileReporter
from coverage.python import get_python_source

from .parser import EnamlParser

os = isolate_module(os)


class EnamlFileReporter(FileReporter):
    """Enaml file reporter.

    """

    def __init__(self, morf):
#        self.coverage = coverage

        if hasattr(morf, '__file__'):
            filename = morf.__file__
        elif isinstance(morf, types.ModuleType):
            # A module should have had .__file__, otherwise we can't use it.
            # This could be a PEP-420 namespace package.
            raise CoverageException("Module {0} has no file".format(morf))
        else:
            filename = morf

        filename = files.unicode_filename(filename)

        super(EnamlFileReporter,
              self).__init__(files.canonical_filename(filename))

        if hasattr(morf, '__name__'):
            name = morf.__name__
            name = name.replace(".", os.sep) + ".enaml"
            name = files.unicode_filename(name)
        else:
            name = files.relative_filename(filename)
        self.relname = name

        self._source = None
        self._parser = None
        self._statements = None
        self._excluded = None

    @contract(returns='unicode')
    def relative_filename(self):
        return self.relname

    @property
    def parser(self):
        """Lazily create a :class:`PythonParser`."""
        if self._parser is None:
            with open(self.filename, 'rU') as src_file:
                src = src_file.read()
            self._parser = EnamlParser(
                text=src,
                filename=self.filename,
#                exclude=self.coverage._exclude_regex('exclude'),
            )
            self._parser.parse_source()
        return self._parser

    def lines(self):
        """Return the line numbers of statements in the file."""
        return self.parser.statements

    def excluded_lines(self):
        """Return the line numbers of statements in the file."""
        return self.parser.excluded

    def translate_lines(self, lines):
        return self.parser.translate_lines(lines)

    def translate_arcs(self, arcs):
        return self.parser.translate_arcs(arcs)

    @expensive
    def no_branch_lines(self):
        no_branch = self.parser.lines_matching(
#            join_regex(self.coverage.config.partial_list),
#            join_regex(self.coverage.config.partial_always_list)
            )
        return no_branch

    @expensive
    def arcs(self):
        return self.parser.arcs()

    @expensive
    def exit_counts(self):
        return self.parser.exit_counts()

    def missing_arc_description(self, start, end, executed_arcs=None):
        return self.parser.missing_arc_description(start, end, executed_arcs)

    @contract(returns='unicode')
    def source(self):
        if self._source is None:
            self._source = get_python_source(self.filename)
        return self._source
