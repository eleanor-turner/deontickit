import subprocess
import ast
from pathlib import Path
from timeit import timeit
from pprint import pprint

import agate

konp = '../../Konclude/Binaries/Konclude'
translator = '../../translate.py'

timeout = 60*5

def klassify(p):
    subprocess.run([konp,  'classification', '-w', 'AUTO', '-i', md, '-o', md.with_stem(f'{md.stem}_res')], timeout=timeout)

res = dict()
    
for md in Path('.').glob('*.txt'):
    try:
        stats = subprocess.run(['python',  translator, md], capture_output=True, text='True', timeout=30).stdout
        stats = ast.literal_eval(stats)
        print(md.stem)
        print('\t',stats)
        res[md.stem] = stats
    except subprocess.TimeoutExpired:
        res[md.stem] = {'output':'', 'time':'parser timedout'}

for md in Path('.').glob('*.owl'):
    try:
        time = timeit(lambda:klassify(md), number=1)
    #print(md)
        res[md.stem]['time'] = round(time,2)
    except subprocess.TimeoutExpired:
        res[md.stem]['time'] = 'timedout'
for md in Path('.').glob('*_res.owl'):
     md.unlink()

for md in Path('.').glob('*.owl'):
    md.unlink() 
    
csv = list()
print(res)
for k,v in res.items():
    v['logic'] = 'jpl'
    v['file'] = k
    csv.append(v)
t = agate.Table.from_object(csv)
t.to_csv('jpl_results.csv')

