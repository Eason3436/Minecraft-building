"""哈利法塔塔身：Y 形三翼平面、螺旋退台、帷幕牆、核心筒、樓層室內、塔冠與尖塔。"""
import math
import numpy as np
from core import *

CC = 84.5                      # 塔中心（格 84 的中心）
X0, X1 = 30, 140               # 計算視窗
F0 = 4                         # 地面層（地板在 y=3）
L0, LMIN = 30.0, 6.5           # 翼長（中心到翼尖）
SETBACKS = [40 + 8 * k for k in range(33)]
ORDERW = [0, 2, 1]             # 退台順序：北 → 西南 → 東南（俯視逆時針）
DIRV = [(0.0, -1.0), (math.sqrt(3) / 2, 0.5), (-math.sqrt(3) / 2, 0.5)]   # 北、東南、西南
WNAME = ['北翼', '東南翼', '西南翼']
YT, YSP, YNEED, YTOP = 264, 300, 345, 372
MECH = (36, 76, 132, 192, 236)
REST, DECK124, DECK125, DECK148, LOUNGE = 200, 208, 212, 252, (256, 260)
CORE = (80, 88)

g = np.arange(X0, X1) + 0.5 - CC
DX, DZ = np.meshgrid(g, g, indexing='ij')
TT = [DX * d[0] + DZ * d[1] for d in DIRV]
SS = [(-DX * d[1] + DZ * d[0]) for d in DIRV]
R = np.hypot(DX, DZ)
XX, ZZ = np.meshgrid(np.arange(X0, X1), np.arange(X0, X1), indexing='ij')


def mstory(y):
    """格高 → 實際公尺"""
    return (y - F0) * 2.25


def wing_len(i, y):
    n = sum(1 for k, yk in enumerate(SETBACKS) if yk < y and ORDERW[k % 3] == i)
    return L0 - (L0 - LMIN) * n / 11.0


def hw(y):
    return 7.2 - 2.6 * min(max(y - F0, 0), 292) / 292


def rc(y):
    return 8.2 - 2.4 * min(max(y - F0, 0), 292) / 292


_cache = {}


def mask(y):
    if y in _cache:
        return _cache[y]
    if y < YSP:
        h = hw(y); a = 0.9 * h
        m = R <= rc(y)
        for i in range(3):
            L = wing_len(i, y); t = TT[i]; s = np.abs(SS[i])
            f = np.where(t <= L - a, 1.0, np.sqrt(np.clip(1 - ((t - (L - a)) / a) ** 2, 0, 1)))
            m |= (t >= 0) & (t <= L) & (s <= h * f)
    elif y < YNEED:
        rs = 4.6 - 3.4 * (y - YSP) / (YNEED - 1 - YSP)
        m = R <= rs
    elif y <= YTOP:
        m = R < 0.1
    else:
        m = np.zeros_like(R, bool)
    _cache[y] = m
    return m


def erode(m):
    p = np.pad(m, 1)
    return m & p[2:, 1:-1] & p[:-2, 1:-1] & p[1:-1, 2:] & p[1:-1, :-2]


def dilate(m):
    p = np.pad(m, 1)
    return m | p[2:, 1:-1] | p[:-2, 1:-1] | p[1:-1, 2:] | p[1:-1, :-2]


def facade_coord(y):
    """每格的立面座標（給鰭片節奏用）"""
    h = hw(y)
    idx = np.argmax(np.stack(TT), axis=0)
    t = np.choose(idx, TT); s = np.choose(idx, SS)
    L = np.choose(idx, [wing_len(i, y) for i in range(3)])
    side = t < L - 0.9 * h
    return np.where(side, t, s)


def put2d(W, y, m, b):
    """把 2D 遮罩（視窗座標）寫到 y 層；b 可為 id 或同形陣列"""
    sub = W.a[X0:X1, y, X0:X1]
    if np.isscalar(b) or isinstance(b, (int, np.integer)):
        sub[m] = b
    else:
        sub[m] = b[m]


