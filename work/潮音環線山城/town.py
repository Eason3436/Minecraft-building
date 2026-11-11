"""城鎮：石階、台地街道、地塊搜尋、參數化房屋。"""
import numpy as np
from collections import deque
from core import *
from terrain import *

LEVELS = [22, 28, 34, 40, 46, 52, 58]

STUCCO = {
    'white': [('white_concrete', 80), ('calcite', 20)],
    'cream': [('smooth_sandstone', 80), ('cut_sandstone', 12), ('white_terracotta', 8)],
    'yellow': [('yellow_terracotta', 92), ('orange_terracotta', 8)],
    'orange': [('orange_terracotta', 80), ('hardened_clay', 20)],
    'salmon': [('white_terracotta', 92), ('smooth_sandstone', 8)],
    'pink': [('pink_terracotta', 90), ('red_terracotta', 10)],
    'red': [('red_terracotta', 84), ('hardened_clay', 16)],
    'blue': [('light_blue_terracotta', 92), ('light_gray_terracotta', 8)],
    'green': [('lime_terracotta', 86), ('green_terracotta', 14)],
    'ochre': [('hardened_clay', 72), ('orange_terracotta', 14), ('brown_terracotta', 14)],
}
ROOFS = {  # 半磚, 樓梯, 整塊
    'brick': ('brick_slab', 'brick_stairs', 'brick_block'),
    'sand': ('red_sandstone_slab', 'red_sandstone_stairs', 'smooth_red_sandstone'),
    'granite': ('granite_slab', 'granite_stairs', 'granite'),
    'mud': ('mud_brick_slab', 'mud_brick_stairs', 'mud_bricks'),
}
SHUTTERS = ['warped_trapdoor', 'spruce_trapdoor', 'dark_oak_trapdoor', 'mangrove_trapdoor', 'warped_trapdoor', 'birch_trapdoor']
DOORS = ['spruce_door', 'dark_oak_door', 'wooden_door', 'mangrove_door', 'warped_door', 'birch_door']
PLANKS = ['spruce_planks', 'oak_planks', 'birch_planks', 'dark_oak_planks']
FLOWERS = ['poppy', 'dandelion', 'cornflower', 'oxeye_daisy', 'allium', 'azure_bluet', 'pink_tulip', 'red_tulip', 'orange_tulip', 'white_tulip']
WINCOLS = {5: [1, 3], 6: [1, 4], 7: [1, 3, 5], 8: [2, 5], 9: [2, 4, 6], 10: [2, 4, 5, 7], 11: [2, 4, 6, 8]}


def paving(W):
    B = W.B
    return W.mix((B('cobblestone'), 40), (B('stone_bricks'), 26), (B('andesite'), 18), (B('gravel'), 6), (B('mossy_cobblestone'), 6), (B('cracked_stone_bricks'), 4))


# ---------------------------------------------------------------- 石階
def stair_path(W, T, cells, d, width, rail=False):
    """cells: 中心線，d: 前進方向。高度取「每步高差 ≤1」的最低包絡，蓋出階梯量體並回傳 [(cell,y)]。"""
    h = T['h']; a = W.a; B = W.B
    lx, lz = DIRS[LEFT[d]]
    t = [int(h[x, z]) for x, z in cells]
    y = t[:]
    for _ in range(2):
        for i in range(len(y) - 2, -1, -1): y[i] = max(y[i], y[i + 1] - 1)
        for i in range(1, len(y)): y[i] = max(y[i], y[i - 1] - 1)
    pave = paving(W)
    sb = W.mix((B('stone_bricks'), 70), (B('mossy_stone_bricks'), 15), (B('cracked_stone_bricks'), 15))
    wall = B('stone_brick_wall')
    half = width // 2
    offs = list(range(-half, width - half))
    n = len(cells)
    for i, (cx, cz) in enumerate(cells):
        up = i > 0 and y[i] > y[i - 1]
        down = i + 1 < n and y[i] > y[i + 1] and not up
        for o in offs + [offs[0] - 1, offs[-1] + 1]:
            x, z = cx + lx * o, cz + lz * o
            if not (0 <= x < SX and 0 <= z < SZ): continue
            border = o in (offs[0] - 1, offs[-1] + 1)
            g = int(h[x, z])
            if border:
                if y[i] > g and not T['cor'][x, z]:                       # 側牆
                    for yy in range(g + 1, y[i] + 1): a[x, yy, z] = sb()
                    a[x, y[i] + 1, z] = wall
                    h[x, z] = y[i]; T['reserved'][x, z] = True
                continue
            for yy in range(min(g, y[i]) - 1, y[i]): a[x, yy, z] = sb()
            a[x, y[i] + 1:y[i] + 5, z] = 0
            if (up or down) and not rail:
                a[x, y[i], z] = W.stairs('stone_brick_stairs' if (i + o) % 5 else 'mossy_stone_brick_stairs', d if up else OPP[d])
            else:
                a[x, y[i], z] = pave() if not rail else sb()
            h[x, z] = y[i]; T['reserved'][x, z] = True; T['street'][x, z] = True
    return list(zip(cells, y))


