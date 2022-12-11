?start: worksheet
?worksheet: axioms
?axioms: axiom* 
?axiom: mlf | subclassof | equiv

mlf: ((NAME? ":")? (implication "."))

?implication: binary | implication  "->" (binary | unary)
?binary : unary | disjunction | conjunction
disjunction: binary "v" unary
conjunction: binary "&" unary

?unary:  basic 
    | box
    | diamond
    | negation
negation: "~" unary
box: "[" arole? "]" unary
diamond: "<" arole? ">" unary
?parenswff: "(" implication ")"
?basic: atomic
    | parenswff
subclassof: implication "=>" implication "."
equiv: implication "=" implication "."
atomic: NAME
arole: NAME

%import common.CNAME -> NAME
%import common.NUMBER -> NUMBER
%import common.WS_INLINE

%ignore WS_INLINE
%import common.WS
%ignore WS  