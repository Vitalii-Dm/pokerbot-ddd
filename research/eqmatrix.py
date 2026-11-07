import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import random, sys, pickle
from multiprocessing import Pool
sys.path.insert(0,ROOT)
from handeval import evaluate, RANK_CHARS
COMBOS=[(a,b) for a in range(52) for b in range(a+1,52)]
def cname(a,b):
    ra,rb=a>>2,b>>2; hi,lo=max(ra,rb),min(ra,rb)
    if hi==lo: return RANK_CHARS[hi]*2
    return RANK_CHARS[hi]+RANK_CHARS[lo]+('s' if (a&3)==(b&3) else 'o')
NAMES=sorted({cname(a,b) for a,b in COMBOS})
IDX={n:i for i,n in enumerate(NAMES)}
by={n:[] for n in NAMES}
for a,b in COMBOS: by[cname(a,b)].append((a,b))
S=1200
def row(i):
    rng=random.Random(i); out=[]
    for j in range(len(NAMES)):
        pairs=[(x,y) for x in by[NAMES[i]] for y in by[NAMES[j]] if len({*x,*y})==4]
        if not pairs: out.append((0.5,0)); continue
        won=0.0
        for _ in range(S):
            x,y=rng.choice(pairs)
            rest=[c for c in range(52) if c not in x and c not in y]
            board=rng.sample(rest,5)
            m=evaluate(list(x)+board); t=evaluate(list(y)+board)
            won+=1 if m>t else 0.5 if m==t else 0
        out.append((won/S,len(pairs)))
    return out
if __name__=='__main__':
    with Pool(10) as p: rows=p.map(row,range(len(NAMES)))
    pickle.dump((NAMES,rows),open('eqmatrix.pkl','wb'))
    print(len(NAMES), rows[IDX['AA']][IDX['KK']], rows[IDX['72o']][IDX['AA']])
