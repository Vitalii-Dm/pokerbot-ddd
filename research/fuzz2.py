import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
# tracker-vs-engine mismatch check under short stacks (heads-up)
import random, sys
sys.path.insert(0,ROOT)
from card_utils import full_deck
from engine import play_hand
import model
from arena.dummies import DUMMIES
mism=[0,0]
od=model.Model._decide
def dec(self,gs):
    mism[1]+=1
    if self.bets!=list(gs.bets) or sum(self.contrib)!=gs.pot: mism[0]+=1
    return od(self,gs)
model.Model._decide=dec
rng=random.Random(1)
for t in range(3000):
    a=model.Model(); b=rng.choice(list(DUMMIES.values()))(seed=t)
    st=[rng.choice([3,10,15,19,20,25,40,500,1500]) for _ in range(2)]
    deck=full_deck(); rng.shuffle(deck)
    play_hand([a,b] if t%2 else [b,a],deck,st,button=rng.randint(0,1))
print("decisions",mism[1],"mismatches",mism[0])
