import os as _os, sys as _sys
HERE = _os.path.dirname(_os.path.abspath(__file__)); ROOT = _os.path.dirname(HERE)
_sys.path[:0] = [ROOT, HERE]
import pickle, sys
NAMES, final = pickle.load(open(sys.argv[1],'rb'))
out=open(sys.argv[2],'w')
out.write('"""Preflop strategy for heads-up 25bb, solved offline with CFR+ over\nthe 169 starting hands (fold/limp/2.5bb/all-in tree). Per node, per hand:\naction probabilities."""\n\nGTO_PREFLOP = {\n')
for node, m in final.items():
    out.write(f'    "{node}": {{\n')
    for i,nm in enumerate(NAMES):
        out.write(f'        "{nm}": {tuple(round(float(x),3) for x in m[i])},\n')
    out.write('    },\n')
out.write('}\n')
