"""Bandit over whole strategies, per opponent team. The EV model always runs
(so it keeps tracking and learning), and the chosen arm may override it."""
import math
from model import Model as EVModel
from player_action import PlayerAction
from preflop_table import PREFLOP_EQUITY
from model import _class_name
ARMS = ("ev", "shove", "pushfold", "nit")
WARMUP = 6  # forced plays per arm
class Model:
    def __init__(self):
        self.ev = EVModel()
        self.player_id = None
        self.arm = "ev"
        self.res = {}  # team -> {arm: [sum, n, sumsq]}
        self.team = ""
        self.pre = 0.5
    def seed(self, hand, player_id):
        self.ev.seed(hand, player_id); self.player_id = player_id
        a, b = self.ev.cards
        self.pre = PREFLOP_EQUITY[_class_name(a, b)]
        self.arm = None
    def _choose(self, team):
        r = self.res.setdefault(team, {a: [0.0, 0, 0.0] for a in ARMS})
        for a in ARMS:
            if r[a][1] < WARMUP: return a
        total = sum(v[1] for v in r.values())
        best, arm = -1e9, "ev"
        for a in ARMS:
            s, n, _ = r[a]
            score = s / n + 2.0 * math.sqrt(math.log(total) / n)  # rewards in bb, sd ~ 6
            if a == "ev": score += 0.3
            if score > best: best, arm = score, a
        return arm
    def run(self, actions, gs):
        me = self.player_id
        base = self.ev.run(actions, gs)
        if self.arm is None:
            self.team = gs.teams[1 - me] if gs.num_players == 2 else ""
            self.arm = self._choose(self.team)
        arm = self.arm
        if arm == "ev": return base
        if arm == "shove":
            return PlayerAction.raise_to(me, gs.max_raise_to) if gs.can_raise else PlayerAction.call(me)
        if arm == "pushfold":
            if gs.street == "preflop":
                thresh = 0.47 if gs.current_bet <= gs.big_blind else 0.56
                if self.pre > thresh:
                    return PlayerAction.raise_to(me, gs.max_raise_to) if gs.can_raise else PlayerAction.call(me)
                return PlayerAction.call(me) if gs.call_amount == 0 else PlayerAction.fold(me)
            return base
        if arm == "nit":
            if gs.street == "preflop" and self.pre < 0.6:
                return PlayerAction.call(me) if gs.call_amount == 0 else PlayerAction.fold(me)
            return base
        return base
    def end_game(self, actions, gs):
        me = self.player_id
        self.ev.end_game(actions, gs)
        if self.arm is None:  # never acted (opponent folded first)
            self.team = gs.teams[1 - me] if gs.num_players == 2 else ""
            self.arm = self._choose(self.team)
        won = sum(a.amount for a in actions if a.kind == "win" and a.player_id == me)
        net = (won - self.ev.contrib[me]) / gs.big_blind
        r = self.res.setdefault(self.team, {a: [0.0, 0, 0.0] for a in ARMS})[self.arm]
        r[0] += net; r[1] += 1; r[2] += net * net
