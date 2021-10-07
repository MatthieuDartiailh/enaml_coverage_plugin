# -----------------------------------------------------------------------------
# Copyright 2016-2021 by Enaml coverage Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin providing coverage support for enaml files.

"""
import collections
import os
import sys
import types
from typing import Optional

from atom.api import Typed
from coverage.misc import NotPython, contract, nice_pair
from coverage.parser import AstArcAnalyzer, ByteParser, PythonParser
from coverage.phystokens import neuter_encoding_declaration
from enaml.core.enaml_ast import ASTVisitor, PythonModule
from enaml.core.enaml_compiler import EnamlCompiler
from enaml.core.parser import parse

if sys.version_info >= (3, 7):
    from enaml.core.parser.lexer3 import Python37EnamlLexer
    lexer = Python37EnamlLexer()
else:
    raise Exception('Unsupported Python version')


class NotEnaml(NotPython):
    """Exception raised when parsing fails on enaml file.

    """
    pass


class EnamlByteParser(ByteParser):
    """Byte parser modified for handling enaml files.

    """
    def __init__(self, text: str, code: Optional[types.CodeType]=None, filename: Optional[str]=None) -> None:
        self.text = text
        if code:
            self.code = code
        else:
            try:
                self.code = EnamlCompiler.compile(parse(text), filename)
            except SyntaxError as synerr:
                raise NotPython(
                    u"Couldn't parse '%s' as Enaml source: '%s' at line %d" % (
                        filename, synerr.msg, synerr.lineno
                    )
                )


class EnamlParser(PythonParser):
    """Enaml parser analyser based on a custom arc analysis.

    """

    @property
    def byte_parser(self) -> EnamlByteParser:
        """Create a ByteParser on demand."""
        if not self._byte_parser:
            self._byte_parser = EnamlByteParser(self.text,
                                                filename=self.filename)
        return self._byte_parser

    def parse_source(self) -> None:
        """Parse source text to find executable lines, excluded lines, etc.

        Sets the .excluded and .statements attributes, normalized to the first
        line of multi-line statements.

        """
        try:
            self._raw_parse()
        except (IndentationError) as err:
            if hasattr(err, "lineno"):
                lineno = err.lineno         # IndentationError
            else:
                lineno = err.args[1][0]     # TokenError
            raise NotEnaml(
                u"Couldn't parse '%s' as Enaml source: '%s' at line %d" % (
                    self.filename, err.args[0], lineno
                )
            )

        self.excluded = self.first_lines(self.raw_excluded)

        ignore = self.excluded | self.raw_docstrings
        starts = self.raw_statements - ignore
        self.statements = self.first_lines(starts) - ignore

    def _raw_parse(self) -> None:
        """Parse the source to find the interesting facts about its lines.

        A handful of attributes are updated.

        """
        # Find lines which match an exclusion pattern.
        if self.exclude:
            self.raw_excluded = self.lines_matching(self.exclude)

        # Tokenize, to find excluded suites, to find docstrings, and to find
        # multi-line statements.
        indent = 0
        exclude_indent = 0
        excluding = False
        excluding_decorators = False
        prev_toktype = lexer.indent(1)
        first_line = None
        empty = True
        first_on_line = True
        operators = {op[1] for op in lexer.operators}

        def generate_tokens(text):
            """Use enaml lexer to generate the tokens.

            """
            lexer.input(text)
            while True:
                tok = lexer.token()
                length = 0
                if tok is None:
                    break
                if tok.type == 'STRING':
                    # HINT use a string when counting to avoid encoding issues.
                    length = tok.value.count(str('\n'))
                yield (tok.type, tok.value, (tok.lineno, 0),
                       (tok.lineno + length, 0), '')

        tokgen = generate_tokens(self.text)
        for toktype, ttext, (slineno, _), (elineno, _), ltext in tokgen:
            if self.show_tokens:                # pragma: not covered
                print("%10s %5s %-20r %r" % (
                    toktype, nice_pair((slineno, elineno)), ttext, ltext
                ))
            if toktype == 'INDENT':
                indent += 1
            elif toktype == 'DEDENT':
                indent -= 1
            elif toktype == 'NAME':
                if ttext == 'class' or ttext == 'enamldef':
                    # Class definitions look like branches in the bytecode, so
                    # we need to exclude them.  The simplest way is to note the
                    # lines with the 'class' keyword.
                    self.raw_classdefs.add(slineno)
            elif toktype in operators:
                if ttext == ':':
                    should_exclude = ((elineno in self.raw_excluded) or
                                      excluding_decorators)
                    if not excluding and should_exclude:
                        # Start excluding a suite.  We trigger off of the colon
                        # token so that the #pragma comment will be recognized
                        # on the same line as the colon.
                        self.raw_excluded.add(elineno)
                        exclude_indent = indent
                        excluding = True
                        excluding_decorators = False
                elif ttext == '@' and first_on_line:
                    # A decorator.
                    if elineno in self.raw_excluded:
                        excluding_decorators = True
                    if excluding_decorators:
                        self.raw_excluded.add(elineno)
            elif toktype == 'STRING 'and prev_toktype == 'INDENT':
                # Strings that are first on an indented line are docstrings.
                # (a trick from trace.py in the stdlib.) This works for
                # 99.9999% of cases.  For the rest (!) see:
                # http://stackoverflow.com/questions/1769332/x/1769794#1769794
                self.raw_docstrings.update(range(slineno, elineno+1))
            elif toktype == 'NEWLINE':
                if first_line is not None and elineno != first_line:
                    # We're at the end of a line, and we've ended on a
                    # different line than the first line of the statement,
                    # so record a multi-line range.
                    for l in range(first_line, elineno+1):
                        self._multiline[l] = first_line
                first_line = None
                first_on_line = True

            if ttext is not None:
                # A non-whitespace token.
                empty = False
                if first_line is None:
                    # The token is not whitespace, and is the first in a
                    # statement.
                    first_line = slineno
                    # Check whether to end an excluded suite.
                    if excluding and indent <= exclude_indent:
                        excluding = False
                    if excluding:
                        self.raw_excluded.add(elineno)
                    first_on_line = False

            prev_toktype = toktype

        # Find the starts of the executable statements.
        if not empty:
            self.raw_statements.update(self.byte_parser._find_statements())

    def _analyze_ast(self) -> None:
        """Run the AstArcAnalyzer and save its results.

        `_all_arcs` is the set of arcs in the code.

        """
        aaa = EnamlASTArcAnalyser(self.text, self.raw_statements,
                                  self._multiline)

        EnamlASTVisitor(arc_analyser=aaa).visit(aaa.root_node)

        self._all_arcs = set()
        for l1, l2 in aaa.arcs:
            fl1 = self.first_line(l1)
            fl2 = self.first_line(l2)
            if fl1 != fl2:
                self._all_arcs.add((fl1, fl2))

        self._missing_arc_fragments = aaa.missing_arc_fragments


class EnamlASTArcAnalyser(AstArcAnalyzer):
    """Custom ast analyser modified to handle enaml ast.

    """
    def __init__(self, text: str, statements: set, multiline) -> None:
        self.root_node = parse(neuter_encoding_declaration(text))
        self.statements = set(multiline.get(l, l) for l in statements)
        self.multiline = multiline

        self.arcs = set()

        # A map from arc pairs to a pair of sentence fragments:
        #     (startmsg, endmsg).
        # For an arc from line 17, they should be usable like:
        #    "Line 17 {endmsg}, because {startmsg}"
        self.missing_arc_fragments = collections.defaultdict(list)
        self.block_stack = []

        self.debug = bool(int(os.environ.get("COVERAGE_TRACK_ARCS", 0)))


class EnamlASTVisitor(ASTVisitor):
    """An enaml AST visitor replacing ast.walk

    """

    #: Reference to the analyser using this visitor.
    arc_analyser = Typed(EnamlASTArcAnalyser)

    def default_visit(self, node, *args, **kwargs):
        """Skip nodes with no special meaning.

        """
        pass

    def visit_body(self, node, *args, **kwargs):
        """Visit the body of a node.

        """
        for n in node.body:
            self.visit(n, *args, **kwargs)

    visit_Module = visit_body
    visit_EnamlDef = visit_body
    visit_ChildDef = visit_body
    visit_TemplateInst = visit_body
    visit_Template = visit_body

    def visit_PythonModule(self, node, *args, **kwargs):
        """Analyse python module using the coverage arc analyser.

        """
        self.arc_analyser._code_object__Module(node.ast)

    def visit_FuncDef(self, node, *args, **kwargs):
        """Analyse funcdef like normal functions.

        """
        self.arc_analyser._code_object__FunctionDef(node.funcdef)

    def visit_operator_like_node(self, node, *args, **kwargs):
        """Analyse a binding or storage expr.

        If the OperatorExpr contains a PythonModule visit it otherwise
        consider the line as containing no arcs.

        """
        if node.expr and isinstance(node.expr.value, PythonModule):
            self.visit(node.expr.value, *args, **kwargs)

    visit_Binding = visit_operator_like_node
    visit_StorageExpr = visit_operator_like_node
