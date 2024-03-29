# -----------------------------------------------------------------------------
# Copyright 2016-2021 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin providing coverage support for enaml files.

"""
from typing import Optional

from coverage import CoveragePlugin, FileTracer

from .reporter import EnamlFileReporter


class EnamlCoveragePlugin(CoveragePlugin):
    """Coverage plugin for enaml files."""

    def file_tracer(self, filename: str) -> Optional["EnamlFileTracer"]:
        """Create a file tracer for each discovered enaml file."""
        if filename.endswith(".enaml"):
            return EnamlFileTracer(filename)
        return None

    def file_reporter(self, filename: str) -> EnamlFileReporter:
        """Create a file reporter for a given filename."""
        return EnamlFileReporter(filename)


class EnamlFileTracer(FileTracer):
    """Tracer used to trace enaml file execution."""

    def __init__(self, filename: str) -> None:
        self._filename = filename

    def source_filename(self) -> str:
        """Return the filename passed as creation."""
        return self._filename
