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

def disjoint(op1, op2):
    return f'''
        <DisjointObjectProperties>
            <ObjectProperty abbreviatedIRI=":{op1}"/>
            <ObjectProperty abbreviatedIRI=":{op2}"/>
        </DisjointObjectProperties>'''

def reflexive_prop(op1, op2):
    return f'''
        <SubClassOf>
            <Class abbreviatedIRI="owl:Thing"/>
            <ObjectUnionOf>
                <ObjectHasSelf>
                    <ObjectProperty abbreviatedIRI=":{op1}"/>
                </ObjectHasSelf>
                <ObjectHasSelf>
                    <ObjectProperty abbreviatedIRI=":{op2}"/>
                </ObjectHasSelf>
            </ObjectUnionOf>
        </SubClassOf>'''

def serial_prop(r):
    return f''' 
        <SubClassOf>
            <Class abbreviatedIRI="owl:Thing"/>
            <ObjectSomeValuesFrom>
                <ObjectProperty abbreviatedIRI=":{r}"/>
                <Class abbreviatedIRI="owl:Thing"/>
            </ObjectSomeValuesFrom>
        </SubClassOf>'''
        
def kconj(kagents):
    if len(kagents) == 1:
        return kagents[0]
    else:
        body = '\n'.join([o for a, o in kagents])
        return f'''
        <ObjectIntersectionOf>
            {body}
        </ObjectIntersectionOf>'''   

def ground_ctd(operators: set, flc: set) -> list:
    axioms = []
    if 'r_I' in operators and 'r_S' in operators:
        axioms.extend([disjoint('r_I','r_S')])
        axioms.extend([reflexive_prop('r_I','r_S')])
        axioms.append(serial_prop('r_I'))
        axioms.append(serial_prop('r_S'))
    return axioms

