import sys, numpy as np
from gen import *
import render as R
ORDER=['ug_station','ug_track','ramp','el_track','el_station']
def line(bio):
    pcs=[build_piece(bio,k) for k in ORDER]
    names=[]; idx={}
    L=sum(p.L for p in pcs); A=np.zeros((L,H,WZ),np.int32); x0=0
    for p in pcs:
        m=np.array([idx.setdefault(n,len(idx)) for n in p.W.names])
        A[x0:x0+p.L]=m[p.W.a]; x0+=p.L
    names=[None]*len(idx)
    for n,i in idx.items(): names[i]=n
    return A,names,pcs
if __name__=='__main__':
    for bid in sys.argv[1:]:
        A,names,pcs=line(BYID[bid])
        R.render(A,names,f'_prev_{bid}.png',view='sw',scale=4,title=bid)
        R.render(pcs[4].W.a,pcs[4].W.names,f'_prev_{bid}_el.png',view='se',scale=8,cut_y=20)
        R.render(pcs[0].W.a,pcs[0].W.names,f'_prev_{bid}_ug.png',view='se',scale=8,cut_y=6)
        R.render(pcs[4].W.a,pcs[4].W.names,f'_prev_{bid}_el_full.png',view='se',scale=8)
        R.render(pcs[0].W.a,pcs[0].W.names,f'_prev_{bid}_ug_full.png',view='se',scale=8)
