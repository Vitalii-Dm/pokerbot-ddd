"""Learns, per opponent, which preflop style earns more against them:
the EV model's exploitative preflop or the CFR (GTO) preflop. Postflop is
always the EV model. UCB over per-hand results in big blinds."""
import math
import sp_gto
from model import Model as EVModel
WARMUP = 10
C = 1.0
class Model(sp_gto.Model):
    learn_realize = True
    def __init__(self):
        super().__init__()
        self.arm_stats = {}
        self.arm = "ev"
    def seed(self, hand, player_id):
        super().seed(hand, player_id)
        self.arm = None
    def _pick(self, team):
        r = self.arm_stats.setdefault(team, {"ev": [0.0, 0], "gto": [0.0, 0]})
        for a in ("gto", "ev"):
            if r[a][1] < WARMUP: return a
        tot = r["ev"][1] + r["gto"][1]
        score = {a: r[a][0] / r[a][1] + C * math.sqrt(math.log(tot) / r[a][1]) for a in r}
        return max(score, key=score.get)
    def _decide(self, gs):
        if self.arm is None: self.arm = self._pick(self.opp_team)
        if self.street == 0 and self.arm == "gto":
            act = self._gto(gs)
            if act is not None: return act
        return EVModel._decide(self, gs)
    def end_game(self, actions, gs):
        super().end_game(actions, gs)
        try:
            if self.n != 2: return
            if self.arm is None: return  # never acted: no information
            me = self.player_id
            won = sum(a.amount for a in actions if a.kind == "win" and a.player_id == me)
            net = (won - self.contrib[me]) / gs.big_blind
            r = self.arm_stats.setdefault(self.opp_team, {"ev": [0.0, 0], "gto": [0.0, 0]})[self.arm]
            r[0] += net; r[1] += 1
        except Exception:
            pass