def ground_aaia(grounding: str, agents: set, flc: set) -> list:
    agents = sorted(agents)
    #E.g. agents = ['r_1','r_2','r_3']
    '''Hacking an OWL/XML file To Be Imported'''
    axioms = [s5('r')]
    axioms.extend([s5(a) for a in agents])
    axioms.extend([subprop(a, 'r') for a in agents])
    if len(agents) == 1:
        return axioms
    if grounding == 'plain':
        return axioms
    kschema = list()
    lhs = '''
            <ObjectSomeValuesFrom>
                <ObjectProperty abbreviatedIRI=":r"/>
                %(alpha)s
            </ObjectSomeValuesFrom>
    '''
    # E.g. lhs = "<r>cake"

    # We always need at least two agents for a grounding
    # (0<=i<k for k>=1, so minimum is 0 and 1)
    # So we pop one agent to be the "seed" on the rhs
    # and we pop another agent to be the kth agent

    match grounding:
        case 'aaia_big':
            #print('aaia_big')
            for kth in agents:
                #E.g. kth = r_3
                remainder = [a for a in agents if a != kth]

                kagents = [(a, f'''
                    <ObjectSomeValuesFrom>
                        <ObjectProperty abbreviatedIRI=":{a}"/>
                        %(alpha)s
                    </ObjectSomeValuesFrom>
                ''') for a in remainder]
                #E.g. kagents = [(r_1, "<r_1>cake"), (r_2, "<r_2>cake")]
                # print(f'r -> {kth}({[a for a in remainder]})')

                con = kconj(kagents)
                #E.g. con = "<r_1>cake & <r_2>cake"

                krhs = f'''
                    <ObjectSomeValuesFrom>
                        <ObjectProperty abbreviatedIRI=":{kth}"/>
                        {con}
                    </ObjectSomeValuesFrom>
                '''  
                #E.g. krhs = "<r_3>(<r_1>cake & <r_2>cake)"

                kschema.append(f'''
                <SubClassOf>
                    {lhs}
                    {krhs}
                </SubClassOf>
                ''')       

        case 'aaia':
            #print('aaia_normal')
            for i in range(len(agents)-1):
                #E.g. kth = r_3
                kth = agents.pop()

                #len(kagents) == k-1
                kagents = [(a, f'''
                    <ObjectSomeValuesFrom>
                        <ObjectProperty abbreviatedIRI=":{a}"/>
                        %(alpha)s
                    </ObjectSomeValuesFrom>
                ''') for a in agents]
                #E.g. kagents = [(r_1, "<r_1>cake"), (r_2, "<r_2>cake")]
                #print(f'r -> {kth}({[a for a in agents]})')

                con = kconj(kagents)
                #E.g. con = "<r_1>cake & <r_2>cake"

                krhs = f'''
                    <ObjectSomeValuesFrom>
                        <ObjectProperty abbreviatedIRI=":{kth}"/>
                        {con}
                    </ObjectSomeValuesFrom>
                '''  
                #E.g. krhs = "<r_3>(<r_1>cake & <r_2>cake)"

                kschema.append(f'''
                <SubClassOf>
                    {lhs}
                    {krhs}
                </SubClassOf>
                ''')       

        case 'aaia_small':
            print('aaia_small')
            kth = agents.pop()

            #len(kagents) == k-1
            kagents = [(a, f'''
                <ObjectSomeValuesFrom>
                    <ObjectProperty abbreviatedIRI=":{a}"/>
                    %(alpha)s
                </ObjectSomeValuesFrom>
            ''') for a in agents]

            #E.g. kagents = [(r_1, "<r_1>cake"), (r_2, "<r_2>cake")]
            print(f'r -> {kth}({[a for a in agents]})')

            con = kconj(kagents)
            #E.g. con = "<r_1>cake & <r_2>cake"

            krhs = f'''
                <ObjectSomeValuesFrom>
                    <ObjectProperty abbreviatedIRI=":{kth}"/>
                    {con}
                </ObjectSomeValuesFrom>
            '''  
            #E.g. krhs = "<r_3>(<r_1>cake & <r_2>cake)"

            kschema.append(f'''
            <SubClassOf>
                {lhs}
                {krhs}
            </SubClassOf>
            ''')

            for a in agents:
                krhs = f'''
                    <ObjectSomeValuesFrom>
                        <ObjectProperty abbreviatedIRI=":{a}"/>
                        <ObjectSomeValuesFrom>
                            <ObjectProperty abbreviatedIRI=":{kth}"/>
                            %(alpha)s
                        </ObjectSomeValuesFrom>
                    </ObjectSomeValuesFrom>
                '''  
    
                print(f'r -> {a}({kth})')

                kschema.append(f'''
                <SubClassOf>
                    {lhs}
                    {krhs}
                </SubClassOf>
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

g = '''?start: worksheet
?worksheet: axioms
axioms: axiom* 
?axiom: mlf | subclassof | equiv

mlf: ((NAME? ":")? (implication "."))

?implication: binary | implication  "->" binary 
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
arole: NAME | NUMBER

LCASE_LETTER: "a".."z"
UCASE_LETTER: "A".."Z"
SYMBOL:  "ϕ"
DIGIT: "0".."9"
LETTER: UCASE_LETTER | LCASE_LETTER | SYMBOL

NAME: ("_"|LETTER) ("_"|LETTER|DIGIT)*

%import common.NUMBER -> NUMBER
%import common.WS_INLINE

%ignore WS_INLINE
%import common.WS
%ignore WS
'''
# %import common.CNAME -> NAME
# %import common.NUMBER -> NUMBER
# %import common.WS_INLINE
# 
# %ignore WS_INLINE
# %import common.WS
# %ignore WS
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
        if a == 'owlThing':
            return '<Class IRI="http://www.w3.org/2002/07/owl#Thing"/>'
        else:
            self.atomics.add(a)
            return self.to_flc(f'<Class abbreviatedIRI=":{a}"/>')

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
     
    def arole(self, items):
        d = items[0]
        try:
            d = f'r_{int(d)}'
        except:
            pass
        self.roles.add(d)
        return f'<ObjectProperty abbreviatedIRI=":{d}"/>'
    
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

class OWLXMLCTDTransformer(OWLXMLTransformer):
    def __init__(self):
        super().__init__()
     
    def arole(self, items):
        d = items[0]
        assert d in ['I','S'], 'Permitted operators are [I], [S]'
        d = f'r_{d}'
        self.roles.add(d)
        return f'<ObjectProperty abbreviatedIRI=":{d}"/>'
    
    def normalise_role_expression(self, items):
        assert len(items) > 1, 'Boxes and Diamonds cannot be empty'
        d = items[0]
        wff = items[1]
        return (d, wff)

def dstit_substitution(formulae):
    # Box substitution
    # For dstit agency, we transform into cstit agency by the following rule:
            # [a dstit p] = [a cstit p] & ~[]p
            # E.g. [1]p = [1]p & ~[]p

    boxes = []
    for i, ltr in enumerate(formulae):
        if ltr == '[' and formulae[i+1] != ']':
            # Find start and end indices of boxes
            st, end = i, formulae.index(']', i)+1
            boxes.insert(0, [st, end])

    for st, end in boxes:
        if formulae[end] == '(':
            wff_end = formulae.index(')', end)+1
            count = 1
            for j, c in enumerate(formulae[end+1:]):
                count += 1 if c == '(' else 0
                count -= 1 if c == ')' else 0
                if count == 0:
                    wff_end = end+j+2
                    break
        else: 
            try:
                wff_end = min(formulae.index(' ', end), formulae.index('.', end), formulae.index(')', end))
            except:
                wff_end = min(formulae.index(' ', end), formulae.index('.', end))

        orig = formulae[st:wff_end]
        wff = formulae[end: wff_end]
        replacement = f"({orig} & ~[]{wff})"

        formulae = formulae[:st] + formulae[wff_end:]   
        f = list(formulae)
        f.insert(st, replacement)
        formulae = ''.join(f)

    # Diamond substitution
    # For dstit agency, we transform into cstit agency by the following rule:
            # <a dstit p> = <a cstit p> v ~<>p
            # E.g. <1>p = <1>p v ~<>p

    diamonds = []
    for i, ltr in enumerate(formulae):
        if ltr == '<' and formulae[i+1] != '>':
            # Find start and end indices of diamonds
            st, end = i, formulae.index('>', i)+1
            diamonds.insert(0, [st, end])

    for st, end in diamonds:
        if formulae[end] == '(':
            wff_end = formulae.index(')', end)+1
            count = 1
            for j, c in enumerate(formulae[end+1:]):
                count += 1 if c == '(' else 0
                count -= 1 if c == ')' else 0
                if count == 0:
                    wff_end = end+j+2
                    break
        else: 
            try:
                wff_end = min(formulae.index(' ', end), formulae.index('.', end), formulae.index(')', end))
            except:
                wff_end = min(formulae.index(' ', end), formulae.index('.', end))

        orig = formulae[st:wff_end]
        wff = formulae[end: wff_end]
        replacement = f"({orig} v ~<>{wff})"

        formulae = formulae[:st] + formulae[wff_end:]  
        f = list(formulae)
        f.insert(st, replacement)
        formulae = ''.join(f)

    return formulae

def jp_substitution(formulae):
    # Replace [Ought]p with '[I]p & <S>~p'
    amendments = []
    inds = [[m.start(), m.end()] for m in re.finditer('\[Ought\]', formulae)]
    for st, end in inds:
        if formulae[end] == '(':
            wff_end = formulae.index(')', end)+1
        else:
            wff_end = min(formulae.index(' ', end), formulae.index('.', end), formulae.index(')', end))
        wff = formulae[end: wff_end]
        amendments.insert(0, [[st, end], wff_end, f"([I]{wff} & <S>~{wff})"])

    for inds, wff_end, replacement in amendments:
        formulae = formulae[:inds[0]] + formulae[wff_end:]  
        f = list(formulae)
        f.insert(inds[0], replacement)
        formulae = ''.join(f)

    # Replace <Ought>p with '<I>p v [S]~p'
    amendments = []
    inds = [[m.start(), m.end()] for m in re.finditer('<Ought>', formulae)]
    for st, end in inds:
        if formulae[end] == '(':
            wff_end = formulae.index(')', end)+1
        else:
            wff_end = min(formulae.index(' ', end), formulae.index('.', end), formulae.index(')', end))
        wff = formulae[end: wff_end]
        amendments.insert(0, [[st, end], wff_end, f"(<I>{wff} v [S]~{wff})"])

    for inds, wff_end, replacement in amendments:
        formulae = formulae[:inds[0]] + formulae[wff_end:]  
        f = list(formulae)
        f.insert(inds[0], replacement)
        formulae = ''.join(f)

    return formulae


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Convert Modeldown files into OWL.')
    parser.add_argument('source', type=Path,
                    help='input file')
    parser.add_argument('-o', '--output', type=Path, 
                    help='output file (default to input file stem + .owl')
    parser.add_argument('-l', '--logic', type=str,
                    help='name of logic (sdl, jp, cstit, dstit)')

    args = parser.parse_args()
    #print(args)
    
    if not args.output:
        args.output = args.source.with_suffix('.owl')
    
    #g = Path('grammars/modal.g').read_text()
    
    s = args.source.read_text()
    meta, formulae = re.split('----+', s)
    meta = meta.strip().split('\n')
    meta = {m[0].strip().lower():m[1].strip().lower() for m in [n.split(':') for n in meta]}

    name = 'test' if not args.output else args.output.name
    if not args.logic:
        if 'logic' in meta.keys():
            args.logic = meta['logic']
        else:
            print('No logic specified at command line or in file metadata, using SDL.')
    else:
        if 'logic' in meta.keys():
            if meta['logic'] == args.logic:
                print(f'You specified the logic ({args.logic}) in both file metadata and at the command line.')
            else:
                print(f'Overriding file metadata which specifies {meta["logic"]} for your command to use {args.logic}')

    if args.logic == 'dstit':
        formulae = dstit_substitution(formulae)
    
    if args.logic == 'jp':
        formulae = jp_substitution(formulae)

    parser = Lark(g, parser='lalr')
    tree = parser.parse(formulae)

    if args.logic == 'cstit' or args.logic == 'dstit':
        filename = str(args.output)
        transformer = OWLXMLTransformer()
        axioms = transformer.transform(tree)
        #print(f"|FLC| = {len(transformer.flc)}")

        grounding = ground_aaia('aaia', transformer.roles, transformer.flc)
        # grounding = ground_aaia('plain', transformer.roles, transformer.flc)
        axioms_aaiabig = axioms + grounding
        nrag = len(transformer.roles) - 1
        flcsize = len(transformer.flc)
        print(f'''{{'agents': {nrag}, 'flc': {flcsize}, 'non_aaia_axioms': {len(axioms)},'aaia_saturation': {nrag*len(transformer.flc)}}}''')
        #print(f"|AAIA Big Axiom Schema| = {len(axioms_aaiabig)}")
        cnames = transformer.atomics - transformer.declared
        ont = owlxml_ont(name, axioms_aaiabig, cnames, transformer.roles)
        if not args.output:
            print(ont)
        else:
            filename = str(args.output) 
            Path(f'{filename[:-4]}.owl').write_text(ont)

        # grounding = ground_aaia('aaia', transformer.roles, transformer.flc)
#         axioms_aaia = axioms + grounding
#         print(f"|AAIA Normal Axiom Schema| = {len(axioms_aaia)}")
#         cnames = transformer.atomics - transformer.declared
#         ont = owlxml_ont(name, axioms_aaia, cnames, transformer.roles)
#         if not args.output:
#             print(ont)
#         else:
#             filename = str(args.output) 
#             Path(f'{filename[:-4]}_aaia_b.xml').write_text(ont)
# 
#         grounding = ground_aaia('aaia_small', transformer.roles, transformer.flc)
#         axioms_aaiasmall = axioms + grounding
#         print(f"|AAIA Small Axiom Schema| = {len(axioms_aaiasmall)}")
#         cnames = transformer.atomics - transformer.declared
#         ont = owlxml_ont(name, axioms_aaiasmall, cnames, transformer.roles)
#         if not args.output:
#             print(ont)
#         else:
#             filename = str(args.output) 
#             Path(f'{filename[:-4]}_aaia_c.xml').write_text(ont)

    elif args.logic == 'jp':
        transformer = OWLXMLCTDTransformer()
        axioms = transformer.transform(tree)
        grounding = ground_ctd(transformer.roles, transformer.flc)
        print(f'''{{'directaxioms': {len(axioms)}, 'background':{len(grounding)}}}''')
        axioms.extend(grounding)
        cnames = transformer.atomics - transformer.declared
        ont = owlxml_ont(name, axioms, cnames, transformer.roles)
        if not args.output:
            print(ont)
        else:
            args.output.write_text(ont)

    elif args.logic == 'sdl':
        transformer = OWLXMLTransformer()
        axioms = transformer.transform(tree) 
        print(f'''{{'directaxioms': {len(axioms)}}}''' )      
        axioms.append('''<SubClassOf>
        <Class abbreviatedIRI="owl:Thing"/>
        <ObjectSomeValuesFrom>
            <ObjectProperty abbreviatedIRI=":r"/>
            <Class abbreviatedIRI="owl:Thing"/>
        </ObjectSomeValuesFrom>
        </SubClassOf>''')
        cnames = transformer.atomics - transformer.declared
        ont = owlxml_ont(name, axioms, cnames, transformer.roles)
        if not args.output:
            print(ont)
        else:
            args.output.write_text(ont)

    else:
        print('I do not know how to translate {args.logic}.')
