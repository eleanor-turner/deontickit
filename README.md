# deontickit

(Probably should rename to modalkit?)

dontickit is Python framework for exploring various deontic logics, that is, modal logic of *obligation*.

In particular, deontikit contains translators from  various deontic logics into descriptiong logics (namely OWL)
while preserving critical aspects of the semantics.

For some deontic logics, e.g., Standard Deontic Logic (SDL) the tranlation is close to equivalent 
(technially sigma-inseperable for the signature of the ontology minus the role which represents the
accessibility relation and any concepts names we introduce for convenience).

For others, things get more complicated. However, we usually get a form of equisatisfiability which allows us,
with care, to hack a complete reasoning procedure. 

# modaldown

We definite a typable, ASCII-ish syntax for multi-modal logic (i.e., with boxes and diamonds), plus some extra feature
such as metadata and tests. This gives us a format for collecting and exploring various examples and puzzles from the
literature.

modaldown supports a form of "ontology (in the computer science sense) oriented" theory development.

# Test corpus

We are collecting examples from the literature.

# Key implementation feature

deontickit seeks to exploit existing, production quality reasoners. Our primary focus is description logic reasoners, such 
as Pellet, Konclude, FaCT++, and HermiT. While adequately expressive, they lack the ability to handle user-defined 
axiom schemata, i.e.,where meta-linguisitc variables get syntactic substitutions. As many interesting logics of agents
and agency have, shall we say, rather funky extra axiom schemata, this is an issue.

We handle this problem by using a form of the Fisher-Ladner closure, roughly, the subconcpts of the original theory plus their 
complements. We then ground any funky axiom schemata into the Fisher-Ladner closure and add the resulting axioms to our
output ontology.