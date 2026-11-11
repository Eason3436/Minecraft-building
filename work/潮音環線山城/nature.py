"""植栽、梯田、瀑布、海草、街燈，以及步行連通檢查。"""
import math
import numpy as np
from collections import deque
from core import *
from terrain import *

GROUND = ('grass_block', 'dirt', 'coarse_dirt', 'podzol')


def can_plant(W, T, x, z, margin=0):
    if not (3 <= x < SX - 3 and 3 <= z < SZ - 3): return False
    if T['street'][x, z] or T['reserved'][x, z] or T['cor2'][x, z] or T['sea'][x, z]: return False
    y = int(T['h'][x, z])
    return W.names[W.a[x, y, z]] in GROUND and W.a[x, y + 1, z] == 0


def leaf_blob(W, cx, cy, cz, rx, ry, leaf, rs, p=0.85):
    for dx in range(-int(rx) - 1, int(rx) + 2):
        for dz in range(-int(rx) - 1, int(rx) + 2):
            for dy in range(-int(ry) - 1, int(ry) + 2):
                d = (dx / rx) ** 2 + (dz / rx) ** 2 + (dy / ry) ** 2
                if d <= 1.0 and (d < 0.6 or rs.rand() < p):
                    W.put(cx + dx, cy + dy, cz + dz, leaf, keep=True)


def tree(W, x, y, z, kind, rs):
    """y＝地面方塊。"""
    B = W.B
    if kind == 'cypress':
        H = int(rs.randint(6, 11)); leaf = B('spruce_leaves'); log = W.log('spruce_log')
        for i in range(1, H + 1): W.put(x, y + i, z, log)
        for i in range(2, H + 2):
            if i <= H - 1:
                for dx, dz in DIRS.values(): W.put(x + dx, y + i, z + dz, leaf, keep=True)
            if 3 <= i <= H - 3 and rs.rand() < 0.5:
                for dx, dz in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                    if rs.rand() < 0.5: W.put(x + dx, y + i, z + dz, leaf, keep=True)
        W.put(x, y + H + 1, z, leaf, keep=True); W.put(x, y + H, z, leaf)
    elif kind == 'pine':        # 傘松
        H = int(rs.randint(6, 9)); leaf = B('oak_leaves'); log = W.log('spruce_log')
        for i in range(1, H + 1): W.put(x, y + i, z, log)
        r = 3 + int(rs.randint(0, 2))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                d = math.hypot(dx, dz)
                if d <= r + 0.3 and (d < r - 0.8 or rs.rand() < 0.7): W.put(x + dx, y + H, z + dz, leaf, keep=True)
                if d <= r - 1.2: W.put(x + dx, y + H + 1, z + dz, leaf, keep=True)
        for dx, dz in DIRS.values(): W.put(x + dx, y + H - 1, z + dz, W.log('spruce_log', 'x' if dx else 'z'), keep=True)
    elif kind == 'olive':
        log = W.log('oak_log'); leaf = B('azalea_leaves')
        W.put(x, y + 1, z, log); W.put(x, y + 2, z, log)
        leaf_blob(W, x, y + 3, z, 2.2, 1.3, leaf, rs, 0.8)
    elif kind == 'lemon':
        W.put(x, y + 1, z, W.log('oak_log')); W.put(x, y + 2, z, W.log('oak_log'))
        leaf_blob(W, x, y + 3, z, 1.6, 1.2, B('oak_leaves'), rs, 0.9)
        for dx, dz in ((1, 0), (-1, 1), (0, -1)):
            if rs.rand() < 0.8 and W.get(x + dx, y + 2, z + dz) == 0: W.put(x + dx, y + 2, z + dz, B('yellow_candle', candles=0, lit=False)) if False else None
    else:                       # oak / birch
        log = W.log('birch_log' if kind == 'birch' else 'oak_log'); leaf = B('birch_leaves' if kind == 'birch' else 'oak_leaves')
        H = int(rs.randint(4, 7))
        for i in range(1, H + 1): W.put(x, y + i, z, log)
        leaf_blob(W, x, y + H, z, 2.4 + rs.rand() * 0.9, 1.9, leaf, rs)