def line(x0, z0, d, n):
    dx, dz = DIRS[d]
    return [(x0 + dx * i, z0 + dz * i) for i in range(n)]


def until_top(T, x0, z0, d, top=58, maxn=120):
    dx, dz = DIRS[d]; out = []
    x, z = x0, z0
    for i in range(maxn):
        if not (2 <= x < SX - 2 and 2 <= z < SZ - 2): break
        out.append((x, z))
        if T['h'][x, z] >= top:
            out += [(x + dx, z + dz), (x + 2 * dx, z + 2 * dz)]
            break
        x += dx; z += dz
    return out


# ---------------------------------------------------------------- 街道
def terrace_streets(W, T):
    h = T['h']; a = W.a; B = W.B
    pave = paving(W)
    wall = B('stone_brick_wall'); lamp = W.lantern()
    edge_d = np.full((SX, SZ), 99, int)
    for L in LEVELS[1:]:
        band = T['town'] & (h == L)
        dq = deque()
        xs, zs = np.nonzero(band)
        for x, z in zip(xs.tolist(), zs.tolist()):
            for dx, dz in DIRS.values():
                nx, nz = x + dx, z + dz
                if 0 <= nx < SX and 0 <= nz < SZ and h[nx, nz] <= L - 3 and not T['cor2'][nx, nz]:
                    edge_d[x, z] = 1; dq.append((x, z)); break
        while dq:
            x, z = dq.popleft()
            if edge_d[x, z] >= 12: continue
            for dx, dz in DIRS.values():
                nx, nz = x + dx, z + dz
                if 0 <= nx < SX and 0 <= nz < SZ and band[nx, nz] and edge_d[nx, nz] > edge_d[x, z] + 1:
                    edge_d[nx, nz] = edge_d[x, z] + 1; dq.append((nx, nz))
    T['edge_d'] = edge_d
    xs, zs = np.nonzero(T['town'] & (edge_d <= 3) & ~T['reserved'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        y = int(h[x, z])
        a[x, y, z] = pave()
        T['street'][x, z] = True
        if edge_d[x, z] == 1:
            a[x, y, z] = B('stone_bricks')
            # 緊鄰石階的地方不設護欄
            if any(T['reserved'][x + dx, z + dz] and h[x + dx, z + dz] >= y - 1 for dx, dz in DIRS.values() if 0 <= x + dx < SX and 0 <= z + dz < SZ):
                continue
            a[x, y + 1, z] = wall
            if (x * 7 + z * 3) % 11 == 0:
                a[x, y + 1, z] = B('stone_bricks'); a[x, y + 2, z] = wall; a[x, y + 3, z] = lamp
            T['parapet'][x, z] = True


def pave_rect(W, T, x0, z0, x1, z1, mat=None, level=None):
    h = T['h']; pave = mat or paving(W)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (0 <= x < SX and 0 <= z < SZ) or T['sea'][x, z] or T['cor'][x, z]: continue
            if level is not None and abs(int(h[x, z]) - level) > 1: continue
            if T['reserved'][x, z] and not T['street'][x, z]: continue
            y = int(h[x, z])
            W.a[x, y, z] = pave(); W.a[x, y + 1:y + 4, z] = 0
            T['street'][x, z] = True


# ---------------------------------------------------------------- 房屋
def roof_gable(F, w, d, y0, kind, axis='x', over=1):
    """低斜度半磚山牆屋頂。axis='x'：屋脊沿局部 x，簷口在前後。y0＝牆頂上一格。回傳屋脊高度。"""
    W = F.W
    slab, stair, full = ROOFS[kind]
    n_s = d if axis == 'x' else w            # 坡向長度
    n_r = w if axis == 'x' else d            # 屋脊方向長度
    top = y0
    for i in range(-over, n_s + over):
        k = min(i + over, (n_s + over - 1) - i)         # 距簷口
        for j in range(n_r):
            gable = j in (0, n_r - 1)
            lx, lz = (j, i) if axis == 'x' else (i, j)
            if k % 2 == 1:
                yy = y0 + (k - 1) // 2
                F.put(lx, yy, lz, W.slab(slab, False))
            else:
                yy = y0 + k // 2 - 1
                if k == 0:
                    inward = ('s' if i < 0 else 'n') if axis == 'x' else ('e' if i < 0 else 'w')
                    F.stairs(lx, yy, lz, stair, inward, True)
                else:
                    F.put(lx, yy, lz, W.B(full) if (gable and 0 <= i < n_s) else W.slab(slab, True))
            top = max(top, yy)
            if gable and 0 <= i < n_s:           # 山牆補滿
                for y2 in range(y0, yy):
                    F.put(lx, y2, lz, F._wm())
    return top


def house(W, T, x0, z0, fw, fd, front, base, floors, rng, shop=False, style=None):
    """x0,z0＝世界座標最小角；fw＝面寬、fd＝進深（局部）；front＝門面朝向；base＝地面方塊 y。"""
    B = W.B
    F = Frame(W, x0, base + 1, z0, fw, fd, front)
    style = style or {}
    color = style.get('color') or rng.choice(list(STUCCO))
    wm = W.mix(*[(B(n), p) for n, p in STUCCO[color]]); F._wm = wm
    roofk = style.get('roof') or rng.choices(list(ROOFS), [50, 22, 14, 14])[0]
    shut = rng.choice(SHUTTERS); door = rng.choice(DOORS); plank = B(rng.choice(PLANKS))
    plinth = W.mix((B('stone_bricks'), 60), (B('cobblestone'), 25), (B('mossy_stone_bricks'), 15))
    pane = B('glass_pane'); air = 0
    w, d = fw, fd
    Ht = floors * 4
    # 地基（補到地面）與地板
    for lx in range(w):
        for lz in range(d):
            x, z = F.xz(lx, lz)
            for yy in range(base, max(int(T['h'][x, z]) - 1, base - 8), -1):
                if W.get(x, yy, z) == 0 or W.names[W.get(x, yy, z)] in ('water', 'grass_block', 'short_grass'):
                    W.put(x, yy, z, plinth())
            F.put(lx, -1, lz, plank if 0 < lx < w - 1 and 0 < lz < d - 1 else plinth())
    F.box(0, 0, 0, w - 1, Ht - 1, d - 1, air)
    # 牆
    for ly in range(Ht):
        for lx in range(w):
            for lz in range(d):
                if lx in (0, w - 1) or lz in (0, d - 1):
                    F.put(lx, ly, lz, plinth() if ly == 0 else wm())
                elif ly % 4 == 3:
                    F.put(lx, ly, lz, plank)
    # 轉角石與樓層腰線（正面）
    trim = B('calcite') if color not in ('white', 'cream') else B('stone_bricks')
    for ly in range(1, Ht):
        if ly % 2 == 1:
            F.put(0, ly, d - 1, trim); F.put(w - 1, ly, d - 1, trim)
    for k in range(1, floors):
        for lx in range(1, w - 1): F.put(lx, 4 * k - 1, d - 1, trim)
    cols = WINCOLS.get(w) or [c for c in range(2, w - 2, 2)]
    doorcol = cols[rng.randrange(len(cols))] if not shop else cols[0]
    F.door(doorcol, 0, d - 1, door, 's')
    F.put(doorcol, -1, d, B('stone_brick_slab') if False else plinth())
    for k in range(floors):
        y = 4 * k
        for c in cols:
            if k == 0 and c == doorcol: continue
            if k == 0 and shop:
                continue
            F.put(c, y + 1, d - 1, pane); F.put(c, y + 2, d - 1, pane)
            for s in (c - 1, c + 1):
                if s not in cols and 0 <= s < w:
                    F.trapdoor(s, y + 1, d, shut, 's'); F.trapdoor(s, y + 2, d, shut, 's')
            if k > 0 and rng.random() < 0.45:
                F.put(c, y, d, B('azalea_leaves_flowered') if rng.random() < 0.6 else B('azalea_leaves'))
        # 側窗
        if k > 0 and d >= 6:
            for lx in (0, w - 1):
                lz = d // 2
                ox, oz = F.xz(lx + (-1 if lx == 0 else 1), lz)
                if W.get(ox, base + 1 + y + 1, oz) == 0:
                    F.put(lx, y + 1, lz, pane); F.put(lx, y + 2, lz, pane)
    # 店面
    if shop:
        awn = [B(c) for c in rng.choice([('red_wool', 'white_wool'), ('blue_wool', 'white_wool'), ('yellow_wool', 'white_wool'), ('green_wool', 'white_wool'), ('orange_wool', 'white_wool')])]
        for lx in range(1, w - 1):
            if lx == doorcol: continue
            F.put(lx, 1, d - 1, pane); F.put(lx, 2, d - 1, pane)
        for lx in range(0, w):
            F.put(lx, 3, d, W.slab({'red_wool': 'mangrove_slab', 'blue_wool': 'warped_slab', 'yellow_wool': 'bamboo_slab', 'green_wool': 'warped_slab', 'orange_wool': 'acacia_slab'}.get(W.names[awn[0]], 'spruce_slab'), True) if lx % 2 == 0 else W.slab('birch_slab', True))
        if w >= 6:
            F.put(w - 2, 0, d, B('barrel', facing_direction=1)); F.put(1 if doorcol != 1 else 2, 0, d, B(rng.choice(['composter', 'hay_block', 'barrel'])))
    # 陽台（法式）
    if floors >= 2 and rng.random() < 0.5 and len(cols) >= 2:
        c = cols[-1] if doorcol != cols[-1] or floors > 2 else cols[0]
        k = rng.randrange(1, floors)
        y = 4 * k
        F.put(c, y, d - 1, pane)
        F.put(c, y - 1, d, W.slab('smooth_stone_slab', True)); F.put(c, y, d, B('iron_bars'))
        for s in (c - 1, c + 1):
            if 0 <= s < w: F.put(s, y - 1, d, W.slab('smooth_stone_slab', True)); F.put(s, y, d, B('iron_bars'))
    # 屋頂
    kind = style.get('rooftype') or rng.choices(['gable', 'gable_z', 'flat'], [62, 18, 20])[0]
    if kind == 'flat':
        for lx in range(w):
            for lz in range(d):
                rim = lx in (0, w - 1) or lz in (0, d - 1)
                F.put(lx, Ht, lz, wm() if rim else air)
                F.put(lx, Ht - 1, lz, wm() if rim else B('smooth_sandstone'))
        for lx in range(0, w, 2):
            F.put(lx, Ht + 1, d - 1, W.slab(ROOFS[roofk][0]))
        # 屋頂花園
        F.put(1, Ht, 1, B('azalea_leaves_flowered')); F.put(w - 2, Ht, 1, B('barrel', facing_direction=1))
        if w >= 6 and d >= 6:
            for lx, lz in ((1, d - 2), (w - 2, d - 2), (1, 2), (w - 2, 2)):
                F.put(lx, Ht, lz, B('spruce_fence')); F.put(lx, Ht + 1, lz, B('spruce_fence'))
            for lx in range(1, w - 1):
                for lz in range(2, d - 1):
                    if (lx + lz) % 2 == 0: F.put(lx, Ht + 2, lz, W.slab('spruce_slab', False))
            F.put(w // 2, Ht, d // 2, B('azalea_leaves'))
        top = Ht + 2
    else:
        top = roof_gable(F, w, d, Ht, roofk, 'x' if kind == 'gable' else 'z')
    # 煙囪
    if kind != 'flat' and rng.random() < 0.6:
        cx, cz = (1, 1) if rng.random() < 0.5 else (w - 2, 1)
        for yy in range(Ht, top + 2): F.put(cx, yy, cz, B('brick_block'))
        F.put(cx, top + 2, cz, B('campfire', extinguished=False))
    # ---- 室內 ----
    lant = W.lantern(True)
    for k in range(floors):
        y = 4 * k
        F.put(w // 2, y + 2, d // 2, lant)
        if k < floors - 1:
            F.put(1, y + 3, 1, air)
        if floors > 1:
            for yy in range(y, y + (4 if k < floors - 1 else 0)):
                F.ladder(1, yy, 1, 's')
        if k == 0:
            F.facing(w - 2, y, 1, 'furnace' if not shop else 'smoker', 's')
            if w >= 6: F.put(w - 3, y, 1, B('crafting_table'))
            if w >= 7: F.put(w - 4, y, 1, B('barrel', facing_direction=1))
            if d >= 6:
                F.put(w - 2, y, d - 3, B('spruce_fence')); F.put(w - 2, y + 1, d - 3, B('brown_carpet'))
                F.stairs(w - 2, y, d - 2, 'spruce_stairs', 's')
            if shop:
                for lx in range(2, w - 2): F.put(lx, y, d - 3, W.slab('spruce_slab', True)) if d >= 6 else None
        else:
            F.bed(w - 2, y, 1, 'n')
            F.facing(w - 2, y, d - 2, 'chest', 'w')
            if w >= 6: F.put(w - 3, y, 1, B('bookshelf'))
            if w >= 7: F.put(w - 4, y, 1, B('bookshelf')); F.put(w - 4, y + 1, 1, B('flower_pot'))
            if d >= 6:
                F.put(2, y, d - 2, B('loom') if k % 2 else B('crafting_table'))
            for lx in range(2, w - 2):
                for lz in range(2, d - 2):
                    F.put(lx, y, lz, B(('red_carpet', 'light_blue_carpet', 'yellow_carpet', 'green_carpet')[k % 4]), keep=True)
    return dict(x0=x0, z0=z0, w=w, d=d, front=front, base=base, floors=floors, color=color, top=base + 1 + top)


# ---------------------------------------------------------------- 地塊搜尋
def find_lots(T, level, rng, wide=(6, 7, 8, 9, 7, 6, 5), deep=(7, 6, 5), gap_p=0.35, need=0.6, tol=0):
    h = T['h']
    free = T['town'] & (np.abs(h - level) <= tol) & ~T['street'] & ~T['reserved'] & ~T['cor2'] & ~T['sea']
    street = T['street']
    lots = []
    cand = []
    xs, zs = np.nonzero(free)
    for x, z in zip(xs.tolist(), zs.tolist()):
        for d, (dx, dz) in DIRS.items():
            nx, nz = x + dx, z + dz
            if 0 <= nx < SX and 0 <= nz < SZ and street[nx, nz] and abs(int(h[nx, nz]) - level) <= 1:
                cand.append((x, z, d))
    rng.shuffle(cand)
    cand.sort(key=lambda c: 0)   # 保持隨機順序
    for x, z, d in cand:
        if not free[x, z]: continue
        ws = list(wide); rng.shuffle(ws)
        placed = False
        for fw in sorted(set(ws), key=lambda v: -v + rng.random() * 3):
            for fd in deep:
                for shift in range(fw):
                    # 以 (x,z) 為正面列上的一格，沿街方向平移 shift
                    sx, sz = DIRS[LEFT[d]]           # 沿街方向（面向 d 時的左手）
                    bx, bz = DIRS[OPP[d]]            # 往屋後
                    cells_x = [x + sx * (i - shift) + bx * j for i in range(fw) for j in range(fd)]
                    cells_z = [z + sz * (i - shift) + bz * j for i in range(fw) for j in range(fd)]
                    X0, X1, Z0, Z1 = min(cells_x), max(cells_x), min(cells_z), max(cells_z)
                    if X0 < 2 or Z0 < 2 or X1 >= SX - 2 or Z1 >= SZ - 2: continue
                    if not free[X0:X1 + 1, Z0:Z1 + 1].all(): continue
                    fr = sum(1 for i in range(fw) if street[x + sx * (i - shift) + DIRS[d][0], z + sz * (i - shift) + DIRS[d][1]])
                    if fr < need * fw: continue
                    lots.append((X0, Z0, fw, fd, d))
                    g = 1 if rng.random() < gap_p else 0
                    if d in 'ns':
                        free[max(X0 - g, 0):X1 + 1 + g, Z0:Z1 + 1] = False
                    else:
                        free[X0:X1 + 1, max(Z0 - g, 0):Z1 + 1 + g] = False
                    T['reserved'][X0:X1 + 1, Z0:Z1 + 1] = True
                    placed = True; break
                if placed: break
            if placed: break
    return lots
