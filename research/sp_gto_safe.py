"""CFR preflop, but deviate to the EV model's choice when it is clearly
better (safe exploitation). Learned realisation on."""
import sp_gto
from model import Model as EVModel
from player_action import PlayerAction
MARGIN_BB = 0.75
class Model(sp_gto.Model):
    learn_realize = True
    def _decide(self, gs):
        if self.street != 0:
            return EVModel._decide(self, gs)
        best = EVModel._decide(self, gs)
        g = self._gto(gs)
        if g is None or not self.options:
            return best
        def ev_of(act):
            evs = [ev for ev, kind, amt in self.options if kind == act.kind]
            if not evs:
                return None
            if act.kind == "raise":
                return max((-abs(amt - act.amount), ev) for ev, kind, amt in self.options if kind == "raise")[1]
            return evs[0]
        if g.kind == "fold" and gs.call_amount == 0:
            g = PlayerAction.call(self.player_id)
        ge = ev_of(g)
        top = max(ev for ev, _, _ in self.options)
        if ge is None or top - ge > MARGIN_BB * gs.big_blind:
            return best
        return g
