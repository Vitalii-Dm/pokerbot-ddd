import pickle, numpy as np, sys
NAMES, rows = pickle.load(open('eqmatrix.pkl','rb'))
n=len(NAMES)
E=np.array([[r[j][0] for j in range(n)] for r in rows]); W=np.array([[r[j][1] for j in range(n)] for r in rows],float)
POS=float(sys.argv[1]) if len(sys.argv)>1 else 0.03
S=np.clip(E+POS,0,1); AI=1000*E-500
# tree: (player, name, [(action, child)]) ; leaves are matrices
def leaf(m): return ('leaf', np.broadcast_to(np.asarray(m,float),(n,n)))
tree=('sb','root',[
 ('F',leaf(-10)),
 ('L',('bb','L',[('X',leaf(40*S-20)),
                 ('R',('sb','LR',[('F',leaf(-20)),('C',leaf(160*S-80)),
                                  ('A',('bb','LRA',[('F',leaf(80)),('C',leaf(AI))]))])),
                 ('A',('sb','LA',[('F',leaf(-20)),('C',leaf(AI))]))])),
 ('R',('bb','R',[('F',leaf(20)),('C',leaf(100*S-50)),('A',('sb','RA',[('F',leaf(-50)),('C',leaf(AI))]))])),
 ('A',('bb','A',[('F',leaf(20)),('C',leaf(AI))])),
])
reg={}; avg={}
def strat(name,k):
    r=reg.setdefault(name,np.zeros((n,k))); avg.setdefault(name,np.zeros((n,k)))
    p=np.maximum(r,0); s=p.sum(1,keepdims=True)
    return np.where(s>0,p/np.where(s>0,s,1),1.0/k)
def walk(node,rS,rB,t):
    if node[0]=='leaf': return node[1]
    who,name,ch=node; k=len(ch); p=strat(name,k)
    vals=[]
    for a,(act,c) in enumerate(ch):
        if who=='sb': vals.append(walk(c,rS*p[:,a],rB,t))
        else: vals.append(walk(c,rS,rB*p[:,a],t))
    if who=='sb':
        V=sum(p[:,a,None]*vals[a] for a in range(k))
        for a in range(k): reg[name][:,a]+=((W*(vals[a]-V))@rB)
        avg[name]+=t*rS[:,None]*p
    else:
        V=sum(p[None,:,a]*vals[a] for a in range(k))
        for a in range(k): reg[name][:,a]+=(rS@(W*(-(vals[a]-V))))
        avg[name]+=t*rB[:,None]*p
    reg[name]=np.maximum(reg[name],0)  # CFR+
    return V
ones=np.ones(n)
for t in range(1,4001): walk(tree,ones,ones,t)
final={k:v/np.maximum(v.sum(1,keepdims=True),1e-12) for k,v in avg.items()}
# value of game for SB using average strategy
def val(node):
    if node[0]=='leaf': return node[1]
    who,name,ch=node; p=final[name]; vals=[val(c) for _,c in ch]
    if who=='sb': return sum(p[:,a,None]*vals[a] for a in range(len(ch)))
    return sum(p[None,:,a]*vals[a] for a in range(len(ch)))
V=val(tree); print("SB EV chips/hand:", (W*V).sum()/W.sum())
# exploitability: best response for each side
def br(node,side,rO):
    """returns per-own-class value vector of best response for side vs avg strat of other, given other's reach rO(classes)"""
    pass
cnt=W.sum(1)/W.sum()
for name in ['root','R','A','L','LA','RA']:
    p=final[name]; acts=[a for a,_ in dict(root=tree,).get(name,tree)[2]] if name=='root' else None
    print(name, 'avg freq', np.round((p*cnt[:,None]).sum(0),3))
pickle.dump((NAMES,final),open(f'cfr_pre_{POS}.pkl','wb'))
show=['AA','KK','AKs','AKo','A5o','K9o','QJs','T9s','77','22','J7o','94o','72o','32o']
I={n:i for i,n in enumerate(NAMES)}
for h in show: print(h, 'root F/L/R/A', np.round(final['root'][I[h]],2), ' BBvsR F/C/A', np.round(final['R'][I[h]],2), ' BBvsA F/C', np.round(final['A'][I[h]],2))
