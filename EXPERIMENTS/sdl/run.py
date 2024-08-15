import subprocess
import ast
from pathlib import Path
from timeit import timeit
from pprint import pprint

konp = '../../Konclude/Binaries/Konclude'
translator = '../../translate.py'

timeout = 60*5

def klassify(p):
    subprocess.run([konp,  'classification', '-w', 'AUTO', '-i', md, '-o', md.with_stem(f'{md.stem}_res')], timeout=timeout)

res = dict()

# clean up first...for debugging.
for md in Path('.').glob('*.owl'):
    md.unlink() 
    
for md in Path('.').glob('*.txt'):
    stats = subprocess.run(['python',  translator, md], capture_output=True, text='True').stdout
    print('stats',stats)
    stats = ast.literal_eval(stats)
    print(md.stem, stats)
    res[md.stem] = stats 
    #print(res)

for md in Path('.').glob('*.owl'):
    try:
        time = timeit(lambda:klassify(md), number=1)
    #print(md)
        res[md.stem]['time'] = time
    except subprocess.TimeoutExpired:
        res[md.stem]['time'] = 'timedout'
        
pprint(res)