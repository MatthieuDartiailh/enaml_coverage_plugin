# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016-2021 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin providing coverage support for enaml files.

"""


def coverage_init(reg, options):
    """Register the enaml plugin."""
    from .plugin import EnamlCoveragePlugin

    reg.add_file_tracer(EnamlCoveragePlugin())
