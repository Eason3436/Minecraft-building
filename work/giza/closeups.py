import numpy as np, gen, render as R
from gen import PX, PZ, QX, Y, G
def panels(W, C, prefix='c_'):
    kz0, kz1 = C.kz
    out = {}
    def cut(name, xmax, crop, view='se', cut_y=None, floor_y=0, sc=8):
        a = W.a.copy(); a[xmax + 1:, :, :] = 0
        p = prefix + name + '.png'
        R.render(a, W.names, p, view=view, scale=sc, crop=crop, cut_y=cut_y, floor_y=floor_y)
        out[name] = p
    cut('gallery', QX + 1, (PX + 3, QX + 2, C.Z0 - 3, C.zg1 + 5), floor_y=Y(19), cut_y=Y(54), sc=7)
    cut('king', 999, (PX - 3, PX + 12, C.zg1 - 4, kz1 + 3), floor_y=Y(40), cut_y=Y(45), sc=12)
    cut('queen', 999, (PX + 1, PX + 14, PZ - 12, PZ + 5), floor_y=Y(18), cut_y=Y(23), sc=14)
    cut('sub', 999, (PX - 7, PX + 10, PZ - 16, PZ + 20), floor_y=Y(-36), cut_y=Y(-26), sc=12)
    cut('mamun', 999, (PX - 1, PX + 12, PZ - 128, PZ - 92), floor_y=G - 1, cut_y=Y(26), view='ne', sc=8)
    cut('pit', 999, (PX + 2, PX + 42, 268, 279), floor_y=G - 6, cut_y=G - 2, view='se', sc=8)
    cut('temple', 999, (250, 330, 108, 172), floor_y=G - 1, view='se', sc=5)
    return out
if __name__ == '__main__':
    W, C = gen.build()
    print(panels(W, C))
