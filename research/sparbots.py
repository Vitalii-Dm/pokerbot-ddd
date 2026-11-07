import random
from card_utils import evaluate
from player_action import PlayerAction
from preflop_table import PREFLOP_EQUITY
from arena.dummies import _Bot, EquityBot
R="23456789TJQKA"
def pre_eq(hand):
    a,b=sorted(hand,key=lambda c:c.value,reverse=True)
    n=a.rank+b.rank+("" if a.rank==b.rank else ("s" if a.suit==b.suit else "o"))
    return PREFLOP_EQUITY[n]
class PushFold(_Bot):
    """Shoves top ~60% from SB, calls shoves with top ~35%; postflop equity."""
    def run(self, actions, gs):
        me=self.player_id; e=pre_eq(self.hand)
        if gs.street=="preflop":
            if gs.current_bet<=gs.big_blind and gs.call_amount>0:
                return self._raise_to(gs, gs.max_raise_to) if e>0.45 else self._check_or_fold(gs)
            if gs.call_amount==0:
                return self._raise_to(gs, gs.max_raise_to) if e>0.55 else PlayerAction.call(me)
            return PlayerAction.call(me) if e>0.56 else PlayerAction.fold(me)
        return self._check_or_fold(gs)
class Maniac(_Bot):
    """Bets pot on every street, re-raises 40%, calls the rest."""
    def __init__(self, seed=None): super().__init__(seed); self.rng=random.Random(seed)
    def run(self, actions, gs):
        if gs.can_raise and (gs.call_amount==0 or self.rng.random()<0.4):
            return self._raise_to(gs, gs.current_bet+gs.pot)
        return PlayerAction.call(self.player_id)
class SmartEq(EquityBot):
    """EquityBot with better preflop and value sizing, 300 samples."""
    def __init__(self, seed=None): super().__init__(seed, samples=300)
    def run(self, actions, gs):
        me=self.player_id
        eq=self.equity(list(gs.board),1)
        if eq>0.65 and gs.can_raise: return self._raise_to(gs, gs.current_bet+gs.pot*0.75)
        if gs.call_amount==0:
            if eq>0.5 and gs.can_raise and self.rng.random()<0.5: return self._raise_to(gs, gs.current_bet+gs.pot*0.5)
            return PlayerAction.call(me)
        return PlayerAction.call(me) if eq>gs.pot_odds+0.05 else PlayerAction.fold(me)
class MinRaiser(_Bot):
    """Min-raises any time it has a pair or better / good preflop, else calls small bets."""
    def run(self, actions, gs):
        me=self.player_id
        if gs.street=="preflop": strong=pre_eq(self.hand)>0.55
        else: strong=evaluate(self.hand+list(gs.board))[0]>=1
        if strong and gs.can_raise: return self._raise_to(gs, gs.min_raise_to)
        if gs.call_amount==0 or gs.pot_odds<0.3: return PlayerAction.call(me)
        return PlayerAction.fold(me)

class Trapper(_Bot):
    """Checks/calls strong hands until the river, then shoves; folds weak to bets."""
    def run(self, actions, gs):
        me=self.player_id
        if gs.street=="preflop":
            e=pre_eq(self.hand)
            if e>0.6 and gs.can_raise and gs.current_bet<=gs.big_blind: return self._raise_to(gs, 3*gs.big_blind)
            if e>0.45 or gs.call_amount==0: return PlayerAction.call(me) if e>0.45 or gs.call_amount==0 else PlayerAction.fold(me)
            return PlayerAction.fold(me)
        cat=evaluate(self.hand+list(gs.board))[0]
        if cat>=2:
            if gs.street=="river" and gs.can_raise: return self._raise_to(gs, gs.max_raise_to)
            return PlayerAction.call(me)
        if cat==1 and gs.pot_odds<0.35: return PlayerAction.call(me)
        return self._check_or_fold(gs)