def plant_all(W, T):
    B = W.B; a = W.a; h = T['h']
    rs = np.random.RandomState(31)
    dens = fbm((SX, SZ), 30, 71, 3)
    occupied = np.zeros((SX, SZ), bool)
    def place(x, z, kind, r=2):
        if occupied[max(x - r, 0):x + r + 1, max(z - r, 0):z + r + 1].any(): return False
        if not can_plant(W, T, x, z): return False
        tree(W, x, int(h[x, z]), z, kind, rs); occupied[x, z] = True; return True
    for (x, z) in T.get('plaza_trees', []):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1): a[x + dx, 59, z + dz] = B('stone_brick_wall') if (dx or dz) and False else a[x + dx, 59, z + dz]
        a[x, 58, z] = B('grass_block'); tree(W, x, 58, z, 'cypress', rs)
    # 葡萄梯田
    xs, zs = np.nonzero(T['farm'] & (T['drop'] <= 1))
    fence = B('oak_fence'); leaf = B('oak_leaves')
    for x, z in zip(xs.tolist(), zs.tolist()):
        if not can_plant(W, T, x, z): continue
        y = int(h[x, z])
        if z % 3 == 0:
            a[x, y + 1, z] = fence
            a[x, y + 2, z] = leaf if (x * 7 + z) % 5 else B('azalea_leaves_flowered')
            occupied[x, z] = True
        elif rs.rand() < 0.25:
            a[x, y + 1, z] = B('short_grass')
        elif rs.rand() < 0.02:
            a[x, y + 1, z] = B('hay_block'); occupied[x, z] = True
    # 城內空地：絲柏、橄欖、花
    xs, zs = np.nonzero(T['town'] & ~T['street'] & ~T['reserved'])
    order = rs.permutation(len(xs))
    for i in order:
        x, z = int(xs[i]), int(zs[i])
        r = rs.rand()
        if r < 0.05: place(x, z, 'cypress', 2)
        elif r < 0.09: place(x, z, 'olive', 3)
        elif r < 0.115: place(x, z, 'pine', 5)
        elif r < 0.30 and can_plant(W, T, x, z) and not occupied[x, z]:
            a[x, int(h[x, z]) + 1, z] = B(['poppy', 'dandelion', 'cornflower', 'oxeye_daisy', 'allium', 'pink_tulip', 'short_grass', 'short_grass', 'fern'][rs.randint(9)])
    # 城外森林與山坡
    for _ in range(9000):
        x, z = int(rs.randint(3, SX - 3)), int(rs.randint(3, SZ - 3))
        if T['town'][x, z] or T['farm'][x, z]: continue
        d = dens[x, z]
        if rs.rand() > 0.35 + d * 0.9: continue
        y = int(h[x, z])
        kind = 'pine' if (y > 45 or rs.rand() < 0.25) else 'cypress' if rs.rand() < 0.15 else 'birch' if rs.rand() < 0.2 else 'oak'
        place(x, z, kind, 3 if kind != 'pine' else 4)
    # 草與花
    xs, zs = np.nonzero(~T['town'] & ~T['sea'] & ~T['cor2'] & ~T['farm'])
    for i in rs.permutation(len(xs))[:len(xs) // 5]:
        x, z = int(xs[i]), int(zs[i])
        if can_plant(W, T, x, z) and not occupied[x, z]:
            r = rs.rand()
            a[x, int(h[x, z]) + 1, z] = B('short_grass') if r < 0.7 else B('fern') if r < 0.82 else B(['poppy', 'dandelion', 'cornflower', 'oxeye_daisy', 'azure_bluet'][rs.randint(5)])
    # 岩壁爬藤（擋土牆）
    xs, zs = np.nonzero(T['town'] & (T['drop'] >= 4) & ~T['reserved'])
    for i in rs.permutation(len(xs))[:len(xs) // 6]:
        x, z = int(xs[i]), int(zs[i])
        for d, (dx, dz) in DIRS.items():
            nx, nz = x + dx, z + dz
            if not (0 <= nx < SX and 0 <= nz < SZ): continue
            if h[nx, nz] <= h[x, z] - 4 and not T['reserved'][nx, nz]:
                bit = {'s': 1, 'w': 2, 'n': 4, 'e': 8}[OPP[d]]
                L = int(rs.randint(2, 5))
                for yy in range(int(h[x, z]), int(h[x, z]) - L, -1):
                    if a[nx, yy, nz] == 0: a[nx, yy, nz] = B('vine', vine_direction_bits=bit)
    # 海草與海帶
    xs, zs = np.nonzero(T['sea'])
    water = B('water')
    for i in rs.permutation(len(xs))[:len(xs) // 9]:
        x, z = int(xs[i]), int(zs[i]); y = int(h[x, z])
        if a[x, y + 1, z] != water or y > SEA - 3: continue
        if rs.rand() < 0.4:
            top = min(SEA - 2, y + int(rs.randint(2, 8)))
            for yy in range(y + 1, top + 1):
                if a[x, yy, z] != water: break
                a[x, yy, z] = B('kelp', kelp_age=int(rs.randint(0, 20))); W.w2[x, yy, z] = True
        else:
            a[x, y + 1, z] = B('seagrass'); W.w2[x, y + 1, z] = True


def waterfall(W, T, xs=66, zc=110):
    B = W.B; a = W.a; h = T['h']
    src = B('water'); fall = B('water', liquid_depth=8)
    y = None; n = 0
    for x in range(xs, 20, -1):
        if T['sea'][x, zc]: break
        if T['cor2'][x, zc]: break
        g = int(h[x, zc])
        if y is None: y = g
        if g < y:
            for yy in range(g + 1, y + 1): a[x, yy, zc] = fall
            y = g
        elif g > y:
            for yy in range(y + 1, g + 2): a[x, yy, zc] = 0
        a[x, y, zc] = src; a[x, y - 1, zc] = B('mossy_cobblestone'); a[x, y + 1:y + 3, zc] = 0
        for dz in (-1, 1):                       # 岸
            if a[x, y, zc + dz] == 0 or int(h[x, zc + dz]) < y: 
                for yy in range(int(h[x, zc + dz]), y + 1): a[x, yy, zc + dz] = B('mossy_cobblestone')
        T['reserved'][x, zc] = True; n += 1
    # 源頭小池
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            g = int(h[xs + 1 + dx, zc + dz])
    return n


def street_dressing(W, T):
    B = W.B; a = W.a
    # 下城主街中央燈柱與長椅
    for x in range(52, 200, 14):
        if not T['street'][x, 179] or a[x, 23, 179] != 0 or T['h'][x, 179] != 22: continue
        a[x, 23, 179] = B('stone_bricks'); a[x, 24, 179] = B('stone_brick_wall'); a[x, 25, 179] = B('stone_brick_wall'); a[x, 26, 179] = W.lantern()
        if a[x + 2, 23, 179] == 0: a[x + 2, 23, 179] = W.stairs('spruce_stairs', 's' if x % 28 else 'n')
    # 站前廣場花台
    for (x, z) in ((116, 174), (127, 174), (103, 183), (143, 183)):
        if a[x, 23, z] == 0:
            a[x, 23, z] = B('azalea_leaves_flowered'); 
            for dx, dz in DIRS.values():
                if a[x + dx, 23, z + dz] == 0: a[x + dx, 23, z + dz] = B('spruce_trapdoor', direction={(1, 0): 1, (-1, 0): 0, (0, 1): 3, (0, -1): 2}[(dx, dz)], open_bit=True)
    # 東城街燈
    for z in range(60, 172, 12):
        if a[215, 29, z] == 0 and T['h'][215, z] == 28 and not T['reserved'][215, z]:
            a[215, 29, z] = B('stone_brick_wall'); a[215, 30, z] = B('stone_brick_wall'); a[215, 31, z] = W.lantern()


def walkable_check(W, T, start, targets):
    """玩家步行連通：站在實心/樓梯/半磚上、頭上 2 格淨空、每步高差 ≤1。"""
    a = W.a; names = W.names
    PASS = ('air', 'carpet', 'rail', 'short_grass', 'fern', 'poppy', 'dandelion', 'cornflower', 'daisy', 'allium', 'tulip', 'bluet', 'vine', 'lever', 'door', 'pressure_plate', 'ladder', 'trapdoor', 'lantern_x')
    passable = np.array([n == 'air' or (any(k in n for k in PASS[1:]) and 'block' not in n) for n in names])
    NOSTAND = ('water', 'leaves', 'fence', '_wall', 'pane', 'bars', 'lantern', 'campfire', 'kelp', 'seagrass', 'chain')
    stand = np.array([not passable[i] and not any(k in n for k in NOSTAND) for i, n in enumerate(names)])
    P = passable[a]; S = stand[a]
    ok = np.zeros(a.shape, bool)               # ok[x,y,z]＝可站在 y（腳在 y，地板在 y-1）
    ok[:, 1:-1, :] = S[:, :-2, :] & P[:, 1:-1, :] & P[:, 2:, :]
    sx, sy, sz = start
    while not ok[sx, sy, sz] and sy < SY - 2: sy += 1
    seen = np.zeros(a.shape, bool); seen[sx, sy, sz] = True
    dq = deque([(sx, sy, sz)])
    while dq:
        x, y, z = dq.popleft()
        for dx, dz in DIRS.values():
            nx, nz = x + dx, z + dz
            if not (0 <= nx < SX and 0 <= nz < SZ): continue
            for dy in (0, 1, -1):
                ny = y + dy
                if 1 <= ny < SY - 2 and ok[nx, ny, nz] and not seen[nx, ny, nz]:
                    if dy == 1 and not P[x, y + 2, z]: continue
                    if dy == -1 and not P[nx, y + 1, nz]: continue
                    seen[nx, ny, nz] = True; dq.append((nx, ny, nz))
    res = {}
    for name, (tx, ty, tz) in targets.items():
        sub = seen[max(tx - 2, 0):tx + 3, max(ty - 2, 0):ty + 3, max(tz - 2, 0):tz + 3]
        res[name] = bool(sub.any())
    return res, seen


def clear_ways(W, T):
    """把長進軌道、街道上方的樹葉與原木清掉。"""
    a = W.a
    veg = np.array([('leaves' in n or n.endswith('_log')) for n in W.names])
    n = 0
    for (x, z), y in T['funi']:
        for dx in (-1, 0, 1):
            col = a[x + dx, y + 1:y + 6, z]; m = veg[col]; n += int(m.sum()); col[m] = 0
    for (x, z), y in T.get('mine_path', []):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                col = a[x + dx, y + 1:y + 5, z + dz]; m = veg[col]; n += int(m.sum()); col[m] = 0
    xs, zs = np.nonzero(T['cor'] & ~T['tunnel'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        r_ = int(T['ry'][x, z]); col = a[x, r_:r_ + 6, z]; m = veg[col]; n += int(m.sum()); col[m] = 0
    xs, zs = np.nonzero(T['street'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        y = int(T['h'][x, z])
        col = a[x, y + 1:y + 4, z]; m = veg[col] & np.array(['leaves' in W.names[k] for k in col]); n += int(m.sum()); col[m] = 0
    return n
