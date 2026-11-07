import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
"""python league.py ROUND.json N  — ROUND.json: {"name": {overrides}} ; '_base' key optional source file."""
import json, sys, random, importlib, itertools, time
from multiprocessing import Pool

sys.path.insert(0, ROOT)
POOL=['tight','random','call','Maniac','MinRaiser','Trapper','LAG','SmartEq','SmallBettor','Overbettor','Stealer','Honest','NaiveEq','file:sp_shove','file:sp_pushfold','file:sp_bandit']
def make_variants(spec):
    src=open(spec.pop('_base', _os.path.join(ROOT,'model.py'))).read()
    for name, over in spec.items():
        if name.startswith('file:'): continue
        lines=[f"{k} = {v!r}" if not isinstance(v,str) or not v.startswith('=') else f"{k} {v}" for k,v in over.items()]
        open(f"{HERE}/v_{name}.py",'w').write(src+"\n\n# variant overrides\n"+"\n".join(lines)+"\n")
    return list(spec)
def mk(spec):
    from arena.dummies import DUMMIES
    import sparbots
    if spec in DUMMIES: return DUMMIES[spec](seed=1)
    if spec.startswith('v:'): return importlib.import_module('v_'+spec[2:]).Model()
    if spec.startswith('file:'): return importlib.import_module(spec[5:]).Model()
    return getattr(sparbots, spec)(seed=1)
def job(args):
    a_spec,b_spec,N,seed=args
    from card_utils import full_deck
    from engine import play_hand
    a=mk(a_spec); b=mk(b_spec); nets=[]
    for i in range(N):
        deck=full_deck(); random.Random(seed*100000+i).shuffle(deck); tot=0
        for seat in (0,1):
            models=[a,b] if seat==0 else [b,a]
            r=play_hand(models,deck,[500,500],button=i%2,teams=['A','B'] if seat==0 else ['B','A'])
            tot+=r.net[seat]
        nets.append(tot/2/20)
    mu=sum(nets)/N; sd=(sum((x-mu)**2 for x in nets)/(N-1))**.5
    return a_spec,b_spec,mu*100,1.96*sd/N**.5*100
if __name__=='__main__':
    spec=json.load(open(sys.argv[1])); N=int(sys.argv[2]); seed=int(sys.argv[3]) if len(sys.argv)>3 else 1
    names=['v:'+n if not n.startswith('file:') else n for n in make_variants(spec)]
    jobs=[(a,b,N,seed) for a,b in itertools.combinations(names,2)]+[(a,o,N,seed) for a in names for o in POOL]
    jobs.sort(key=lambda j: 0 if j[1] in ('SmartEq','LAG') else 1)
    t=time.time()
    with Pool(10) as p: res=p.map(job,jobs,chunksize=1)
    h2h={n:{} for n in names}; pool={n:{} for n in names}
    for a,b,mu,ci in res:
        if b in names: h2h[a][b]=(mu,ci); h2h[b][a]=(-mu,ci)
        else: pool[a][b]=(mu,ci)
    print(f"{'variant':18s} {'H2H sum':>8s} {'pool mean':>9s} {'TOTAL':>8s}  | " + " ".join(f"{n[-8:]:>8s}" for n in names))
    rows=[]
    for n in names:
        hs=sum(v[0] for v in h2h[n].values()); pm=sum(v[0] for v in pool[n].values())/len(POOL)
        rows.append((hs+pm*len(POOL),n,hs,pm))
    for tot,n,hs,pm in sorted(rows,reverse=True):
        cells=" ".join(f"{h2h[n][m][0]:+8.0f}" if m in h2h[n] else f"{'-':>8s}" for m in names)
        print(f"{n:18s} {hs:+8.0f} {pm:+9.0f} {tot:+8.0f}  | {cells}")
    print("pool detail:")
    for n in names: print(f"  {n:16s} "+" ".join(f"{o[:6]}:{pool[n][o][0]:+.0f}" for o in POOL))
    print(f"(N={N} deals x2 seats, h2h CI ~±{sum(v[1] for d in h2h.values() for v in d.values())/max(1,sum(len(d) for d in h2h.values())):.0f}; {time.time()-t:.0f}s)")
