#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
parser.py -- parser for the Dieter programming language.
$Id: parser.py 382 2010-01-28 23:40:43Z cpressey $
"""

import dieter.ast as ast

class Parser(object):
    """
    A recursive-descent parser for Dieter.
    """

    def __init__(self, scanner):
        """
        Creates a new Parser object.  The passed-in scanner is expected
        to be compatible with a Scanner object.
        """
        self.scanner = scanner

    def Dieter(self):
        program = ast.Program()
        while self.scanner.token in ["order", "module", "forward"]:
            if self.scanner.token == "order":
                ordering = self.Ordering()
                program.add_ordering(ordering)
            elif self.scanner.token == "module":
                module = self.Module()
                program.add_module(module)
            elif self.scanner.token == "forward":
                forward = self.Forward()
                program.add_forward(forward)
            else:
                self.error("expected order, module or forward, found " + token)
        return program

    def Ordering(self):
        self.scanner.expect("order")
        qual1 = self.scanner.grab()
        self.scanner.expect("<")
        qual2 = self.scanner.grab()
        ordering = ast.Ordering(qual1, qual2)
        return ordering

    def Module(self):
        self.scanner.expect("module")
        name = self.scanner.grab()
        fails = False
        if self.scanner.token == "fails":
            self.scanner.expect("fails")
            fails = True
        module = ast.Module(name, fails)
        while self.scanner.token == "var":
            self.scanner.expect("var")
            vdecl = self.VarDecl()
            module.add_local(vdecl)
        while self.scanner.token == "procedure":
            pdecl = self.ProcDecl()
            module.add_proc(pdecl)
        self.scanner.expect("end")
        return module

    def Forward(self):
        self.scanner.expect("forward")
        name = self.scanner.grab()
        type_expr = ast.ProcTypeExpr([], None)
        self.scanner.expect("(")
        if self.scanner.token != ")":
            arg_type_expr = self.TypeExpr()  
            type_expr.add_arg_type_expr(arg_type_expr)
            while self.scanner.token == ",":
                self.scanner.expect(",")
                arg_type_expr = self.TypeExpr()
                type_expr.add_arg_type_expr(arg_type_expr) 
        self.scanner.expect(")")
        self.scanner.expect(":")
        type_expr.return_type_expr = self.TypeExpr()
        fwd = ast.FwdDecl(name, type_expr)
        return fwd

    def VarDecl(self):
        name = self.scanner.grab()
        self.scanner.expect(":")
        type_expr = self.TypeExpr()
        var = ast.VarDecl(name, type_expr)
        return var

    def ProcDecl(self):
        self.scanner.expect("procedure")
        name = self.scanner.grab()
        proc = ast.ProcDecl(name)
        self.scanner.expect("(")
        if self.scanner.token != ")":
            arg = self.VarDecl()
            proc.add_arg(arg)
            while self.scanner.token == ",":
                self.scanner.expect(",")
                arg = self.VarDecl()
                proc.add_arg(arg)
        self.scanner.expect(")")
        self.scanner.expect(":")
        type_expr = self.TypeExpr()
        proc.set_return_type_expr(type_expr)
        while self.scanner.token == "var":
            self.scanner.expect("var")
            vdecl = self.VarDecl()
            proc.add_local(vdecl)
        stmt = self.Statement()
        proc.set_body(stmt)
        return proc

    def Statement(self):
        stmt = None
        if self.scanner.token == "begin":
            stmt = ast.CompoundStatement()
            self.scanner.expect("begin")
            while self.scanner.token != "end":
                step = self.Statement()
                stmt.add_step(step)
            self.scanner.expect("end")
        elif self.scanner.token == "if":
            self.scanner.expect("if")
            test = self.Expr()
            self.scanner.expect("then")
            then_stmt = self.Statement()
            else_stmt = None
            if self.scanner.token == "else":
                self.scanner.expect("else")
                else_stmt = self.Statement()
            stmt = ast.IfStatement(test, then_stmt, else_stmt)
        elif self.scanner.token == "while":
            self.scanner.expect("while")
            test = self.Expr()
            self.scanner.expect("do")
            body = self.Statement()
            stmt = ast.WhileStatement(test, body)
        elif self.scanner.token == "return":
            self.scanner.expect("return")
            if self.scanner.token == "final":
                self.scanner.expect("final")
            expr = self.Expr()
            stmt = ast.ReturnStatement(expr)
        else:
            name = self.scanner.grab()
            if self.scanner.token == "(":
                self.scanner.expect("(")
                stmt = ast.CallStatement(name)
                if self.scanner.token != ")":
                    expr = self.Expr()
                    stmt.add_arg(expr)
                    while self.scanner.token == ",":
                        self.scanner.expect(",")
                        expr = self.Expr()
                        stmt.add_arg(expr)
                self.scanner.expect(")")
            else:
                stmt = ast.AssignStatement(name)
                if self.scanner.token == "[":
                    self.scanner.expect("[")
                    index = self.Expr()
                    stmt.set_index(index)
                    self.scanner.expect("]")
                self.scanner.expect(":=")
                expr = self.Expr()
                stmt.set_expr(expr)
        return stmt

    def Expr(self):
        expr = None
        if self.scanner.token == "(":
            self.scanner.expect("(")
            expr = self.Expr()
            self.scanner.expect(")")
        elif self.scanner.token == "bestow":
            self.scanner.expect("bestow")
            name = self.scanner.grab()
            sub = self.Expr()
            expr = ast.BestowExpr(name, sub)
        elif self.scanner.token == "super":
            self.scanner.expect("super")
            expr = ast.SuperExpr()
        elif self.scanner.toktype == "int":
            value = self.scanner.tokval
            self.scanner.grab()
            expr = ast.IntConstExpr(value)
        elif self.scanner.toktype == "string":
            value = self.scanner.tokval
            self.scanner.grab()
            expr = ast.StringConstExpr(value)
        else:
            name = self.scanner.grab()
            if self.scanner.token == "(":
                expr = ast.CallExpr(name)
                self.scanner.expect("(")
                if self.scanner.token != ")":
                    sub = self.Expr()
                    expr.add_arg(sub)
                    while self.scanner.token == ",":
                        self.scanner.expect(",")
                        sub = self.Expr()
                        expr.add_arg(sub)
                self.scanner.expect(")")
            else:
                expr = ast.VarRefExpr(name)
                if self.scanner.token == "[":
                    self.scanner.expect("[")
                    index = self.Expr()
                    expr.set_index(index)
                    self.scanner.expect("]")
        return expr

    def TypeExpr(self):
        quals = []
        # XXX would be better to have 'forward qualifier'
        while self.scanner.token not in [
                u"void", u"bool", u"int", u"rat", u"string", u"ref", u"map", u"♥"
            ]:
            name = self.scanner.grab()
            quals.append(name)
        type_expr = self.BareTypeExpr()
        for qual in quals:
            type_expr = ast.QualifiedTypeExpr(qual, type_expr)
        return type_expr

    def BareTypeExpr(self):
        token = self.scanner.token
        if token in ["void", "bool", "int", "rat", "string","ref"]:
            self.scanner.scan()
            return ast.PrimitiveTypeExpr(token)
        elif token == "map":
            self.scanner.scan()
            from_type_expr = None
            if self.scanner.token == "from":
                self.scanner.expect("from")
                from_type_expr = self.TypeExpr()
            self.scanner.expect("to")
            to_type_expr = self.TypeExpr()
            return ast.MapTypeExpr(to_type_expr, from_type_expr)
        elif token == u"♥":
            self.scanner.scan()
            name = self.scanner.grab()
            return ast.TypeVariableExpr(name)
        else:
            self.scanner.error("expected valid type expression")
