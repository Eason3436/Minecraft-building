"""步行連通檢查（近似）：從盜洞前的現代階梯出發。"""
from collections import deque
import numpy as np
import gen
from gen import Y, PX, PZ


def walk(W, C, start, targets, box):
    x0, x1, y0, y1, z0, z1 = box
    names = W.names
    half = np.array([('stairs' in n or 'slab' in n) for n in names])
    lad = np.array([n == 'ladder' for n in names])
    soft = np.array([n in ('air', 'ladder', 'lantern', 'deadbush', 'short_dry_grass', 'tall_dry_grass', 'sandstone_wall_x') for n in names])
    a = W.a[x0:x1, y0:y1, z0:z1]
    H, S, L = half[a], soft[a], lad[a]
    feet = S | H
    head = S | H
    solid = ~S
    X, Yn, Z = a.shape
    def ok(x, y, z):
        if not (0 <= x < X and 1 <= y < Yn - 1 and 0 <= z < Z): return False
        if not (feet[x, y, z] and head[x, y + 1, z]): return False
        return solid[x, y - 1, z] or L[x, y, z] or H[x, y, z]
    sx, sy, sz = start[0] - x0, start[1] - y0, start[2] - z0
    assert ok(sx, sy, sz), ('bad start', start, names[W.a[start]], names[W.a[start[0], start[1]-1, start[2]]])
    seen = np.zeros(a.shape, bool); seen[sx, sy, sz] = True
    q = deque([(sx, sy, sz)])
    while q:
        x, y, z = q.popleft()
        nb = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (1, 0, -1, -2, -3):
                nb.append((x + dx, y + dy, z + dz))
        if L[x, y, z] or L[x, y - 1, z]:
            nb += [(x, y + 1, z), (x, y - 1, z)]
        for n in nb:
            if ok(*n) and not seen[n]:
                # 往上跳要源頭頭頂多一格
                if n[1] > y and not (head[x, y + 2, z] or L[x, y, z]):
                    continue
                seen[n] = True; q.append(n)
    res = {}
    for k, (tx, ty, tz) in targets.items():
        lx, ly, lz = tx - x0, ty - y0, tz - z0
        res[k] = bool(seen[lx, ly:ly + 3, lz].any() | seen[max(lx-1,0):lx+2, ly:ly+3, max(lz-1,0):lz+2].any())
    return res, int(seen.sum())


if __name__ == '__main__':
    W, C = gen.build()
    P = C.P
    zf = PZ - gen.hw_of(7)
    start = (PX + 4, gen.G + 1, zf - 13)
    tg = {k: (v[0], Y(v[1]), v[2]) for k, v in P.items() if k not in ('gant', 'temple', 'boatpit') and not k.startswith('queen_')}
    print(walk(W, C, start, tg, (PX - 20, PX + 30, 2, gen.G + 80, 15, 265)))
