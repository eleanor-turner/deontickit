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
        stats = subprocess.run(['python',  translator, md], capture_output=True, text='True', timeout=60).stdout
        stats = ast.literal_eval(stats)
        print(md.stem, stats)
        res[md.stem] = stats 
        #print(res)
    except subprocess.TimeoutExpired:
        res[md.stem] = {'output':'', 'parser time':'timedout'}

for md in Path('.').glob('*.owl'):
    try:
        time = timeit(lambda:klassify(md), number=1)
    #print(md)
        res[md.stem]['time'] = round(time,2)
    except subprocess.TimeoutExpired:
        res[md.stem]['time'] = 'timedout'
# clean up first...for debugging.
for md in Path('.').glob('*.owl'):
    md.unlink()         
pprint(res)
csv = list()
print(res)
for k,v in res.items():
    v['logic'] = 'sdl'
    v['file'] = k
    csv.append(v)
t = agate.Table.from_object(csv)
t.to_csv('sdl_results.csv')