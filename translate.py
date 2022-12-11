import argparse
import re

from pathlib import Path

from lark import Lark, Transformer

def whole_sdl_ont(name, body, cnames, rnames):
    '''Generates complete ontology including the seriality axiom.
    
    Signature handling is a bit wonky.'''
    
    r_decl = '\n'.join(['ObjectProperty: ' + a for a in rnames])
    c_decl = '\n'.join(['Class: ' + a for a in cnames])
                         
    url = f'http://bjp.org/{name}'
    
    return f'''Prefix: : <{url}#>
Prefix: dc: <http://purl.org/dc/elements/1.1/>
Prefix: owl: <http://www.w3.org/2002/07/owl#>
Prefix: rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
Prefix: rdfs: <http://www.w3.org/2000/01/rdf-schema#>
Prefix: xml: <http://www.w3.org/XML/1998/namespace>
Prefix: xsd: <http://www.w3.org/2001/XMLSchema#>



Ontology: <{url}>

{r_decl}

{c_decl}

Class: owl:Thing SubClassOf: r some owl:Thing

{body}
'''

g ='''?start: worksheet
worksheet: axioms
axioms: axiom* 
?axiom: mlf | subclassof

mlf: ((NAME? ":")? (wff "."))
       
?wff: atomic
    | box
    | diamond
    | negation
    | implication
    | disjunction
    | conjunction
    | parenswff

subclassof: wff "=>" wff "."
?parenswff: "(" wff ")"
negation: "~" wff
box: "[" role? "]" wff
implication: wff "->" wff
diamond: "<" role? ">" wff

disjunction: wff "v" wff
conjunction: wff "&" wff
atomic: NAME
role: NAME
%import common.CNAME -> NAME
%import common.NUMBER -> NUMBER
%import common.WS_INLINE

%ignore WS_INLINE
%import common.WS
%ignore WS'''

text = '''
s1: (<>[0]A) -> (<1><0>[0]A).
s2: (<>[0]A) -> (<1>[0]A).
s3: ((<>[0]A) & ([1]A)) -> ((<1>[0]A) & ([1][1]A)).
s4: ((<>[0]A) & ([1]A)) -> (<1>(([0]A) & ([1]A))).
s5: (<>((<>[0]A) & ([1]A))) -> (<><1>(([0]A) & ([1]A))).
s6: ((<>[0]A) & (<>[1]A)) -> (<><1>(([0]A) & ([1]A))).
s7: ((<>[0]A) & (<>[1]A)) -> (<>(([0]A) & ([1]A))).

nec20: ([]A) -> ([0]A).
nec21: ([]A) -> ([1]A).
s6r: (<><1>(([0]A) & ([1]A))).
s7r:  (<>(([0]A) & ([1]A))).'''

t2 ='''
s1: <>[0]A -> <1><0>[0]A.
s2: <>[0]A -> <1>[0]A.
s3: <>[0]A & [1]A -> <1>[0]A & [1][1]A.
s4: <>[0]A & [1]A -> <1>([0]A & [1]A).
s4N:[](<>[0]A & [1]A -> <1>([0]A & [1]A)).
s5: <>(<>[0]A & [1]A) -> <><1>([0]A & [1]A).
s6: <>[0]A & <>[1]A -> <><1>([0]A & [1]A).
s7: <>[0]A & <>[1]A -> <>([0]A & [1]A).
'''
text1 = '''
s1lhs: (<>([0]A)).
s1rhs: (<1><0>[0]A).
s2hls: (<>[0]A).
s2rhs: (<1>[0]A).
GForm: ((<>A) & (<> B)) -> (<>(A & B)).
t1_2: (<1><0>[0]A) -> (<1>[0]A).
s1r: (<1><0>[0]A).
s2r: (<1>[0]A).
s6r: (<><1>(([0]A) & ([1]A))).
s7r:  (<>(([0]A) & ([1]A))).
s4n: []((<>[0]A) & ([1]A)) -> (<1>(([0]A) & ([1]A))).
s4nd: <>((<>[0]A) & ([1]A)) -> (<1>(([0]A) & ([1]A))).
'''

text = '''P1: <1>([1](party & <1>[1]cake)).
cake => bake.
P3: ~[1]bake.'''
flc = ['A','~A',
       '[]A', '[]~A',
       '~[]A', '~[]~A',
       '([]A) & ([]~A)',
       '~(([]A) & ([]~A))']

flcaxioms = [f'[]({c}) => <>({c}).' for c in flc]
flcaxioms.append('T: ([]A) & ([]~A).')
c = 0
for con in flc:
    c += 1
    flcaxioms.append(f'FLC{c}: {con}.')
#text =  '\n'.join(flcaxioms)
r = 'r'
class OWLTransformer(Transformer):
    def __init__(self):
        self.declared = set()
        self.atomics = set()
        self.roles = {r}
        self.counter = 0
        
    def _ambig(self, n):
        return n[-1]
        
    def NAME(self, n):
        return n.value

    def atomic(self, a):
        (a,) = a
        self.atomics.add(a)
        return a
        
    def NUMBER(self, n):
        return n.value
        
    def conjunction(self, items):
        return f'({items[0]} and {items[1]})'
    
    def negation(self, items):
        return f'(not {items[0]})'
        
    def disjunction(self, items):
        return f'({items[0]} or {items[1]})'

    def implication(self, items):
        return f'((not ({items[0]})) or ({items[1]}))'

    def normalise_role_expression(self, items):
        if len(items) == 1:
            d = r
            wff = items[0]
        else:
            d = items[0]
            try:
                int(d)
                d = f'r_{d}'
            except:
                pass
            wff = items[1]
        return (d, wff)
    
    def box(self, items):
        d, wff = self.normalise_role_expression(items)
        return f'({d} only {wff})'
    
    def diamond(self, items):
        d, wff = self.normalise_role_expression(items)
        return f'({d} some {wff})'
        
    def subclassof(self, items):
        self.counter += 1
        self.declared.add('RHS{self.counter}')
        self.declared.add('LHS{self.counter}')  
        return f'''Class: RHS{self.counter} EquivalentTo:  {items[1]}
        Class: LHS{self.counter} EquivalentTo:  {items[0]} 
            SubClassOf:  RHS{self.counter}'''
    
    def axioms(self, items):
        return items
        
    def mlf(self, items):
        self.declared.add(items[0])
        return f'Class: {items[0]} EquivalentTo:  {items[1]}'
    
    def equiv(self, items):
        self.declared.add(items[0])
        return f'Class: {items[0]} EquivalentTo:  {items[1]}'    


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Convert Modeldown files into OWL.')
    parser.add_argument('source', type=Path,
                    help='input file')
    parser.add_argument('-o', '--output', type=Path, 
                    help='input file')

    args = parser.parse_args()
    
    g = Path('grammars/modal.g').read_text()
    
    s = args.source.read_text()
    meta, formulae = re.split('---*', s)
    print(meta)
   
    parser = Lark(g, parser='earley')
    tree = parser.parse(formulae)
    name = 'test' if not args.output else args.output.name
    transformer = OWLTransformer()
    axioms = '\n'.join(transformer.transform(tree))
    cnames = transformer.atomics - transformer.declared
    ont = whole_sdl_ont(name, axioms, cnames, transformer.roles)
    if not args.output:
        print(ont)
    else:
        args.output.write_text(ont)