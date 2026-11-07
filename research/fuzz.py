import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import random, sys, traceback
sys.path.insert(0,ROOT)
from card_utils import full_deck
from engine import play_hand
import model, sparbots
from arena.dummies import DUMMIES
errs=[]; mism=[]; faults=[]
def wrap(name):
    orig=getattr(model.Model,name)
    def w(self,*a,**k):
        try: return orig(self,*a,**k)
        except Exception: errs.append((name,traceback.format_exc())); raise
    setattr(model.Model,name,w)
for n in ['_start','_observe','_learn_action','_narrow','_abs_pct','_learn_showdown','_learn_realize','_simulate','_decide','_decide_multiway','end_game']: wrap(n)
rng=random.Random(42)
opps=list(DUMMIES.values())+[sparbots.Maniac,sparbots.SmallBettor,sparbots.Stealer]
for t in range(3000):
    n = 2 if t < 2000 else rng.choice([3,4,5,6])
    me = model.Model()
    seats=[me]+[rng.choice(opps)(seed=t+i) if rng.random()<0.8 else model.Model() for i in range(n-1)]
    rng.shuffle(seats)
    sb=rng.choice([1,5,10,10,25]); bb=sb*rng.choice([1,2,2,3])
    stacks=[rng.choice([0,1,sb,bb-1 if bb>1 else 1,bb,3*bb,rng.randint(1,3000),500,500]) for _ in range(n)]
    stacks=[max(1,s) for s in stacks]
    deck=full_deck(); rng.shuffle(deck)
    for hand in range(rng.randint(1,4)):
        try:
            r=play_hand(seats,deck,stacks,button=hand%n,small_blind=sb,big_blind=bb,teams=[f"t{i}" for i in range(n)])
        except Exception as e:
            print("engine refused", e); break
        for i,s in enumerate(seats):
            if isinstance(s, model.Model) and i in r.faults: faults.append(r.faults[i])
        rng.shuffle(deck)
print("hands done; errors", len(errs), "faults", len(faults))
for e in errs[:2]: print(e[0]); print(e[1][-800:])
for f in faults[:3]: print(f)
