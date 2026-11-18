"""檢查：水不外溢、步行連通。"""
import numpy as np
from collections import deque
from core import SX, SY, SZ

FLOWABLE = ('air', 'short_grass', 'tall_grass', 'fern', 'large_fern', 'poppy', 'tulip', 'allium', 'cornflower', 'daisy', 'orchid', 'lily_of_the_valley',
            'dandelion', 'rose_bush', 'peony', 'vine', 'reeds', 'torch', 'carpet', 'azalea', 'flowering_azalea', 'cave_vines', 'lantern', 'flower_pot')
PASS = ('air', 'short_grass', 'tall_grass', 'fern', 'poppy', 'tulip', 'allium', 'cornflower', 'daisy', 'orchid', 'lily_of_the_valley', 'dandelion',
        'vine', 'carpet', 'cave_vines', 'large_fern', 'rose_bush', 'peony', 'ladder', '_door')

def water_leaks(W, allow=()):
    names = W.names
    isw = np.array([n == 'water' for n in names])
    flow = np.array([any(n == f or (f in n and f not in ('air',)) for f in FLOWABLE) for n in names]); flow[0] = True
    flow[isw] = False
    a = W.a
    xs, ys, zs = np.nonzero(isw[a])
    bad = []
    allow = set(allow)
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        if (x, y, z) in allow: continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
            nx, ny, nz = x + dx, y + dy, z + dz
            if not (0 <= nx < SX and 0 <= ny < SY and 0 <= nz < SZ):
                bad.append(((x, y, z), 'edge')); continue
            if flow[a[nx, ny, nz]]:
                bad.append(((x, y, z), names[a[nx, ny, nz]], (nx, ny, nz)))
    return bad

def walk(W, start, box=None):
    names = W.names
    ps = np.array([n == 'air' or any(p in n for p in PASS[1:]) for n in names])
    solid_like = ~ps
    solid_like[[i for i, n in enumerate(names) if n in ('water',) or 'leaves' in n]] = False
    a = W.a
    P = ps[a]; S = solid_like[a]
    seen = np.zeros(a.shape, bool)
    q = deque([start]); seen[start] = True
    def ok(x, y, z):
        return 0 <= x < SX and 1 <= y < SY - 1 and 0 <= z < SZ and P[x, y, z] and P[x, y + 1, z] and S[x, y - 1, z]
    assert ok(*start), ('bad start', start, names[a[start]], names[a[start[0], start[1]-1, start[2]]])
    while q:
        x, y, z = q.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (0, 1, -1, -2, -3):
                nx, ny, nz = x + dx, y + dy, z + dz
                if dy == 1 and not P[x, min(y + 2, SY - 1), z]: continue
                if dy < 0 and not all(P[nx, ny + k, nz] for k in range(1, -dy + 1)) if 0 <= nx < SX and 0 <= nz < SZ and ny >= 0 else True: continue
                if ny >= 1 and ok(nx, ny, nz) and not seen[nx, ny, nz]:
                    seen[nx, ny, nz] = True; q.append((nx, ny, nz)); break
        # 梯子
        for dy in (1, -1):
            ny = y + dy
            if 1 <= ny < SY - 1 and not seen[x, ny, z] and 'ladder' in names[a[x, ny, z]] or (1 <= y + dy < SY - 1 and 'ladder' in names[a[x, y, z]] and P[x, y + dy, z] and not seen[x, y + dy, z]):
                if P[x, ny, z] and P[x, min(ny + 1, SY - 1), z]:
                    seen[x, ny, z] = True; q.append((x, ny, z))
    return seen
