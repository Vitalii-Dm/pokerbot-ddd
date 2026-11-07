import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import random, sys
sys.path.insert(0,ROOT)
from card_utils import full_deck
from engine import play_hand
import model, sparbots
from arena.dummies import DUMMIES
from collections import defaultdict
opp=sys.argv[1]; N=int(sys.argv[2]); show=int(sys.argv[3])
m=model.Model(); o=DUMMIES[opp](seed=1) if opp in DUMMIES else getattr(sparbots,opp)(seed=1)
by=defaultdict(float); cnt=defaultdict(int); big=[]
for i in range(N):
    deck=full_deck(); random.Random(9000+i).shuffle(deck)
    for seat in (0,1):
        models=[m,o] if seat==0 else [o,m]
        r=play_hand(models,deck,[500,500],button=i%2,teams=['A','B'] if seat==0 else ['B','A'])
        acts=[a for a in r.actions if a.kind in('fold','call','raise')]
        last=r.actions[-1]
        folded = any(a.kind=='fold' for a in r.actions)
        who_fold = [a.player_id for a in r.actions if a.kind=='fold']
        ending = ('I fold' if who_fold and who_fold[0]==seat else 'opp folds' if who_fold else 'showdown')
        nb=sum(1 for a in r.actions if a.kind=='reveal_card' and a.player_id==-1)
        st={0:'pre',3:'flop',4:'turn',5:'river'}[nb]
        key=(('btn' if i%2==seat else 'bb'), ending, st if ending!='showdown' else '')
        by[key]+=r.net[seat]/20; cnt[key]+=1
        w=lambda p:'ME' if p==seat else 'op' if p>=0 else 'D'
        big.append((r.net[seat], i, 'btn' if i%2==seat else 'bb', [str(c) for c in r.hands[seat]], [str(c) for c in r.hands[1-seat]],
           ' '.join(f"{w(a.player_id)}:{a.kind[0]}{a.amount or ''}{a.card or ''}" for a in r.actions if a.kind!='win' and not (a.kind=='reveal_card' and a.player_id>=0))))
tot=sum(by.values())
print(f"total {tot/N/2*100:+.1f} bb/100")
for k in sorted(by, key=lambda k: by[k]): print(f"  {str(k):40s} n={cnt[k]:4d} {by[k]:+8.1f}bb  avg {by[k]/cnt[k]:+.2f}")
big.sort()
for b in big[:show]: print(b)
