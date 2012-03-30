#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
type.py -- data type structures for the Dieter programming language.
$Id: type.py 382 2010-01-28 23:40:43Z cpressey $
"""

import logging

logger = logging.getLogger("type")


class Type(object):
    """
    A class representing types.  Note that types are *not* AST nodes.
    After typechecking, every AST node has a type (even if only TypeVoid.)
    'Simple' types like TypeVoid may be aliased (there need not be multiple
    instances of TypeVoid; all expressions of type void can point to a
    single TypeVoid object.)  For this reason it is a good idea for code
    to treat Type objects as immutable.
    
    Note that this class only deals with the structual aspect of types:
    constructing and unifying them.
    Type-checking is dealt with in the TypingContext class.
    """

    def __init__(self):
        self.qualifiers = []

    def qualify(self, qual):
        """
        Returns a new type which is the same as this type except
        with the given qualifier added to it.
        """
        t = self.clone()
        if qual not in self.qualifiers:
            t.qualifiers.append(qual)
        return t

    def unqualify(self, qual):
        """
        Returns a new type which is the same as this type except
        without the given qualifier.
        """
        t = self.clone()
        if qual in t.qualifiers:
            t.qualifiers.remove(qual)
        return t

    def has_qualifier(self, qual):
        """
        Returns True if this type has the given qualifier.
        """
        return qual in self.get_all_qualifiers()

    def get_binding(self):
        """
        Returns the concrete type that this type represents.  In the case of
        actual concrete types, this just returns the same type, but in the case
        of type variables, the chain of equivalence relations is followed to
        find the basic concrete type, if any (or None if the variable is unbound.)
        """
        return self

    def get_all_qualifiers(self):
        """
        Returns all qualifiers on this type.  In the case of concrete types,
        this is just the set of qualifiers as stored internally, but in the
        case of type variables, the chain of equivalence relations is followed
        to collect all qualifiers involved in the binding.
        """
        return self.qualifiers

    def can_receive(receptor, provider):
        """
        The rule for unification with type qualifiers is this: the qualifiers of
        the provider must be a superset of the qualifiers of the receptor.
        
        A type can receive another type if the other type is at least as qualified
        as this type.
        """
        for qual in receptor.get_all_qualifiers():
            if not provider.has_qualifier(qual):
                return False
        return True

    def is_bound(self):
        return True

    def isa(self, python_type):
        """
        Checks if the type this is bound to is the given type.
        Crashes on unbound type variables.
        """
        return isinstance(self.get_binding(), python_type)

    def is_callable(self):
        return False

    def __str__(self):
        """
        Returns a human-readable string representation of this type.
        """
        d = ""
        for qual in self.qualifiers:
            d += qual + ' '
        return d

    def clone(self):
        """
        Returns a deep, fresh copy of this type.  Fresh meaning all type
        variables in the new copy are unbound.
        
        The default implementation of this method is appropriate for
        primitive types -- it just returns another reference to the type,
        which is safe when the type is immutable, as all primitives are.
        """
        return self

    def bestow_qualifiers_onto(self, other):
        for qual in self.get_all_qualifiers():
            if not other.has_qualifier(qual):
                other.qualifiers.append(qual)

    def unify(receptor, provider):
        """
        Returns true, and possibly modifies the given types, if this type
        can be unified with the given type.  By "unify" we mean "make
        equivalent to by assigning appropriate types to type variables."

        Because these types have special rules regarding type qualifiers,
        the unify operation is not commutative (as it would usually be).
        The 'self' type is considered to be the receptor type, whereas the
        argument is the provider type.  The rule for unification with type
        qualifiers is this: the qualifiers of the provider must be a
        superset of the qualifiers of the receptor.
        """
        logger.info("unifying " + str(receptor) + " (receptor) with " + str(provider) + " (provider)")
        if not receptor.can_receive(provider):
            logger.info("receptor cannot receive provider: unification failed")
            return False
        if not provider.is_bound():
            provider.bind_to(receptor)
            return True
        else:
            return provider.isa(receptor.__class__)


class TypeVoid(Type):
    def __str__(self):
        return Type.__str__(self) + 'void'


class TypeBool(Type):
    def __str__(self):
        return Type.__str__(self) + 'bool'


class TypeInt(Type):
    def __str__(self):
        return Type.__str__(self) + 'int'


class TypeRat(Type):
    def __str__(self):
        return Type.__str__(self) + 'rat'


class TypeString(Type):
    def __str__(self):
        return Type.__str__(self) + 'string'


class TypeRef(Type):
    def __str__(self):
        return Type.__str__(self) + 'ref'


# Non-simple types follow.

class TypeMap(Type):

    # NB.  from_type can be None.

    def __init__(self, to_type, from_type):
        Type.__init__(self)
        self.to_type = to_type
        self.from_type = from_type

    def __str__(self):
        s = Type.__str__(self) + 'map '
        if self.from_type is not None:
            s += 'from ' + str(self.from_type)
        s += ' to ' + str(self.to_type)
        return s

    def unify(receptor, provider):
        logger.info("unifying " + str(receptor) + " with " + str(provider))
        if not receptor.can_receive(provider):
            logger.info("receptor cannot receive provider: unification failed")
            return False
        if not provider.is_bound():
            provider.bind_to(receptor)
            return True
        provider = provider.get_binding()
        if not (provider.isa(TypeMap)):
            return False
        if receptor.from_type is not None:
            if not receptor.from_type.unify(provider.from_type):
                return False
        return receptor.to_type.unify(provider.to_type)

    def clone(self):
        from_clone = None
        if self.from_type is not None:
            from_clone = self.from_type.clone()
        new_type = TypeMap(self.to_type.clone(), from_clone)
        self.bestow_qualifiers_onto(new_type)
        return new_type


class TypeProc(Type):
    def __init__(self, return_type):
        Type.__init__(self)
        self.arg_types = []
        self.return_type = return_type

    def is_callable(self):
        return True

    def add_arg_type(self, arg_type):
        self.arg_types.append(arg_type)

    def get_arg_type(self, index):
        return self.arg_types[index]

    def __str__(self):
        d = Type.__str__(self) + 'proc('
        arg_type_strings = []
        for arg_type in self.arg_types:
            arg_type_strings.append(str(arg_type))
        d += ','.join(arg_type_strings) + "): " + str(self.return_type)
        return d

    def unify(receptor, provider):
        logger.info("unifying " + str(receptor) + " with " + str(provider))
        if not receptor.can_receive(provider):
            logger.info("receptor cannot receive provider: unification failed")
            return False
        if not provider.is_bound():
            provider.bind_to(receptor)
            return True
        provider = provider.get_binding()
        if not provider.isa(TypeProc):
            return False
        i = 0
        for arg_type in receptor.arg_types:
            if not arg_type.unify(provider.get_arg_type(i)):
                return False
            i += 1
        return receptor.return_type.unify(provider.return_type)

    def clone(self):
        t = TypeProc(self.return_type.clone())
        for arg_type in self.arg_types:
            t.add_arg_type(arg_type.clone())
        self.bestow_qualifiers_onto(t)
        return t


class TypeVar(Type):

    def __init__(self, name):
        Type.__init__(self)
        self.name = name
        self.bound_to = None

    def __str__(self):
        return Type.__str__(self) + '*' + self.name

    def __unicode__(self):
        return Type.__unicode__(self) + u'♥' + self.name

    def is_variable(self):
        return True

    def is_bound(self):
        return self.bound_to is not None

    def get_binding(self):
        if self.bound_to is None:
            return None
        if self.bound_to is self:
            return self
        return self.bound_to.get_binding()
        
    def bind_to(self, target):
        # Note that when setting the binding for a type variable, we
        # point to the top of the chain, not the bottom as we probably
        # normally would in performing disjoint set union in a common
        # unify.  We do this, even though it is less efficient, in order
        # to pick up all the type qualifiers that are mentioned along
        # the unification chain.
        self.bound_to = target

    def get_all_qualifiers(self):
        quals = []
        quals += self.qualifiers
        type = self
        while type.bound_to is not None:
            type = type.bound_to
            quals += type.qualifiers
        return quals

    def unify(receptor, provider):
        logger.info("unifying. receptor:" + str(receptor) + ", provider:" + str(provider))
        if not receptor.can_receive(provider):
            logger.info("receptor cannot receive provider: unification failed")
            return False

        if not receptor.is_bound():
            receptor.bind_to(provider)
            return True
        
        if not provider.is_bound():
            provider.bind_to(receptor)
            return True

        lhs_type = receptor_type.get_binding()
        rhs_type = provider_type.get_binding()
        
        return lhs_type.unify(rhs_type)

    def clone(self):
        t = TypeVar(self.name)
        self.bestow_qualifiers_onto(t)
        return t