class LAG(EquityBot):
    """Loose-aggressive: equity bot that bluffs 35% when checked to and 3-bets light."""
    def __init__(self, seed=None): super().__init__(seed, samples=200)
    def run(self, actions, gs):
        me=self.player_id
        eq=self.equity(list(gs.board),1)
        roll=self.rng.random()
        if gs.can_raise and (eq>0.6 or (roll<0.35 and gs.call_amount==0) or (roll<0.15)):
            return self._raise_to(gs, gs.current_bet+gs.pot*0.8)
        if gs.call_amount==0: return PlayerAction.call(me)
        return PlayerAction.call(me) if eq>gs.pot_odds else PlayerAction.fold(me)

class SmallBettor(_Bot):
    """Bets a third of the pot whenever checked to; min-raises preflop always; calls bets with any pair."""
    def run(self, actions, gs):
        me=self.player_id
        if gs.call_amount==0 and gs.can_raise: return self._raise_to(gs, gs.current_bet+max(gs.big_blind, gs.pot//3))
        if gs.street=="preflop":
            if gs.can_raise and gs.current_bet<=gs.big_blind: return self._raise_to(gs, gs.min_raise_to)
            return PlayerAction.call(me) if pre_eq(self.hand)>0.5 or gs.pot_odds<0.25 else PlayerAction.fold(me)
        cat=evaluate(self.hand+list(gs.board))[0]
        return PlayerAction.call(me) if cat>=1 or gs.pot_odds<0.2 else PlayerAction.fold(me)
class Overbettor(EquityBot):
    """Overbets 2x pot with strong equity and as a 25% bluff; otherwise check/fold, calls with equity."""
    def __init__(self, seed=None): super().__init__(seed, samples=200)
    def run(self, actions, gs):
        me=self.player_id; eq=self.equity(list(gs.board),1)
        if gs.can_raise and (eq>0.7 or (eq<0.3 and self.rng.random()<0.25)):
            return self._raise_to(gs, gs.current_bet+2*gs.pot)
        if gs.call_amount==0: return PlayerAction.call(me)
        return PlayerAction.call(me) if eq>gs.pot_odds+0.1 else PlayerAction.fold(me)
class Stealer(_Bot):
    """Raises 3x every preflop spot, c-bets half pot on flop always, gives up after unless pair."""
    def run(self, actions, gs):
        me=self.player_id
        if gs.street=="preflop":
            if gs.can_raise and gs.raise_range and gs.current_bet<=3*gs.big_blind: return self._raise_to(gs, 3*gs.current_bet)
            return PlayerAction.call(me) if pre_eq(self.hand)>0.55 else self._check_or_fold(gs)
        cat=evaluate(self.hand+list(gs.board))[0]
        if gs.street=="flop" and gs.call_amount==0 and gs.can_raise: return self._raise_to(gs, gs.pot//2)
        if cat>=1: return PlayerAction.call(me)
        return self._check_or_fold(gs)

class Honest(EquityBot):
    """PyPokerEngine's HonestPlayer: call if win rate >= 1/players, else fold."""
    def __init__(self, seed=None): super().__init__(seed, samples=300)
    def run(self, actions, gs):
        eq=self.equity(list(gs.board),1)
        if eq>=0.5 or gs.call_amount==0: return PlayerAction.call(self.player_id)
        return PlayerAction.fold(self.player_id)
class NaiveEq(EquityBot):
    """Gongsta/Poker-AI naive equity: eq>=.5 -> bet 10bb (or call), else check/fold."""
    def __init__(self, seed=None): super().__init__(seed, samples=300)
    def run(self, actions, gs):
        me=self.player_id; eq=self.equity(list(gs.board),1)
        if gs.call_amount==0:
            return self._raise_to(gs, gs.current_bet+10*gs.big_blind) if eq>=0.5 else PlayerAction.call(me)
        return PlayerAction.call(me) if eq>=0.5 else PlayerAction.fold(me)
