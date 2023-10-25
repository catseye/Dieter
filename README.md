The Dieter Programming Language
===============================

_Entry_ [@ catseye.tc](https://catseye.tc/node/Dieter)
| _See also:_ [Castile](https://codeberg.org/catseye/Castile#castile)

Description
-----------

Dieter (that's Dieter as in the German masculine given name Dieter, not
dieter as in "one who diets") is a little experimental programming
language which conflates *type qualifiers* with *modules*. In this
article, we'll first describe these mechanisms. Then we'll show how
their interaction produces something that resembles object-oriented
programming.

### Type Qualifiers ###

A type qualifier is simply a keyword which may be placed before any type
expression, further specializing it. Type qualifiers should be familiar
to programmers of C, where *storage classes*, such as `const` and
`static`, are examples of type qualifiers. The cardinal rule of type
qualifiers in Dieter is this: **during assignment (or
parameter-passing), a variable (or parameter) whose type possesses some
type qualifier *only* accepts values of the same type that possess *at
least* that same qualifier.**

Some basic properties of type qualifiers follow (but first, for
concreteness, let's stipulate that Dieter has an assortment of primitive
types: `bool`, `int`, `rat`, and `string`. And `void` denoting the type
of the absence of any value.) The order that type qualifiers are given
in a type expression doesn't matter: if `beefy` and `gnarly` are type
qualifiers, then `beefy gnarly int` and `gnarly beefy int` are wholly
equivalent types. Neither does the number of occurrences matter:
`beefy gnarly beefy int` is equivalent to `beefy gnarly int`.
Algebraically speaking, type qualifiers are commmutative and idempotent.

You can't assign an `int` to a `beefy int` (or pass it to a procedure
expecting a `beefy int`,) but you can assign a `beefy int` to an `int`.
This might sound counter-intuitive initially, but after you think about
it a bit I'm sure you'll conclude it's appropriate: it's just like how
you can assign a `const int` to an `int` in C, but not an `int` to a
`const int`. `int` is more general, and will tolerate information being
lost in the copy, whereas `beefy int` is more specific, and will not
accept a value with insufficient information associated with it. Or, if
you prefer, while all `beefy int`s are `int`s, there are `int`s that
aren't `beefy` and thus can't be assigned to a variable which is
restricted to `beefy int`s.

### Type Operators ###

In order to make use of type qualifiers in user programs, Dieter
provides type operators, similar to C's type-casting facilities, to
manipulate type qualifiers.

In fact, Dieter has only one explicit type operator, called `bestow`. It
can be used in an expression to endow its type with further type
qualifiers. `bestow` takes a type qualifier q and a value of some type t
and returns a new value of type q·t. (You can think of q·t as a kind of
pseudo-product type that obeys the algebraic laws given in the previous
section rather than those of conventional products.)

The complementary operation — stripping q·t back to t — is not
explicitly denoted; it happens automatically as needed. (This is the
underlying rule that was in effect, when we stated that a `beefy int`
can be assigned to an `int`.)

Note that type operators in no way alter the *value* of the expression
they are used in, only its *type*.

### Type Variables ###

Dieter supports uniform polymorphic types. Type expressions can contain
type variables (which I'll denote with ♥ for no good reason) which can
unify with concrete types or other type variables during instantiation
of a language construct. In practice, this means that procedures can
have type variables in their parameter and return types; these variables
are replaced by types specified at the call site whenever a procedure
call is type-checked.

The scope of each type variable ranges over a single instance of a
single procedure. So `♥x` in the parameter list of `grunt` is the same
type as every occurrence of `♥x` anywhere in the definition of `grunt`
during that same invokation of `grunt`, but may be different from `♥x`
in other invokations of `grunt` (calls to `grunt` from different call
sites), and different from `♥x` appearing in other procedures entirely.

A complication for polymorphism in Dieter is that type variables range
not only over core type expressions, but *also* over type qualifiers.
That is, the types `beefy gnarly int` and `beefy ♥t` unify, and their
most general unifier is {`♥t` → `gnarly int`}. This has a few
implications for the unification algorithm; see [Appendix
A](#appendix_a) for a detailed discussion of these.

### Modules ###

Dieter is a modular language, which has its usual meaning — a Dieter
program consists of a set of modules, each of which exposes only its
interface, not its implementation, to all other modules. In Dieter,
however, there is a notable twist: every type qualifier is defined by
some module which bears the same name. The key idea of Dieter is this:
**a type operator that affects a given qualifier may *only* be used in
the module which defines that qualifier.** The reasoning for this is
similar to the argument against using casts in the C language: the goal
of typing is to specify constraints on the program's structure and to
automatically check that they are met. If programmers are allowed to
muck with types willy-nilly, it defeats the purpose of having these
constraints in the first place. So the power to `bestow` a particular
type qualifier is only given out to the module "in charge" of that type
qualifier. This is a form of encapsulation: the internal details of some
thing (in this case, a type modifier) can only be manipulated by the
implementation of that thing.

### Procedures ###

Each Dieter module consists of a set of procedure declarations. Any
procedure can be called from any procedure in any module; they are
comparable to `public static` methods in Java in this respect.
Procedures are polymorphic, as mentioned; each one's parameter and
return types can contain type variables. At each call site, the type
variables are unified with the types of the values being passed to them,
and resolved ultimately to concrete types.

A bit of administrivia that we should also mention is that Dieter
requires procedures to be declared, though not necessarily defined,
before they are called. Much like Pascal, it offers a `forward`
declaration construct for this purpose. It can also be used to declare
procedures intrinsic to the implementation, procedures external to some
set of modules, or completely ficticious procedures for the purpose of
demonstrating and testing the type system.

### Example ###

We're now ready to give a very simple example of a Dieter module.

    module beefy

      procedure beef_up(x: ♥t): beefy ♥t
      begin
        return (bestow beefy x)
      end

    end

The intent of this example is to get the general gist of the language
across, not to demonstrate good programming practice. The procedure
`beef_up` essentially behaves as `bestow`, except, being a procedure, it
may be called from any procedure, including those in other modules. So,
it breaks the abstraction we just presented; it implements something
akin to a "generic setter method," providing direct access to a data
member that is ordinarily private.

### Object-oriented Programming ###

We'll now try to show that this interaction between type qualifiers and
modules produces something resembling object-oriented programming by
adding three language features to Dieter: a declaration form and two new
types.

-   Module-level variables are variables that are instantiated on, well,
    the level of the module. (This is in contrast to local variables in
    procedures, which I haven't said anything about, but which I've
    nevertheless assumed exist in Dieter...) Module-level variables
    can't be accessed directly from outside the module; they're
    comparable to `private static` fields in Java.
-   `ref` is a built-in type. These aren't references *to* anything;
    each is just a unique value, much like values of `ref` type in the
    language Erlang. A program can obtain a new `ref` value by calling
    `new_ref()`; the value thus obtained is guaranteed to be different
    from all other `ref` values in the program.
-   `map` is a built-in type constructor, over range (key) and domain
    (value) types, that defines a data structure that acts like a
    dictionary. The usual square-bracket syntax `x[y]` is used to
    reference a location within a map.

We can now construct a class of objects like so:

    module person

      var name_map: map from person ref to string
      var age_map: map from person ref to int

      procedure person_new(name: string, age: int): person ref
        var p: person ref
      begin
        p := bestow person new_ref()
        name_map[p] := name
        age_map[p] := age
        return p
      end

      procedure person_get_name(p: person ref): string
      begin
        return name_map[p]
      end

      procedure person_attend_birthday_party(p: person ref): void
      begin
        age_map[p] := succ(age_map[p])
      end

    end

Because the type qualifier `person` is defined by the module `person`,
which only uses `bestow` in one place, we know exactly what kind of
expressions can result in a type qualified by `person`. More to the
point, we know that no other procedure in any other module can create a
`person`-qualified type without calling `person_new`.

### Mixins ###

If we loosen the constraints on `map`s, and say that the range (key)
type can be left unspecified and that values of all types can be used as
keys in any given `map`, then we have have a way to make type qualifiers
work like mixins:

    module tagged

      var tag_map : map to string

      procedure make_tagged(x: ♥t): tagged ♥t
      begin
        return (bestow tagged x)
      end

      procedure tag(x: tagged ♥t, y: string): void
      begin
        tag_map[x] := y
      end

      procedure get_tag(x: tagged ♥t): string
      begin
        return tag_map[x]
      end

    end

I think this demonstrates an underrated principle of OO, namely
*identity*. If I call `tag(make_tagged(4), "mine")`, do *all*
occurrences of 4 have that tag, or just the ephemeral instance of 4
passed to `tag`? If there can't be seperate instances of 4, that might
be a reason for OO languages to not treat it as an object. And if you
believe seperate instances of 4 are silly, that's an argument against
"everything is an object".

### Inheritance ###

Since module-level variables are private to each module, they give
Dieter something akin to traditional encapsulation. But what about
inheritance?

Well, we can get something like inheritance if we give Dieter another
feature. We haven't said much about scope of names so far; in
particular, we haven't said what happens when one declares two different
procedures with the same name and number of parameters, and what, if
anything, should happen when client code tries to call such ambiguously
declared procedures.

Hey, in the spirit of compromise, let's just say that when this happens,
*all* those procedures are called! Specifically, all the procedures
whose formal parameter types are compatible with the types of the actual
parameters are called — procedures with parameters of completely
different types, or of more highly qualified types, are not called.

And, to keep this interesting, let's say that the order in which these
procedures are called depends on the generality of their parameter
types. If `grind(beefy ♥t):void` and `grind(beefy gnarly ♥t):void` are
both defined, and `grind` is called with a variable whose type is
qualified with both `beefy` and `gnarly`, then `grind(beefy ♥t):void`
(the more general) should be called first, then
`grind(beefy gnarly ♥t):void` (the more specific) called second.

There are a few issues now that need to be dealt with.

-   We've discussed compatibility of parameter types of a procedure, but
    not its return type. For simplicity, let's just disallow differing
    return types on different procedures with the same name — it's a
    compile-time error.
-   It would be nice if procedures had a way to capture the results of a
    procedure that was called before them in this calling chain. So,
    let's say that every procedure has access to an implicit read-only
    variable that holds the result of the previous procedure (if any)
    that was executed along this chain. The type of this variable will
    always be the same as the return type of the current procedure
    (because by the previous bullet point, the previous procedure must
    have had the same return type as the current one.) If no previous
    procedure with this signature was executed, the value will be `nil`.
    For syntax, let's call this implicit variable `super`.
-   It would also be nice if a procedure could prevent any further
    procedures from being called in this chain. Let's give Dieter a
    special form of `return` for this purpose — say, `return final`.
-   Finally, what about incomparable signatures? Say that, in the above
    example, procedures `grind(gnarly ♥t):void` and `grind(♥t):void` are
    defined too. Then, when `grind` is called with a `beefy gnarly`
    variable, `grind(♥t):void` gets called first (it's the most
    general), but which gets called next: `grind(gnarly ♥t):void` or
    `grind(beefy ♥t):void`? We can let the programmer give some sort of
    disambiguating assertion, like `order beefy < gnarly`, to enforce a
    partial ordering between type qualifiers. Then we know that the more
    general procedure — in this case `grind(gnarly ♥t):void` — will be
    called before `grind(beefy ♥t):void`, because we just noted that,
    all other things being equal, we want `gnarly` to be treated as more
    general than `beefy`.

Now: do you think it's a coincidence that the last problem looks similar
to the problems that come from multiple inheritance, where we don't
quite know what we should be inheriting when two of our superclasses are
descendants of the same class? Well, I can tell you this much: it's
definately *not* a coincidence that I chose `super` and `final` for the
names of the other two features!

This whole thing looks to me very much as if we were approaching
object-oriented programming from another direction. Which might not be
such a surprise, if one thinks of subclassing as a special form of type
qualification.

Of course, it's not *quite* the same in Dieter as it is in most OO
languages. For example, procedures in Dieter do not actually override
those with more general (less qualified) signatures, they simply add to
them. But, those more specific procedures could be written to ignore the
results of, and undo the state changes of, the more general procedures
in the chain that were called first, which would accomplish essentially
the same thing.

Background
----------

Why did I design this language, anyway?

### Hungarian Notation ###

The origins of the central idea in Dieter — **encapsulate type
qualifiers in modules that define them** — was an indirect result of
reading [Joel Spolsky's explanation of the value of Hungarian
notation](http://www.joelonsoftware.com/articles/Wrong.html). He
contrasts the original notion of Hungarian notation with the
cargo-cultist convention that it somehow degenerated into. He explains
how it helps make incorrect programs look incorrect.

I thought, why stop there? If the purpose of Hungarian notation is to
make evident assignment errors between variables that have the same type
but different *roles*, then why can't you have the compiler type-check
the roles, too? Well, you can, and that's basically what Dieter is doing
with type qualifiers — using them as a computer-checkable form of
Hungarian notation.

### Aliasing Prevention ###

What further spurred development of the idea was the problem of
aliasing. Aliasing is where some part of a program is dealing with two
references which might or might not point to the same thing —
importantly, you can't make guarantees for the sake of safety (or
optimization) that they *don't* point to the same thing. So you have to
assume that they might.

The contribution of type qualifiers to this is that in some situations
you might be able to give the two references two different type
qualifiers, even though they are basically the same type, thus
guaranteeing that they don't in fact refer to the same value.

There's a significant problem with this, though: it still doesn't give
you a hard-and-fast guarantee that no aliasing is occurring, because the
module that defines a modifier can still do whatever it likes with it
internally. It gives you only a sort of "module-level guarantee"; only
if you trust the individual modules involved to not be aliasing values
of these types, can you be sure the values won't be aliased "in the
large".

In addition, it's far from certain that there are lots of cases where
this would *in practice* support some genuine non-trivial beneficial
code pattern while preventing aliasing. It could be that all examples
where this works are quite contrived. I suppose that if I were to do
further work on Dieter, it would be to try to discover whether this is
really the case or not.

### Related work ###

Type qualifiers have been around informally for a long time, probably
almost as long as there have been types. Here's [Dennis Ritchie ranting
against certain type qualifiers proposed for ANSI
C](http://www.lysator.liu.se/c/dmr-on-noalias.html). (One of which,
coincidentally, was intended to deal with aliasing, albiet quite
myopically.)

Mark P Jones has written [a
paper](http://web.cecs.pdx.edu/~mpj/pubs/esop92.html) and [a
thesis-turned-book](http://web.cecs.pdx.edu/~mpj/pubs/thesis.html)
describing a theory of qualified types. Dieter can be seen as a concrete
instance of Jones's theory (as can many other type systems — it's a very
general theory), although I have not explicated it as such here, as the
resulting article would likely have been much less accessible.

Haskell's type classes (another type system easily seen as a concrete
instance of qualified types) are very similar to Dieter's type
qualifiers. However, in Haskell, every type either belongs to or does
not belong to some class: every `Int` is an `Eq Ord`, due to the
mathematical properties of `Int`s. In Dieter, every type can potentially
be modified with every qualifier: there can be `int`s, `eq int`s,
`ord int`s, and `eq ord int`s, all slightly different.

On the other end of the spectrum, solidly in the domain of application
rather than theory, [CQUAL](http://www.cs.umd.edu/~jfoster/cqual/) is an
extension of C which adds user-defined type qualifiers. CQUAL is
primarily concerned with inferring type qualifiers where there are none,
and is not concerned with encapsulating qualifiers within modules.

Conclusion
----------

I hope you found Dieter to be an entertaining little diversion through
type-qualifier-land (and that you did not expect too much more, or I
imagine you'll have been somewhat disappointed.)

Although there is no reference implementation of Dieter (and it's
unlikely that there could be without some more specified semantics,)
there is a reference parser and type-checker (not at all guaranteed to
be bug-free) written in Python of all things.

Appendix A
----------

### Polymorphic Typing with Type Qualifiers ###

While Dieter does not support full-blown type inference — all variables
must be explicitly notated with their type — it does support uniform
polymorphic typing using type variables, and it uses the core mechanism
of type inference, namely unification, to give those variables concrete
types at each usage instance.

In place of a concrete type, a type variable may be given. Like a
concrete type, this type variable can possess any number of type
qualifiers. During each instance of the thing being typed (for example,
each call to a procedure,) the type variables are resolved into concrete
types by unification.

The presence of type qualifiers makes this process more complicated.

The first thing to note is that unification during inference is no
longer commutative — it is no longer the case that, if A unifies with B,
then B necessarily unifies with A. As mentioned, a procedure with a
formal parameter of type `gnarly int` will not accept (i.e. is not
compatible with) an actual parameter with type simply `int`. But the
reverse situation is acceptable — we think of the `gnarly` modifier
being 'dropped'. The convention we will use when describing this
non-commutative unification is to call the formal parameter (or variable
being assigned to) the receptor and write it on the left, and call the
actual parameter (or expression being assigned) the provider and write
it on the right.

The cardinal rule, which applies to every primitive type expression,
including those with variables, is that **the qualifiers on the provider
must be a superset of the qualifiers on the receptor**.

As during the conventional algorithm, an unbound type variable in either
type expression will unify with (take on the binding of) the type
subexpression that corresponds with it in the other type expression. In
addition, here it will also take on the type qualifiers of that
subexpresion, if it can. This leaves us with the question of which ones,
and when.

If the variable is in the receptor position, it might as well unify with
*all* of the type qualifiers on the provider, because those must be a
superset of the receptor's in order to unify at all, and because down
the road, they can always be 'dropped' from the variable, should it be
used as a provider.

If the variable is in the provider position, the type in receptor
position can't possibly have any more qualifiers than the variable — or
it wouldn't be able to unify in the first place. So the variable might
as well unify with the whole expression in the receptor position.

If both positions contain variables, the provider's variable should be
bound to the receptor's type expression, because it will be the one that
is more general.

The other thing to note that differs from conventional type inference is
that **a type variable, once bound to a qualified type, may be
*re-bound* to a less qualified type**.

### Examples ###

Module names aren't really important for this, so they're omitted. We'll
assume the following intrinsics are available:

    forward and(bool, bool): bool
    forward equal(♥t, ♥t): bool
    forward print(string): void

#### Example 1 ####

    procedure thing(): void
      var i, j: int
      var s, t: string
    begin
      if and(equal(i, j), equal(s, t)) then print("yes") else print("no")
    end

Should typecheck successfully, because the two calls to `equal` are two
seperate instances of the type ♥t, but the two parameters inside the
type signature of `equal` are the same instance.

#### Example 2 ####

    forward glunt(beefy gnarly ♥t): gnarly ♥t
    ...
    procedure thing(): void
      var i: beefy gnarly int
    begin
      if equal(glunt(i), 4) then print("yes") else print("no")
    end

Should typecheck successfully. The call to `glunt` returns a
`gnarly int`. Midway through typechecking the call to `equal`, we obtain
{♥t → `gnarly int`}. But when we typecheck the second argument we see
that it's simply an `int`. We *re-bind* the variable to obtain {♥t →
`int`}. This is OK with respect to the first argument — we just consider
the `gnarly` to be dropped.

#### Example 3 ####

    forward traub(beefy gnarly ♥t): bool
    ...
    procedure thing(p: beefy ♥s): ♥s
    begin
      if traub(p) then print("yes") else print("no")
      return p
    end

Should *not* typecheck. The call to `traub` needs something qualified
with both `beefy` and `gnarly`. `beefy ♥s` will fail to unify with it.

Grammar
-------

    Dieter    ::= {Module | Ordering | Forward} ".".
    Ordering  ::= "order" Name/qual "<" Name/qual.
    Module    ::= "module" Name/qual {"var" VarDecl} {ProcDecl} "end".
    Forward   ::= "forward" Name/proc "(" [Type {"," Type}] ")" ":" Type.
    VarDecl   ::= Name/var ":" Type.
    ProcDecl  ::= "procedure" Name/proc "(" [VarDecl {"," VarDecl}] ")" ":" Type {"var" VarDecl} Statement.
    Statement ::= "begin" {Statement} "end"
                | "if" Expr "then" Statement ["else" Statement]
                | "while" Expr "do" Statement
                | Name/var ["[" Expr "]"] ":=" Expr
                | Name/proc "(" [Expr {"," Expr}] ")"
                | "return" ["final"] Expr
                .
    Expr      ::= Name/var ["[" Expr "]"]
                | Name/proc "(" [Expr {"," Expr}] ")"
                | "(" Expr ")"
                | "bestow" Qualifier Expr
                | "super"
                .
    Type      ::= {Name/qual} BareType.
    BareType  ::= "map" ["from" Type] "to" Type
                | "♥" Name/tvar
                | "bool" | "int" | "rat" | "string" | "ref"
                .
