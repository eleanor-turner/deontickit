import argparse
import re
from pprint import pprint

from pathlib import Path

from lark import Lark, Transformer


def s5(r):
    return f'''    <SymmetricObjectProperty>
        <ObjectProperty abbreviatedIRI=":{r}"/>
    </SymmetricObjectProperty>
    <TransitiveObjectProperty>
        <ObjectProperty abbreviatedIRI=":{r}"/>
    </TransitiveObjectProperty>
    <ReflexiveObjectProperty>
        <ObjectProperty abbreviatedIRI=":{r}"/>
    </ReflexiveObjectProperty>'''

def subprop(sub, sup):
    return f'''
<SubObjectPropertyOf>
    <ObjectProperty abbreviatedIRI=":{sub}"/>
    <ObjectProperty abbreviatedIRI=":{sup}"/>
</SubObjectPropertyOf>'''

def ground_aaia(agents, flc) -> list:
    '''Hacking an OWL/XML file To Be Imported'''
    axioms = [s5('r')]
    axioms.extend([s5(a) for a in agents])
    if len(agents) == 1:
        axioms.append(subprop(list(agents)[0], 'r'))
        return axioms
    
    lhs = '''
            <ObjectSomeValuesFrom>
                <ObjectProperty abbreviatedIRI=":r"/>
                %(alpha)s
            </ObjectSomeValuesFrom>
    '''
    kagents = list()
    kschema = list()
    groundings = list()
    # handle last agent...
    for a in agents:
        axioms.append(subprop(a, 'r'))
        if kagents:
            body = '\n'.join(kagents)
            con = f'''
            <ObjectIntersectionOf>
                {body}
            </ObjectIntersectionOf>'''
        else:
            con = '%(alpha)s'
            
        krhs = f'''
            <ObjectSomeValuesFrom>
                <ObjectProperty abbreviatedIRI=":{a}"/>
                {con}
            </ObjectSomeValuesFrom>
    '''   
        kschema.append(f'''
        <SubClassOf>
            {lhs}
            {krhs}
        </SubClassOf>
        ''')
        kagents.append(f'''
            <ObjectSomeValuesFrom>
                <ObjectProperty abbreviatedIRI=":{a}"/>
                %(alpha)s
            </ObjectSomeValuesFrom>
    ''')
    for f in flc:
        for k in kschema:
            axioms.append(k % {'alpha':f})
    return axioms

def owlxml_ont(name, body, cnames, rnames):
    cdecls = list()
    for c in cnames:
        cdecls.append(f'''  <Declaration>
        <Class abbreviatedIRI=":{c}"/>
    </Declaration>''')
    rdecls = list()
    for r in rnames:
        rdecls.append(f'''  <Declaration>
        <ObjectProperty abbreviatedIRI=":{r}"/>
    </Declaration>''')
    n = '\n'
    return f'''<?xml version="1.0"?>
<Ontology xmlns="http://www.w3.org/2002/07/owl#"
     xml:base="{name}"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     ontologyIRI="{name}">
    <Prefix name="" IRI="{name}#"/>
    <Prefix name="dc" IRI="http://purl.org/dc/elements/1.1/"/>
    <Prefix name="owl" IRI="http://www.w3.org/2002/07/owl#"/>
    <Prefix name="rdf" IRI="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>
    <Prefix name="xml" IRI="http://www.w3.org/XML/1998/namespace"/>
    <Prefix name="xsd" IRI="http://www.w3.org/2001/XMLSchema#"/>
    <Prefix name="rdfs" IRI="http://www.w3.org/2000/01/rdf-schema#"/>
    {n.join(cdecls)}
    {n.join(rdecls)}
    {n.join(body)}
</Ontology>'''

def whole_ont(name, body, cnames, rnames, imports=''):
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

{imports}

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

r = 'r'
class ClassAtom:
    def __init__(self, name):
        self.name = name
    
    def xml(self):
        return '<Class abbreviatedIRI=":{self.name}"/>'
    
