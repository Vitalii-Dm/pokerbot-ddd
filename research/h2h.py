import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import sys
from multiprocessing import Pool
import league
if __name__=='__main__':
    a,b,N=sys.argv[1],sys.argv[2],int(sys.argv[3])
    with Pool(10) as p: res=p.map(league.job,[(a,b,N//10,100+s) for s in range(10)])
    mus=[r[2] for r in res]; m=sum(mus)/10; sd=(sum((x-m)**2 for x in mus)/9)**.5
    print(f"{a} vs {b}: {m:+.1f} ± {1.96*sd/10**.5:.1f} bb/100 over {N} deals")
