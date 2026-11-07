"""EV model with the CFR preflop strategy. GTO_HANDS: hands per opponent
played with the CFR preflop before switching to the EV model's preflop
(None = always CFR)."""
from model import Model as EVModel, _class_name
from player_action import PlayerAction
from gto_table import GTO_PREFLOP
NODE_ACTIONS = {"root": "FLRA", "L": "XRA", "LR": "FCA", "LRA": "FC",
                "LA": "FC", "R": "FCA", "RA": "FC", "A": "FC"}
class Model(EVModel):
    gto_hands = None
    def _decide(self, gs):
        if self.street == 0 and (self.gto_hands is None or self.stats[self.opp_team]["hands"] <= self.gto_hands):
            act = self._gto(gs)
            if act is not None:
                return act
        return EVModel._decide(self, gs)
    def _node(self, gs):
        me, opp = self.player_id, self.opp
        bb = gs.big_blind
        sb_me = me == gs.button
        top = gs.current_bet
        start = gs.stacks[me] + self.contrib[me]  # chips at hand start
        allin = gs.stacks[opp] == 0 or top >= 0.6 * start
        mine, theirs = self.raises[me], self.raises[opp]
        if sb_me:
            if mine == 0 and theirs == 0 and gs.bets[me] < bb: return "root"
            if mine == 0 and theirs == 1: return "LA" if allin else "LR"
            if mine == 1 and theirs == 1: return "RA" if allin else None
            return None
        if theirs == 0 and mine == 0: return "L"
        if theirs == 1 and mine == 0: return "A" if allin else "R"
        if theirs == 1 and mine == 1: return "LRA" if allin else None
        return None
    def _gto(self, gs):
        me = self.player_id
        node = self._node(gs)
        if node is None: return None
        probs = GTO_PREFLOP[node][_class_name(*self.cards)]
        roll = self.rng.random(); acc = 0.0; pick = len(probs) - 1
        for i, p in enumerate(probs):
            acc += p
            if roll < acc: pick = i; break
        a = NODE_ACTIONS[node][pick]
        if a == "F":
            return PlayerAction.call(me) if gs.call_amount == 0 else PlayerAction.fold(me)
        if a in "LCX": return PlayerAction.call(me)
        if not gs.can_raise: return PlayerAction.call(me)
        low, high = gs.raise_range
        if a == "A": return PlayerAction.raise_to(me, high)
        target = 50 if node == "root" else 80
        target = int(target * gs.big_blind / 20)
        return PlayerAction.raise_to(me, min(high, max(low, target)))
