# -*- coding: utf-8 -*-

"""
context.py -- typing contexts for the Dieter programming language.
$Id: context.py 492 2010-04-26 21:16:03Z cpressey $
"""

from dieter.type import Type, TypeProc
import logging

logger = logging.getLogger("context")


class TypingError(Exception):
    """An exception indicating that a type incompatibility was encountered."""
    pass


class TypingContext(object):
    """Class that associates names with types in a given scope.

    A TypingContext object is passed along the AST during typechecking,
    being modified as a result.  Each TypingContext can have a parent
    TypingContext; lookups for types go to it if not found in the current one.
    
    It's actually more like a symbol table, because it associates
    every symbol with some information about it, even if it's not
    a type...

    """

    def __init__(self, parent):
        self.map = {}
        self.parent = parent
        self.module = None
        self.TypingError = TypingError

    def associate(self, name, type):
        """Associate the given name with the given type in this context.

        The name must be a name not already present in this context.

        """
        if name in self.map:
            raise TypingError("name " + name + " already bound to " + str(type))
        assert isinstance(type, Type)
        logger.info("associating " + name + " with " + str(type))
        self.map[name] = type

    def associate_qualifier(self, name):
        logger.info("registering " + name + " as a type qualifier")
        self.map[name] = "qualifier"

    def get_type(self, name):
        if name in self.map:
            logger.info("got type for " +name+ ": " + str(self.map[name]))
            return self.map[name]
        elif self.parent != None:
            logger.info("name " + name + " not found, trying parent context")
            return self.parent.get_type(name)
        else:
            raise TypingError("name " + name + " totally not found")

    def dump(self):
        for k, v in self.map.iteritems():
            if isinstance(v, Type):
                print(k + " : " + str(v))  # return string instead?
            else:
                print(k + " : " + v)

    def assert_equiv(self, inwhat, s, t):
        if not s.unify(t):
            raise TypingError("in " + inwhat + ": " + str(s) +
                              " not compatible with " + str(t))

    def check_call(self, proc_name, arg_types):
        """Check that a call to the named procedure or function in
        this context, with the given argument types, is legal.

        We start by obtaining the (fully general) type of the
        procedure being called, and instantiating it so that we
        can bind any type variables in it.
        
        If unification succeeds, we return the (bound) return type
        of the called procedure.

        """
        proc_type = self.get_type(proc_name)
        if not proc_type.is_callable():
            raise TypingError(self.name + ":" + str(proc_type) + " is not a procedure type")
        proc_type = proc_type.clone()
        return_type = proc_type.return_type

        # create a putative type representing the proc we are trying to call
        putative_type = TypeProc(return_type)
        for arg_type in arg_types:
            putative_type.add_arg_type(arg_type)

        logger.info("check_call to '" + proc_name + "' which has type " + str(proc_type))
        logger.info("putative type is " + str(putative_type))

        # try to unify
        if proc_type.unify(putative_type):
            return proc_type.return_type
        else:
            raise TypingError(str(proc_type) + " could not unify with " + str(putative_type))

    def new_module(self, module):
        """Create a new subcontext for a module.

        Given a module AST, return a new subcontext to
        contain things that cannot be accessed outside the
        module, such as its module-local variables.  The
        current context is made the parent of the returned
        subcontext, so any searches in the subcontext will
        search the parent if the term is not found.

        """
        subcontext = TypingContext(self)
        subcontext.module = module
        return subcontext

    def get_module(self):
        if self.module != None:
            return self.module
        elif self.parent != None:
            return self.parent.get_module()
        else:
            # XXX this is more of an internal error than a TypingError
            raise TypingError("get_module: no module in context")

    def new_procedure(self, procedure):
        """Create a new subcontext for a module.

        Like new_module, but for procedures.

        """
        subcontext = TypingContext(self)
        subcontext.procedure = procedure
        return subcontext

    def get_procedure(self):
        if self.procedure != None:
            return self.procedure
        elif self.parent != None:
            return self.parent.get_procedure()
        else:
            # XXX this is more of an internal error than a TypingError
            raise TypingError("get_procedure: no procedure in context")

    def global_context(self):
        if self.parent != None:
            return self.parent.global_context()
        else:
            return self
