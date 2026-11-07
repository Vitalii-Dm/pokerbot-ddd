import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
"""python bench.py VARIANT_JSON N opp1,opp2,...  -> per-opponent bb/100 for model with overrides."""
import random, sys, json, importlib
from multiprocessing import Pool
sys.path.insert(0,ROOT); sys.path.insert(0,HERE)
def mk(spec, over=None):
    from arena.dummies import DUMMIES
    import sparbots
    if spec in DUMMIES: return DUMMIES[spec](seed=1)
    if spec.startswith('mod:'):
        m=importlib.import_module(spec[4:])
        return m.Model()
    return getattr(sparbots, spec)(seed=1)
def job(args):
    over, opp, N, modname = args
    m=importlib.import_module(modname)
    for k,v in over.items(): setattr(m,k,v)
    from card_utils import full_deck
    from engine import play_hand
    a=m.Model(); b=mk(opp)
    nets=[]
    for i in range(N):
        deck=full_deck(); random.Random(777+i).shuffle(deck); tot=0
        for seat in (0,1):
            models=[a,b] if seat==0 else [b,a]
            r=play_hand(models,deck,[500,500],button=i%2,teams=['A','B'] if seat==0 else ['B','A'])
            tot+=r.net[seat]
        nets.append(tot/2/20)
    mu=sum(nets)/N; sd=(sum((x-mu)**2 for x in nets)/(N-1))**.5
    return opp, mu*100, 1.96*sd/N**.5*100
if __name__=='__main__':
    over=json.loads(sys.argv[1]); N=int(sys.argv[2]); opps=sys.argv[3].split(',')
    modname=sys.argv[4] if len(sys.argv)>4 else 'model'
    with Pool(len(opps)) as p: res=p.map(job,[(over,o,N,modname) for o in opps])
    tot=0
    for o,mu,ci in res: print(f"  {o:14s} {mu:+7.1f} ± {ci:5.1f}"); tot+=mu
    print(f"  {'MEAN':14s} {tot/len(res):+7.1f}   {sys.argv[1]}")
