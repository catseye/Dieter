#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dieter.py -- driver for parsing/typechecking the Dieter programming language.
$Id: dieter.py 382 2010-01-28 23:40:43Z cpressey $
"""

import sys
from optparse import OptionParser
import logging

from dieter.scanner import Scanner
from dieter.parser import Parser
from dieter.context import TypingContext


def load(filename, options):
    f = open(filename, "r")
    scanner = Scanner(f.read())
    f.close()
    parser = Parser(scanner)
    ast = parser.Dieter()
    context = TypingContext(None)
    if options.verbose:
        logging.basicConfig(level=logging.INFO)
    ast.typecheck(context)
    if options.dump_ast:
        print "--- AST: ---"
        print ast.dump(0)
    if options.dump_symtab:
        print "--- Symbol Table: ---"
        context.dump()

def main(argv):
    optparser = OptionParser("[python] dieter.py {options} {source.dtr}\n" + __doc__)
    optparser.add_option("-a", "--dump-ast",
                         action="store_true", dest="dump_ast", default=False,
                         help="dump AST after source is parsed")
    optparser.add_option("-s", "--dump-symtab",
                         action="store_true", dest="dump_symtab", default=False,
                         help="dump symbol table after source is parsed")
    optparser.add_option("-v", "--verbose",
                         action="store_true", dest="verbose", default=False,
                         help="""be verbose about actions taken internally
                                 (e.g. type unification)""")
    (options, args) = optparser.parse_args(argv[1:])
    for filename in args:
        load(filename, options)


if __name__ == "__main__":
    main(sys.argv)
