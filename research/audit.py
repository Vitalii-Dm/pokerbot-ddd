import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import random, sys, traceback, importlib
sys.path.insert(0,ROOT)
from card_utils import full_deck
from engine import play_hand
import model, sparbots
from arena.dummies import DUMMIES
errs=[]; mism=[]
def wrap(name):
    orig=getattr(model.Model,name)
    def w(self,*a,**k):
        try: return orig(self,*a,**k)
        except Exception: errs.append((name,traceback.format_exc())); raise
    setattr(model.Model,name,w)
for n in ['_start','_observe','_learn_action','_narrow','_abs_pct','_learn_showdown','_simulate','_decide_multiway','end_game']: wrap(n)
od=model.Model._decide
def dec(self,gs):
    st=("preflop","flop","turn","river")[self.street]
    if self.bets!=list(gs.bets) or sum(self.contrib)!=gs.pot or len(self.board)!=len(gs.board) or st!=gs.street:
        mism.append((self.bets,list(gs.bets),sum(self.contrib),gs.pot,st,gs.street))
    try: return od(self,gs)
    except Exception: errs.append(('_decide',traceback.format_exc())); raise
model.Model._decide=dec
opps=list(DUMMIES)+['PushFold','Maniac','SmartEq','MinRaiser','self']
for spec in opps:
    a=model.Model(); b=model.Model() if spec=='self' else (DUMMIES[spec](seed=1) if spec in DUMMIES else getattr(sparbots,spec)(seed=1))
    N=100 if spec in ('equity','SmartEq') else 300
    e0,m0=len(errs),len(mism)
    for i in range(N):
        deck=full_deck(); random.Random(5000+i).shuffle(deck)
        for seat in (0,1):
            models=[a,b] if seat==0 else [b,a]
            play_hand(models,deck,[500,500],button=i%2,teams=['A','B'] if seat==0 else ['B','A'])
    print(spec,'errors',len(errs)-e0,'mismatches',len(mism)-m0,flush=True)
# multiway smoke
ms=[model.Model(),DUMMIES['tight'](seed=1),DUMMIES['random'](seed=2)]
e0=len(errs)
for i in range(100):
    deck=full_deck(); random.Random(i).shuffle(deck)
    play_hand(ms,deck,[500]*3,button=i%3,teams=['A','B','C'])
print('multiway errors',len(errs)-e0)
if errs: print(errs[0][0]); print(errs[0][1])
if mism: print(mism[:3])
