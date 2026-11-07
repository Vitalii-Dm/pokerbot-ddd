import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import random, sys
from multiprocessing import Pool
sys.path.insert(0, ROOT)
from handeval import evaluate, RANK_CHARS
N = 40000
def classes():
    out = []
    for hi in range(12, -1, -1):
        for lo in range(hi, -1, -1):
            if hi == lo: out.append((hi, lo, False))
            else:
                out.append((hi, lo, True)); out.append((hi, lo, False))
    return out
def name(c):
    hi, lo, s = c
    return RANK_CHARS[hi] + RANK_CHARS[lo] + ("" if hi == lo else ("s" if s else "o"))
def eq(c):
    hi, lo, s = c
    a = hi * 4; b = lo * 4 + (0 if s else 1)
    rng = random.Random(hi * 100 + lo * 2 + s)
    rest = [x for x in range(52) if x not in (a, b)]
    won = 0.0
    for _ in range(N):
        cs = rng.sample(rest, 7)
        board = cs[:5]
        m = evaluate([a, b] + board); t = evaluate(cs[5:] + board)
        won += 1 if m > t else 0.5 if m == t else 0
    return name(c), round(won / N, 4)
if __name__ == '__main__':
    with Pool(8) as p:
        res = p.map(eq, classes())
    with open(_os.path.join(ROOT,'preflop_table.py'), 'w') as f:
        f.write('"""Preflop equity of each starting hand against a random hand\n(heads-up, all-in to the river), generated offline with handeval."""\n\n')
        f.write('PREFLOP_EQUITY = {\n')
        for k, v in res: f.write(f'    "{k}": {v},\n')
        f.write('}\n')
    print(res[:5], res[-3:])