def build_tower(W, info):
    B = W.B
    glassB = B('light_blue_stained_glass'); glassG = B('light_gray_stained_glass'); fin = B('polished_diorite')
    tint = B('tinted_glass'); dslate = B('polished_deepslate'); quartz = B('smooth_quartz')
    slab = B('smooth_stone'); lamp = B('sea_lantern'); pane = B('light_gray_stained_glass_pane')
    iron = B('iron_block'); lgc = B('light_gray_concrete'); white = B('white_concrete')
    mechset = set()
    for s in MECH:
        mechset.update((s + 1, s + 2, s + 3))
    deckset = set()
    for s in (DECK124, DECK125, DECK148, REST) + LOUNGE:
        deckset.update((s + 1, s + 2, s + 3))
    terr_rooms = []
    for y in range(F0, YTOP + 1):
        M = mask(y)
        if not M.any():
            continue
        bd = M & ~erode(M)
        inner = M & ~bd
        if y >= YSP:                       # 尖塔
            if y >= YNEED:
                put2d(W, y, M, iron if ((y - YNEED) // 4) % 2 == 0 else lgc)
                continue
            ang = np.floor((np.arctan2(DZ, DX) + math.pi) / (2 * math.pi) * 12).astype(int)
            mat = np.where(ang % 2 == 0, iron, lgc)
            if y % 6 == 0:
                mat = np.full(M.shape, fin)
            put2d(W, y, bd, mat)
            if y % 12 == 0:
                put2d(W, y, inner, lgc)
            continue
        fc = np.floor(facade_coord(y) + 300).astype(int)
        crown = y >= YT
        if crown:
            mat = np.where(fc % 2 == 0, fin, glassG)
        elif y in mechset:
            mat = np.where(fc % 3 == 0, B('light_gray_concrete'), np.where(y % 2 == 0, tint, B('gray_stained_glass')))
        elif y in deckset:
            mat = np.where(fc % 6 == 0, fin, np.where(fc % 2 == 0, glassG, glassB))
        elif y % 4 == 0:
            mat = np.where(fc % 3 == 0, fin, glassG)
        else:
            mat = np.where(fc % 3 == 0, fin, np.where(fc % 3 == 1, glassB, glassG))
        put2d(W, y, bd, mat)
        # 樓板
        is_slab = (y % 4 == 0 and y >= 12 and y < YT) or (crown and y % 8 == 0)
        if is_slab:
            light = ((XX % 6) == 3) & ((ZZ % 6) == 3)
            put2d(W, y, inner, slab)
            put2d(W, y, inner & light, lamp)
    # 退台屋頂與玻璃欄杆（含 y=299 頂部收頭）
    for y in range(F0, YTOP):
        M, M1 = mask(y), mask(y + 1)
        rem = M & ~M1
        if not rem.any():
            continue
        put2d(W, y, rem, quartz)
        if y < YSP:
            edge = rem & ~erode(M)
            put2d(W, y + 1, edge, pane)
            if y in SETBACKS:
                terr_rooms.append((y, int(rem.sum())))
    info['terraces'] = terr_rooms
    # 尖塔頂
    W.put(84, YTOP, 84, B('lightning_rod', facing_direction=1))
    for yy in (330, 352, 364):
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if W.get(84 + dx, yy, 84 + dz) == 0:
                W.put(84 + dx, yy, 84 + dz, B('end_rod', facing_direction={(1, 0): 5, (-1, 0): 4, (0, 1): 3, (0, -1): 2}[(dx, dz)]))
    core(W, info)
    entrances(W, info)
    interiors(W, info)
    terrace124(W, info)


def core(W, info):
    B = W.B
    wall = B('white_concrete'); shaft = B('light_gray_concrete'); slab = B('smooth_stone')
    glass = B('glass'); bub = B('bubble_column', drag_down=False)
    a, b = CORE
    for y in range(F0, YT):
        for x in range(a, b + 1):
            for z in range(a, b + 1):
                edge = x in (a, b) or z in (a, b)
                if edge:
                    door = (x == 84 or z == 84) and ((y - 1) % 4 in (0, 1) or y in (4, 5, 6))
                    W.put(x, y, z, 0 if door else wall)
                elif 85 <= x <= 87 and 85 <= z <= 87:
                    W.put(x, y, z, shaft)
                elif y % 4 == 0 and y >= 12:
                    W.put(x, y, z, slab)
                else:
                    W.put(x, y, z, 0)
    # 氣泡柱電梯：(82,82)，地面到 148 樓
    top = DECK148
    W.put(82, 3, 82, B('soul_sand'))
    for y in range(F0, top + 1):
        for x in (81, 82, 83):
            for z in (81, 82, 83):
                W.put(x, y, z, bub if (x, z) == (82, 82) else glass)
    W.door(82, 4, 83, 'wooden_door', 's')
    for x in (81, 82, 83):
        for z in (81, 82, 83):
            if (x, z) not in ((82, 82), (82, 83)):
                W.put(x, top + 1, z, glass)
    # 梯子 (87,82)，靠東牆
    lad = W.ladder('w')
    for y in range(F0, LOUNGE[1] + 2):
        W.put(87, y, 82, lad)
    # 核心頂
    for x in range(a, b + 1):
        for z in range(a, b + 1):
            W.put(x, YT, z, B('smooth_quartz'))
    W.put(87, YT, 82, lad)
    info['bubble'] = (82, F0, 82, top)


def entrances(W, info):
    """三翼尖端入口：開門洞＋雨庇"""
    B = W.B
    pil = B('quartz_pillar'); roof = B('smooth_quartz'); gl = B('light_blue_stained_glass'); fl = B('polished_diorite')
    ents = []
    for i, d in enumerate(DIRV):
        L = wing_len(i, F0)
        for y in (4, 5, 6):
            M = mask(y)
            m = M & ~erode(M) & (np.abs(SS[i]) <= 2.0) & (TT[i] > L - 4)
            put2d(W, y, m, 0)
        # 雨庇：沿翼軸往外 2..10、半寬 5
        cells = []
        for x in range(X0, X1):
            for z in range(X0, X1):
                px, pz = x + .5 - CC, z + .5 - CC
                t = px * d[0] + pz * d[1]; s = -px * d[1] + pz * d[0]
                if L + 1 <= t <= L + 10 and abs(s) <= 5:
                    cells.append((x, z, t, s))
        for x, z, t, s in cells:
            W.put(x, 3, z, fl)
            edge = t > L + 9 or abs(s) > 4
            W.put(x, 9, z, roof if edge else gl)
            if (t > L + 9 and abs(s) > 4) or (abs(t - (L + 9.5)) < .6 and abs(abs(s) - 4.5) < .6):
                for y in range(4, 9):
                    W.put(x, y, z, pil)
        # 柱子：四角
        for tt, ss in ((L + 9.5, 4.5), (L + 9.5, -4.5), (L + 1.5, 4.5), (L + 1.5, -4.5)):
            x = int(math.floor(CC + tt * d[0] - ss * d[1])); z = int(math.floor(CC + tt * d[1] + ss * d[0]))
            for y in range(4, 9):
                W.put(x, y, z, pil)
        tip = (int(CC + (L + 6) * d[0]), 4, int(CC + (L + 6) * d[1]))
        ents.append(tip)
    info['entrances'] = ents


# ---------------- 室內 ----------------
STAIR_BACK = {'s': 'n', 'n': 's', 'e': 'w', 'w': 'e'}


def chair(W, x, y, z, face, mat='spruce_stairs'):
    """椅子面向 face（椅背在反方向）"""
    W.put(x, y, z, W.stairs(mat, OPP[face]))


def free(W, x, y, z, w=1, d=1):
    for i in range(x - w, x + w + 1):
        for k in range(z - d, z + d + 1):
            if W.get(i, y, k) != 0 or W.get(i, y + 1, k) != 0 or W.get(i, y - 1, k) == 0:
                return False
            if CORE[0] - 1 <= i <= CORE[1] + 1 and CORE[0] - 1 <= k <= CORE[1] + 1:
                return False
    return True


def tpl_bed(W, x, y, z, r):
    head = r.choice('nesw')
    W.bed(x, y, z, head)
    dx, dz = DIRS[RIGHT[head]]
    W.put(x + dx, y, z + dz, W.B('barrel', facing_direction=1))
    W.put(x + dx, y + 1, z + dz, W.lantern())
    hx, hz = DIRS[OPP[head]]
    W.put(x + hx * 2, y, z + hz * 2, W.B('white_carpet'))


def tpl_sofa(W, x, y, z, r):
    col = r.choice(['light_gray_carpet', 'cyan_carpet', 'brown_carpet', 'white_carpet'])
    for i in (-1, 0, 1):
        for k in (0, 1):
            W.put(x + i, y, z + k, W.B(col))
    for i in (-1, 0, 1):
        chair(W, x + i, y, z - 1, 's', r.choice(['dark_oak_stairs', 'quartz_stairs']))
    W.put(x, y, z + 1, W.slab('spruce_slab', top=True))
    W.put(x - 1, y, z + 1, W.B('flowering_azalea') if r.random() < .5 else W.B('azalea'))


def tpl_dining(W, x, y, z, r):
    W.put(x, y, z, W.B('dark_oak_fence'))
    W.put(x, y + 1, z, W.B('light_weighted_pressure_plate'))
    for f, (dx, dz) in DIRS.items():
        chair(W, x + dx, y, z + dz, OPP[f], 'spruce_stairs')


def tpl_plant(W, x, y, z, r):
    W.put(x, y, z, W.B(r.choice(['flowering_azalea', 'azalea'])))


def tpl_kitchen(W, x, y, z, r):
    for i, b in zip((-1, 0, 1), ('smoker', 'quartz_block', 'barrel')):
        if b == 'smoker':
            W.put(x + i, y, z, W.facing('smoker', 's'))
        elif b == 'barrel':
            W.put(x + i, y, z, W.B('barrel', facing_direction=1))
        else:
            W.put(x + i, y, z, W.B(b))
    W.put(x, y + 1, z, W.B('cauldron'))


def tpl_desk(W, x, y, z, r):
    for i in (-1, 0):
        W.put(x + i, y, z, W.slab('dark_oak_slab', top=True))
        chair(W, x + i, y, z + 1, 'n', 'dark_oak_stairs')
    W.put(x + 1, y, z, W.B('bookshelf'))
    W.put(x + 1, y + 1, z, W.B('lantern'))


def tpl_meeting(W, x, y, z, r):
    for i in (-1, 0, 1):
        W.put(x + i, y, z, W.slab('dark_oak_slab', top=True))
        chair(W, x + i, y, z - 1, 's', 'dark_oak_stairs')
        chair(W, x + i, y, z + 1, 'n', 'dark_oak_stairs')


def tpl_table_rest(W, x, y, z, r):
    W.put(x, y, z, W.B('quartz_block'))
    W.put(x, y + 1, z, W.B('white_carpet'))
    for f, (dx, dz) in DIRS.items():
        if f in 'ns':
            chair(W, x + dx, y, z + dz, OPP[f], 'crimson_stairs')


def tpl_bench(W, x, y, z, r):
    for i in (-1, 0, 1):
        W.put(x + i, y, z, W.slab('quartz_slab'))


def tpl_scope(W, x, y, z, r):
    W.put(x, y, z, W.B('iron_bars'))
    W.put(x, y + 1, z, W.B('lightning_rod', facing_direction=r.choice([2, 3, 4, 5])))


def tpl_machine(W, x, y, z, r):
    m = r.choice(['iron_block', 'polished_andesite', 'light_gray_concrete'])
    for i in (-1, 0, 1):
        for k in (0,):
            W.put(x + i, y, z + k, W.B(m))
            W.put(x + i, y + 1, z + k, W.B('iron_bars') if i == 0 else W.B(m))
    W.put(x, y + 2, z, W.B('iron_bars'))


def tpl_bar(W, x, y, z, r):
    for i in (-1, 0, 1):
        W.put(x + i, y, z, W.B('quartz_block'))
        W.put(x + i, y + 1, z, W.B('white_stained_glass_pane') if i else W.lantern())
        chair(W, x + i, y, z + 1, 'n', 'crimson_stairs')


PROGRAMS = {
    'hotel': [(tpl_bed, 4), (tpl_sofa, 2), (tpl_plant, 2), (tpl_dining, 1)],
    'res': [(tpl_bed, 3), (tpl_sofa, 3), (tpl_dining, 2), (tpl_kitchen, 2), (tpl_plant, 2)],
    'office': [(tpl_desk, 6), (tpl_meeting, 2), (tpl_plant, 2)],
    'mech': [(tpl_machine, 1)],
    'rest': [(tpl_table_rest, 5), (tpl_bar, 1), (tpl_plant, 1)],
    'deck': [(tpl_bench, 3), (tpl_scope, 3), (tpl_plant, 1)],
    'lounge': [(tpl_sofa, 4), (tpl_bar, 1), (tpl_plant, 2), (tpl_dining, 2)],
    'lobby': [(tpl_sofa, 3), (tpl_plant, 4)],
}


def program(s):
    if s == 3: return 'lobby'
    if s in MECH: return 'mech'
    if s in (REST, 204): return 'rest'
    if s in (DECK124, DECK125, DECK148): return 'deck'
    if s in LOUNGE: return 'lounge'
    if s <= 32: return 'hotel'
    if s <= 172: return 'res'
    return 'office'


def furnish(W, s, prog, rng, density=1.0):
    w = s + 1
    M = mask(w)
    I = erode(M)
    pool = PROGRAMS[prog]
    fns = [f for f, k in pool for _ in range(k)]
    off = rng.randrange(4)
    n = 0
    if prog in ('deck', 'lounge', 'rest'):
        ring = erode(M) & ~erode(erode(M))
        k = 0
        for x, z in zip(*np.nonzero(ring)):
            x += X0; z += X0
            if W.get(x, w, z) != 0 or W.get(x, w - 1, z) == 0 or (CORE[0] - 1 <= x <= CORE[1] + 1 and CORE[0] - 1 <= z <= CORE[1] + 1):
                continue
            k += 1
            if k % 3 == 0:
                if prog == 'deck':
                    W.put(x, w, z, W.B('iron_bars')); W.put(x, w + 1, z, W.B('lightning_rod', facing_direction=rng.choice([2, 3, 4, 5])))
                else:
                    W.put(x, w, z, W.B(rng.choice(['flowering_azalea', 'azalea'])))
                n += 1
            elif k % 3 == 1 and prog == 'deck':
                W.put(x, w, z, W.slab('quartz_slab')); n += 1
    for x in range(X0 + off, X1, 4):
        for z in range(X0 + (off * 2) % 4, X1, 4):
            jx, jz = x + rng.randrange(-1, 2), z + rng.randrange(-1, 2)
            if not (X0 <= jx < X1 and X0 <= jz < X1):
                continue
            if not I[jx - X0, jz - X0] or rng.random() > density:
                continue
            if not all(I[min(max(jx + i - X0, 0), X1 - X0 - 1), min(max(jz + k - X0, 0), X1 - X0 - 1)] for i in (-1, 0, 1) for k in (-1, 0, 1)):
                continue
            if not free(W, jx, w, jz):
                continue
            rng.choice(fns)(W, jx, w, jz, rng)
            n += 1
    return n


def interiors(W, info):
    rng = W.rng
    B = W.B
    # 大廳地板（y=3）
    M = mask(F0)
    chk = ((XX + ZZ) % 2 == 0)
    flo = np.where(chk, B('quartz_block'), B('polished_diorite'))
    put2d(W, 3, M, flo)
    put2d(W, 3, M & (np.abs(R - 14) < 0.7), B('polished_blackstone'))
    W.put(82, 3, 82, B('soul_sand'))
    # 接待櫃台：每翼 t≈20
    for i in range(3):
        m = M & (np.abs(TT[i] - 22) < 0.6) & (np.abs(SS[i]) <= 3.5)
        put2d(W, 4, m, B('quartz_block'))
        put2d(W, 5, m, B('smooth_quartz_slab'))
    # 吊燈
    for x in range(X0, X1):
        for z in range(X0, X1):
            if M[x - X0, z - X0] and (x % 6 == 3 and z % 6 == 3) and W.get(x, 11, z) == 0 and W.get(x, 12, z) != 0:
                W.put(x, 11, z, B('end_rod', facing_direction=0))
    counts = {}
    counts[3] = furnish(W, 3, 'lobby', rng, 0.6)
    for s in range(12, YT, 4):
        prog = program(s)
        counts[s] = furnish(W, s, prog, rng, 0.85 if prog in ('res', 'hotel', 'office') else 1.0)
    # 觀景台地板與欄杆
    for s in (DECK124, DECK125, DECK148):
        M = mask(s + 1)
        put2d(W, s, M & ~(M & ~erode(M)) & (W.a[X0:X1, s, X0:X1] == B('smooth_stone')), B('polished_deepslate'))
    # 餐廳地毯
    for s in (REST, 204):
        M = mask(s + 1); I = erode(M)
        sub = W.a[X0:X1, s + 1, X0:X1]
        m = I & (sub == 0)
        sub[m] = B('gray_carpet')
    info['furniture'] = counts


def terrace124(W, info):
    """124 樓戶外觀景退台：在 y=208 退台的立面開門"""
    y = DECK124
    rem = mask(y) & ~mask(y + 1)
    nb = dilate(rem) & mask(y + 1) & ~erode(mask(y + 1))
    fc = np.floor(facade_coord(y + 1) + 300).astype(int)
    door = nb & (fc % 6 >= 2) & (fc % 6 <= 3)
    for yy in (y + 1, y + 2):
        put2d(W, yy, door, 0)
    # 戶外欄杆已由 pane 處理；加長椅
    info['terrace124'] = int(door.sum())
