# -----------------------------------------------------------------------------
# Copyright 2016-2021 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin providing coverage support for enaml files.

"""
import os.path
import types
from typing import Set, Tuple

from coverage import files
from coverage.misc import CoverageException, isolate_module
from coverage.plugin import FileReporter
from coverage.python import get_python_source

from .parser import EnamlParser

os = isolate_module(os)


class EnamlFileReporter(FileReporter):
    """Enaml file reporter."""

    def __init__(self, morf):
        if hasattr(morf, "__file__"):
            filename = morf.__file__
        elif isinstance(morf, types.ModuleType):
            # A module should have had .__file__, otherwise we can't use it.
            # This could be a PEP-420 namespace package.
            raise CoverageException("Module {0} has no file".format(morf))
        else:
            filename = morf

        super(EnamlFileReporter, self).__init__(files.canonical_filename(filename))

        if hasattr(morf, "__name__"):
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

    def relative_filename(self) -> str:
        return self.relname

    @property
    def parser(self) -> EnamlParser:
        """Lazily create a parser."""
        if self._parser is None:
            with open(self.filename, "r") as src_file:
                src = src_file.read()
            self._parser = EnamlParser(
                text=src,
                filename=self.filename,
                #                exclude=self.coverage._exclude_regex('exclude'),
            )
            self._parser.parse_source()
        return self._parser

    def lines(self) -> Set[int]:
        """Get the executable lines in this file.

        Your plug-in must determine which lines in the file were possibly
        executable.  This method returns a set of those line numbers.

        Returns a set of line numbers.

        """
        return self.parser.statements

    def excluded_lines(self) -> Set[int]:
        """Get the excluded executable lines in this file.

        Your plug-in can use any method it likes to allow the user to exclude
        executable lines from consideration.

        Returns a set of line numbers.

        The base implementation returns the empty set.

        """
        return self.parser.excluded

    def translate_lines(self, lines: Set[int]) -> Set[int]:
        """Translate recorded lines into reported lines."""
        return self.parser.translate_lines(lines)

    def translate_arcs(self, arcs: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Translate recorded arcs into reported arcs.

        Similar to :meth:`translate_lines`, but for arcs.  `arcs` is a set of
        line number pairs.

        """
        return self.parser.translate_arcs(arcs)

    def no_branch_lines(self) -> Set[int]:
        """Get the lines excused from branch coverage in this file."""
        no_branch = self.parser.lines_matching()
        return no_branch

    def arcs(self) -> Set[Tuple[int, int]]:
        return self.parser.arcs()

    def exit_counts(self) -> Set[Tuple[int, int]]:
        """Get a count of exits from that each line."""
        return self.parser.exit_counts()

    def missing_arc_description(
        self, start: int, end: int, executed_arcs: Set[Tuple[int, int]] = None
    ) -> str:
        """Provide an English sentence describing a missing arc."""
        return self.parser.missing_arc_description(start, end, executed_arcs)

    def source(self) -> str:
        if self._source is None:
            self._source = get_python_source(self.filename)
        return self._source