class OWLXMLTransformer(Transformer):
    def __init__(self):
        self.declared = set()
        self.atomics = set()
        self.roles = set()
        self.counter = 0
        self.flc = set()
        self.locflc = set()
        self.r = '<ObjectProperty abbreviatedIRI=":r"/>'
        
    def to_flc(self, term):
        self.locflc.add(term)
        self.locflc.add(f'''
        <ObjectComplementOf>
            {term}
        </ObjectComplementOf>''')
        return term
    
    def drop_from_flc(self, term):
        self.locflc.remove(term)
        self.locflc.remove(f'''
        <ObjectComplementOf>
            {term}
        </ObjectComplementOf>''')        
            
        
    def _ambig(self, n):
        return n[-1]
        
    def NAME(self, n):
        return n.value

    def atomic(self, a):
        (a,) = a
        self.atomics.add(a)
        return self.to_flc(f'<Class abbreviatedIRI=":{a}"/>')        
     
    def arole(self, items):
        d = items[0]
        try:
            d = f'r_{int(d)}'
        except:
            pass
        self.roles.add(d)
        return f'<ObjectProperty abbreviatedIRI=":{d}"/>'

    def NUMBER(self, n):
        return n.value
    
    def negation(self, items):
        return f'''
        <ObjectComplementOf>
            {items[0]}
        </ObjectComplementOf>'''
    
    def conjunction(self, items):
        return self.to_flc(f'''
        <ObjectIntersectionOf>
            {items[0]}
            {items[1]}
        </ObjectIntersectionOf>''')
        
    def disjunction(self, items):
        return self.to_flc(f'''
        <ObjectUnionOf>
            {items[0]}
            {items[1]}
        </ObjectUnionOf>''')

    def implication(self, items):
        return self.to_flc(f'''
    <ObjectUnionOf>
        <ObjectComplementOf>
            {items[0]}
        </ObjectComplementOf>
        {items[1]}
    </ObjectUnionOf>''')
    
    def normalise_role_expression(self, items):
        if len(items) == 1:
            d = self.r
            wff = items[0]
        else:
            d = items[0]
            wff = items[1]
        return (d, wff)
    
    def box(self, items):
        d, wff = self.normalise_role_expression(items)
        return self.to_flc(f'''
    <ObjectAllValuesFrom>
        {d}
        {wff}
    </ObjectAllValuesFrom>'''  )
    
    def diamond(self, items):
        d, wff = self.normalise_role_expression(items)
        return self.to_flc(
        f'''<ObjectSomeValuesFrom>
            {d}
            {wff}
        </ObjectSomeValuesFrom>''' )      
    
    def mlf(self, items):
        #if items[0][0:6] == '<Class' and items[0] in self.locflc:
        #    self.drop_from_flc(items[0])
        self.flc.update(self.locflc)
        self.locflc = set()
        return  f'''    <EquivalentClasses>
            <Class abbreviatedIRI=":{items[0]}"/> 
            {items[1]}
        </EquivalentClasses>'''    
    
    def subclassof(self, items):
        self.locflc = set()
        return f'''    <SubClassOf>
        {items[0]} 
        {items[1]}
    </SubClassOf>'''
    
    def equiv(self, items):
        self.locflc = set()
        return  f'''    <EquivalentClasses>
            {items[0]} 
            {items[1]}
        </EquivalentClasses>''' 

    def axioms(self, items):
        
        return items
        

    
class OWLTransformer(Transformer):
    def __init__(self):
        self.declared = set()
        self.atomics = set()
        self.roles = {r}
        self.counter = 0
        self.flc = set()
    
    def to_flc(self, term):
        self.flc.add(term)
        self.flc.add(f'~{term}')
        return term
        
    def _ambig(self, n):
        return n[-1]
        
    def NAME(self, n):
        return n.value

    def atomic(self, a):
        (a,) = a
        self.atomics.add(a)
        return self.to_flc(a)
    
    def arole(self, items):
        self.roles.add(items[0])
        return items[0]
    
    def NUMBER(self, n):
        return n.value
    
    def negation(self, items):
        return f'(not {items[0]})'
    
    def conjunction(self, items):
        return self.to_flc(f'({items[0]} and {items[1]})')
        
    def disjunction(self, items):
        return self.to_flc(f'({items[0]} or {items[1]})')

    def implication(self, items):
        return self.to_flc(f'((not ({items[0]})) or ({items[1]}))')

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
        return self.to_flc(f'({d} only {wff})')
    
    def diamond(self, items):
        d, wff = self.normalise_role_expression(items)
        return self.to_flc(f'({d} some {wff})')
        
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
    parser.add_argument('-l', '--logic', type=str, help='name of logic (sdl, cstit)', default='sdl')

    args = parser.parse_args()
    
    g = Path('grammars/modal.g').read_text()
    
    s = args.source.read_text()
    meta, formulae = re.split('---*', s)
    print(meta)
   
    parser = Lark(g, parser='earley')
    tree = parser.parse(formulae)
    name = 'test' if not args.output else args.output.name
    transformer = OWLXMLTransformer()
    axioms = transformer.transform(tree)
    if args.logic == 'cstit':
        grounding = ground_aaia(transformer.roles, transformer.flc)
        axioms.extend(grounding)
    cnames = transformer.atomics - transformer.declared
    ont = owlxml_ont(name, axioms, cnames, transformer.roles)
    if not args.output:
        print(ont)
    else:
        args.output.write_text(ont)