import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
"""Full round robin: python field.py N seed entrant1 entrant2 ...  (file:mod or sparbot/dummy names)"""
import sys, itertools, time
from multiprocessing import Pool
import league
if __name__=='__main__':
    N=int(sys.argv[1]); seed=int(sys.argv[2]); ents=sys.argv[3:]
    jobs=[(a,b,N,seed) for a,b in itertools.combinations(ents,2)]
    slow=('SmartEq','LAG','Overbettor','equity')
    jobs.sort(key=lambda j: -sum(x in slow or x.startswith('file:') for x in j[:2]))
    t=time.time()
    with Pool(10) as p: res=p.map(league.job,jobs,chunksize=1)
    M={e:{} for e in ents}
    for a,b,mu,ci in res: M[a][b]=mu; M[b][a]=-mu
    rank=sorted(ents,key=lambda e:-sum(M[e].values()))
    short=lambda e:e.replace('file:','')[:9]
    print(f"{'entrant':12s} {'mean':>7s} | "+" ".join(f"{short(e):>9s}" for e in rank))
    for e in rank:
        print(f"{short(e):12s} {sum(M[e].values())/(len(ents)-1):+7.0f} | "+" ".join(f"{M[e][o]:+9.0f}" if o in M[e] else f"{'-':>9s}" for o in rank))
    print(f"N={N} deals x2 seats, {time.time()-t:.0f}s")
