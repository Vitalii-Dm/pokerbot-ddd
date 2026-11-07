# Team ddd — heads-up no-limit hold'em bot

Our entry for the [Manchester AI Society poker bot hackathon](https://poker-arena-site.vercel.app/#/)
(engine forked from [Manchester-AI-Society/poker_bot](https://github.com/Manchester-AI-Society/poker_bot);
the original challenge README is in [CHALLENGE.md](CHALLENGE.md)).

The bot is pure Python (no numpy) and makes a move in about 10–60 ms.

**Submission files (repo root):** [`ddd.pkl`](ddd.pkl), [`model.py`](model.py),
[`handeval.py`](handeval.py), [`preflop_table.py`](preflop_table.py). The pickle
was built with `python -m submit --team ddd`, which plays it from a clean copy
of just these four files. The same four files are also in
[`submission_ddd/`](submission_ddd).

## How it plays

Every decision compares the expected value of fold, check/call and several
raise sizes (0.4–1.5 pot, 2.5/3bb opens, all-in):

- **Equity by Monte Carlo** (1,200 runouts) against the opponent's
  *estimated range*, using a fast bitmask hand evaluator
  ([`handeval.py`](handeval.py), ~2 µs per 7-card hand, checked against the
  engine's evaluator on 30k random hands).
- **Range narrowing.** Each of the 1,326 hole-card combinations has a weight.
  Every opponent action keeps a band of hands by absolute strength ("raises
  with the top 20%"), where the band width is how often *this* opponent takes
  that action in that spot (7 contexts: open, option, vs raise, vs re-raise,
  free, facing a bet, facing a raise).
- **Fold equity by bet size**, learned per opponent (four size buckets) and
  turned into a strength threshold, so the chance they fold depends on how
  strong their range already is. This stopped the early bot from re-raise
  bluffing into opponents who had already shown strength.
- **Honesty.** Showdowns check whether the opponent's shown hand matched the
  band its actions implied. Random or bluff-heavy bots get their ranges barely
  narrowed; honest bots get read precisely.
- **Learned postflop edge.** Per opponent, chips actually won after the flop
  against what preflop equity predicted. It sees more flops against bots it
  outplays postflop (calling stations) and fewer against tough ones.
- Everything is wrapped so a bug can never become a fault: on any exception it
  checks, or calls a cheap bet, or folds.

## How it was chosen: a league

[`research/`](research) holds the tooling. Every candidate played duplicate
matches (each deal twice, seats swapped) against every other candidate and a
field of sparring bots: the engine dummies, our own bots (maniac, trapper,
loose-aggressive, overbettor, small-bettor, stealer, min-raiser, push/fold,
always-shove), ports of open-source strategies (PyPokerEngine's
HonestPlayer, the Gongsta/Poker-AI naive-equity bot) and:

- **A CFR+ game-theory solution** of the 25bb heads-up preflop game over all
  169 starting hands ([`research/cfr_pre.py`](research/cfr_pre.py), using a
  169×169 equity matrix from [`research/eqmatrix.py`](research/eqmatrix.py)).
  Result: as SB, limp 72%, raise 23%, fold 4.5%.
- A **bandit learner** that picks per opponent between whole strategies.

Highlights (bb/100; full tables in [`research/results/`](research/results)):

| Round | Finding |
|---|---|
| Full round robin, 16 bots | The EV bot was 1st (+143) and beat all 15 others. Always-shove was 12th (−44), push/fold 9th (−15), bandit 3rd (+100) |
| GTO vs EV | GTO preflop was a near tie with the EV bot, but it beat the calling station by more, which led to the learned-postflop-edge feature |
| Round 6 | EV + learned edge was best against the field (+178 vs +168), and even head-to-head over 2000 deals |
| Finals simulation (600 deals vs the strongest 10) | Mean +88. Loses to none except near-copies of itself (within noise) |

Against the engine's dummies (`python -m evals`): fold +75, call +420,
random +250, shove +170, tight +70, equity +160, all with no faults.

## Run it

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/test_model.py -q   # valid submission?
.venv/bin/python -m evals --deals 1000              # vs the dummies
.venv/bin/python -m submit --team ddd               # build ddd.pkl
.venv/bin/python research/h2h.py file:sp_ev_real file:sp_gto_safe 2000
```

`research/league.py ROUND.json N` runs a league (variants as module-constant
overrides of `model.py`); `research/field.py N SEED bot...` runs a full
round robin. The CFR solver needs numpy, offline only:
`python research/eqmatrix.py && python research/cfr_pre.py 0.03`.
