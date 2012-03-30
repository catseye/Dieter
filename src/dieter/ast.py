#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
ast.py -- Abstract Syntax Trees for the Dieter programming language.
$Id: ast.py 398 2010-02-04 00:20:41Z cpressey $
"""

import logging

import dieter.type as type
import dieter.context as context

logger = logging.getLogger("ast")


class AST:
    """Class representing nodes in an abstract syntax tree.
    
    Each node has a type.  Initially this is None, meaning
    no type has been assigned.  This is not the same as
    VoidType.
    
    Calling the typecheck method of a node attempts to
    compute the types of that node, and all of its children,
    in the given typing context.

    """

    type = None

    def typecheck(self, context):
        """Checks that this part of the AST is well-typed, and set the type
        attribute of the AST to the type.

        Returns nothing.  Raises an exception if AST is ill-typed.
        (This method is abstract, and is only included on AST for the sake
        of documentation.)

        """
        raise NotImplementedError


class Program(AST):
    def __init__(self):
        self.forwards = []
        self.modules = []
        self.orderings = []

    def add_forward(self, forward):
        self.forwards.append(forward)

    def add_module(self, module):
        self.modules.append(module)

    def add_ordering(self, ordering):
        self.orderings.append(ordering)

    def dump(self, indent):
        d = ('  ' * indent) + "program\n"
        for forward in self.forwards:
            d += forward.dump(indent + 1)
        for ordering in self.orderings:
            d += ordering.dump(indent + 1)
        for module in self.modules:
            d += module.dump(indent + 1)
        return d

    def typecheck(self, context):
        for forward in self.forwards:
            forward.typecheck(context)
        for ordering in self.orderings:
            ordering.typecheck(context)
        for module in self.modules:
            if module.fails:
                logger.info("typechecking module " + module.name +  " (intends to fail)")
                failed = False
                try:
                    module.typecheck(context)
                except context.TypingError, e:
                    logger.info("caught TypingError " + str(e))
                    failed = True
                except Exception, e:
                    logger.info("caught Exception " + str(e))
                finally:
                    if not failed:
                        raise context.TypingError("module claimed to fail typechecking but didn't")
            else:
                logger.info("typechecking module " + module.name +  " (intends to succeed)")
                module.typecheck(context)


class Ordering(AST):
    def __init__(self, before, after):
        self.before = before
        self.after = after

    def dump(self, indent):
        d = ('  ' * indent) + "order " + self.before + " < " + self.after + "\n"
        return d

    def typecheck(self, context):
        # XXX context.add_ordering(self.before, self.after)
        pass


class FwdDecl(AST):
    def __init__(self, name, type_expr):
        self.name = name
        self.type_expr = type_expr

    def dump(self, indent):
        d = ('  ' * indent) + 'forward ' + self.name + " : \n" + self.type_expr.dump(indent+1) + "\n"
        return d

    def typecheck(self, context):
        self.type_expr.typecheck(context)
        self.type = self.type_expr.type
        context.associate(self.name, self.type)


### Modules...

class Module(AST):
    def __init__(self, name, fails):
        self.name = name
        self.fails = fails
        self.locals = []
        self.procs = []

    def add_local(self, local):
        self.locals.append(local)

    def add_proc(self, proc):
        self.procs.append(proc)

    def dump(self, indent):
        d = ('  ' * indent) + 'module ' + self.name + "\n"
        for local in self.locals:
            d += local.dump(indent + 1)
        for proc in self.procs:
            d += proc.dump(indent + 1)
        return d

    def typecheck(self, context):
        logger.info("typechecking module " + self.name)
        context.associate_qualifier(self.name)
        # make a new context for this module, to contain module-local variables
        my_context = context.new_module(self)
        for local in self.locals:
            local.typecheck(my_context)
        for proc in self.procs:
            proc.typecheck(my_context)


class VarDecl(AST):
    def __init__(self, name, type_expr):
        self.name = name
        self.type_expr = type_expr

    def dump(self, indent):
        d = ('  ' * indent) + ('var ' + self.name + ' : ' +
                               self.type_expr.dump(0) + "\n")
        return d

    def typecheck(self, context):
        self.type_expr.typecheck(context)
        self.type = self.type_expr.type
        context.associate(self.name, self.type)


class ProcDecl(AST):
    def __init__(self, name):
        self.name = name
        self.args = []
        self.locals = []
        self.return_type_expr = None
        self.body = None

    def add_arg(self, arg):
        self.args.append(arg)

    def add_local(self, local):
        self.locals.append(local)

    def set_body(self, body):
        self.body = body

    def set_return_type_expr(self, type_expr):
        self.return_type_expr = type_expr

    def dump(self, indent):
        d = ('  ' * indent) + ('procedure ' + self.name + " : " +
                               self.return_type_expr.dump(0) + "\n")
        for arg in self.args:
            d += arg.dump(indent + 1)
        for local in self.locals:
            d += local.dump(indent + 1)
        d += self.body.dump(indent + 1)
        return d

    def typecheck(self, context):
        self.return_type_expr.typecheck(context)
        return_type = self.return_type_expr.type
        proc_type = type.TypeProc(return_type)
        # make a new context for this procedure, to contain args and local variables
        my_context = context.new_procedure(self)
        for arg in self.args:
            arg.typecheck(my_context)
            proc_type.add_arg_type(arg.type)
        for local in self.locals:
            local.typecheck(my_context)
        context.global_context().associate(self.name, proc_type)
        self.body.typecheck(my_context)


### ... statements ...

class CompoundStatement(AST):
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)

    def dump(self, indent):
        d = ('  ' * indent) + "begin\n"
        for step in self.steps:
            d += step.dump(indent + 1)
        d += ('  ' * indent) + "end\n"
        return d

    def typecheck(self, context):
        for step in self.steps:
            step.typecheck(context)

class IfStatement(AST):
    def __init__(self, test, then_stmt, else_stmt):
        self.test = test
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    def dump(self, indent):
        d = ('  ' * indent) + "if\n"
        d += self.test.dump(indent + 1)
        d += ('  ' * indent) + "then\n"
        d += self.then_stmt.dump(indent + 1)
        if self.else_stmt != None:
            d += ('  ' * indent) + "else\n"
            d += self.else_stmt.dump(indent + 1)
        return d

    def typecheck(self, context):
        self.test.typecheck(context)
        test_type = self.test.type
        context.assert_equiv("if", type.TypeBool(), test_type)
        self.then_stmt.typecheck(context)
        self.else_stmt.typecheck(context)


class WhileStatement(AST):
    def __init__(self, test, body):
        self.test = test
        self.body = body

    def dump(self, indent):
        d = ('  ' * indent) + "while\n"
        d += self.test.dump(indent + 1)
        d = ('  ' * indent) + "do\n"
        d += self.body.dump(indent + 1)
        return d

    def typecheck(self, context):
        self.test.typecheck(context)
        context.assert_equiv("while", test_type, type.TypeBool())
        self.body.typecheck(context)


class ReturnStatement(AST):
    def __init__(self, expr):
        self.expr = expr

    def dump(self, indent):
        d = ('  ' * indent) + "return\n"
        d += self.expr.dump(indent + 1)
        return d

    def typecheck(self, context):
        self.expr.typecheck(context)
        return_type = self.expr.type
        context.assert_equiv("return", return_type, context.get_procedure().return_type_expr.type)


class CallStatement(AST):
    def __init__(self, name):
        self.name = name
        self.args = []

    def add_arg(self, arg):
        self.args.append(arg)

    def dump(self, indent):
        d = ('  ' * indent) + self.name + "(\n"
        for arg in self.args:
            d += arg.dump(indent + 1)
        d += ('  ' * indent) + ")\n"
        return d

    def typecheck(self, context):
        logger.info("typechecking procedure call to " + self.name)
        arg_types = []
        for arg in self.args:
            arg.typecheck(context)
            arg_types.append(arg.type)
        return_type = context.check_call(self.name, arg_types)
        self.type = return_type


class AssignStatement(AST):
    def __init__(self, name):
        self.name = name
        self.index = None
        self.expr = None

    def set_index(self, index):
        self.index = index

    def set_expr(self, expr):
        self.expr = expr

    def dump(self, indent):
        d = ('  ' * indent) + self.name + " "
        if self.index != None:
            d += ('  ' * indent) + "[\n"
            d += self.index.dump(indent + 1)
            d += ('  ' * indent) + "] "
        d += ":=\n"
        d += self.expr.dump(indent + 1)
        return d

    def typecheck(self, context):
        lhs_type = context.get_type(self.name)
        # if this variable is a map type then make sure its index is the right type
        if isinstance(lhs_type, type.TypeMap):
            assert self.index != None
            self.index.typecheck(context)
            index_type = self.index.type
            if lhs_type.from_type is not None:
                context.assert_equiv("index", lhs_type.from_type, index_type)
            lhs_type = lhs_type.to_type
        self.expr.typecheck(context)
        rhs_type = self.expr.type
        context.assert_equiv("assignment", lhs_type, rhs_type)


### ... expressions ...

class IntConstExpr(AST):
    def __init__(self, value):
        self.value = value

    def dump(self, indent):
        d = ('  ' * indent) + str(self.value) + "\n"
        return d

    def typecheck(self, context):
        self.type = type.TypeInt()


class StringConstExpr(AST):
    def __init__(self, value):
        self.value = value

    def dump(self, indent):
        d = ('  ' * indent) + "\"" + self.value + "\"\n"
        return d

    def typecheck(self, context):
        self.type = type.TypeString()


class VarRefExpr(AST):
    def __init__(self, name):
        self.name = name
        self.index = None

    def set_index(self, index):
        self.index = index

    def dump(self, indent):
        d = ('  ' * indent) + str(self.name) + " "
        if self.index != None:
            d += ('  ' * indent) + "[\n"
            d += self.index.dump(indent + 1)
            d += ('  ' * indent) + "]"
        d += "\n"
        return d

    def typecheck(self, context):
        self.type = context.get_type(self.name)
        # if this variable is a map type then make sure its index is the right type
        if isinstance(self.type, type.TypeMap):
            assert self.index != None
            self.index.typecheck(context)
            index_type = self.index.type
            if self.type.from_type is not None:
                context.assert_equiv("index", self.type.from_type, index_type)
            self.type = self.type.to_type


class SuperExpr(AST):
    def __init__(self):
        pass

    def dump(self, indent):
        d = ('  ' * indent) + "super\n"
        return d

    def typecheck(self, context):
        # same as the return type of the current procedure
        self.type = context.get_procedure().return_type


class BestowExpr(AST):
    def __init__(self, qual, expr):
        self.qual = qual
        self.expr = expr

    def dump(self, indent):
        d = ('  ' * indent) + "bestow " + self.qual + "\n"
        d += self.expr.dump(indent + 1)
        return d

    def typecheck(self, context):
        if self.qual != context.get_module().name:
            raise context.TypingError("type operation on %s used outside of its module (in module %s)" %
              (self.qual, context.get_module().name))
        else:
            self.expr.typecheck(context)
            self.type = self.expr.type.qualify(self.qual)


class CallExpr(AST):
    def __init__(self, name):
        self.name = name
        self.args = []

    def add_arg(self, arg):
        self.args.append(arg)

    def dump(self, indent):
        d = ('  ' * indent) + self.name + "(\n"
        for arg in self.args:
            d += arg.dump(indent + 1)
        d += ('  ' * indent) + ")\n"
        return d

    def typecheck(self, context):
        logger.info("typechecking function call to " + self.name)
        arg_types = []
        for arg in self.args:
            arg.typecheck(context)
            arg_types.append(arg.type)
        return_type = context.check_call(self.name, arg_types)
        self.type = return_type


### ... type expressions ...

class PrimitiveTypeExpr(AST):
    def __init__(self, token):
        self.token = token

    def __str__(self):
        return self.token

    def dump(self, indent):
        d = ('  ' * indent) + self.token
        return d

    def typecheck(self, context):
        map = {
            'void': type.TypeVoid,
            'bool': type.TypeBool,
            'int': type.TypeInt,
            'rat': type.TypeRat,
            'string': type.TypeString,
            'ref': type.TypeRef
        }
        self.type = map[self.token]()


class MapTypeExpr(AST):
    def __init__(self, range, domain):
        self.range = range
        self.domain = domain

    def dump(self, indent):
        d = ('  ' * indent) + "map from " + self.range.dump(0)
        if self.domain is not None:
            d = d + " to " + self.domain.dump(0)
        return d

    def typecheck(self, context):
        self.range.typecheck(context)
        if self.domain is None:
            self.type = type.TypeMap(self.range.type, None)
        else:
            self.domain.typecheck(context)
            self.type = type.TypeMap(self.range.type, self.domain.type)


class ProcTypeExpr(AST):
    def __init__(self, arg_type_exprs, return_type_expr):
        self.arg_type_exprs = arg_type_exprs
        self.return_type_expr = return_type_expr

    def dump(self, indent):
        d = ('  ' * indent) + 'proc('
        for arg_type_expr in self.arg_type_exprs:
            d += arg_type_expr.dump(0) + ","
        d = d[:-1] + "): " + self.return_type_expr.dump(0)
        return d

    def add_arg_type_expr(self, arg_type_expr):
        self.arg_type_exprs.append(arg_type_expr)

    def typecheck(self, context):
        for arg_type_expr in self.arg_type_exprs:
            arg_type_expr.typecheck(context)
        self.return_type_expr.typecheck(context)
        self.type = type.TypeProc(self.return_type_expr.type)
        for arg_type_expr in self.arg_type_exprs:
            self.type.add_arg_type(arg_type_expr.type)


class QualifiedTypeExpr(AST):
    def __init__(self, qual, type_expr):
        self.qual = qual
        self.type_expr = type_expr

    def dump(self, indent):
        return self.qual + " " + self.type_expr.dump(0)

    def typecheck(self, context):
        self.type_expr.typecheck(context)
        self.type = self.type_expr.type.qualify(self.qual)


class TypeVariableExpr(AST):
    def __init__(self, name):
        self.name = name

    def dump(self, indent):
        return "*" + self.name

    def typecheck(self, context):
        self.type = type.TypeVar(self.name)
