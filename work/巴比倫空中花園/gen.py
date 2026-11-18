"""巴比倫空中花園 生成器：地形河道 → 梯台花園 → 提水系統 → 城門城牆王宮民宅 → 地面植栽。"""
import math
from core import *

G = 8                      # 地面草地頂
NL = 5                     # 梯台層數
INSET = 9
R0 = (44, 32, 147, 127)    # L0 x0 z0 x1 z1
YT = [17 + 9 * k for k in range(NL)]   # 每層平台頂面 y
def ybase(m): return G if m == 0 else YT[m - 1]
def rect(k): x0, z0, x1, z1 = R0; return (x0 + INSET * k, z0 + INSET * k, x1 - INSET * k, z1 - INSET * k)
TR = (92, 99)              # 大階梯 x 範圍（側牆 91、100）
def casc_t(m, s):
    """第 m 層某一面的瀑布位置（沿牆 t 座標）。"""
    x0, z0, x1, z1 = rect(m)
    w = x1 - x0
    if s in 'ns':
        out = [x0 + round(0.25 * w), x1 - round(0.25 * w)]
        if s == 's': out = [t for t in out if not (85 <= t <= 106)]
        return out
    zc = (z0 + z1) // 2
    return [zc + 8] if s == 'w' else [zc]
VINE_BIT = {'s': 4, 'n': 1, 'w': 8, 'e': 2}
OUTV = {'s': (0, 1), 'n': (0, -1), 'w': (-1, 0), 'e': (1, 0)}

W = World()
rng = W.rng
B = W.B
AIR = 0

# ---------- 常用方塊 ----------
MB = B('mud_bricks'); PM = B('packed_mud'); BR = B('brick_block'); HC = B('hardened_clay')
SS = B('smooth_sandstone'); CS = B('cut_sandstone'); CH = B('chiseled_sandstone'); SAND = B('sandstone')
LAP = B('lapis_block'); BLT = B('blue_terracotta'); BC = B('blue_concrete')
YT_ = B('yellow_terracotta'); GOLD = B('gold_block'); QZ = B('smooth_quartz'); OT = B('orange_terracotta')
GRASS = B('grass_block'); DIRT = B('dirt'); WATER = B('water'); SANDB = B('sand'); CDIRT = B('coarse_dirt')
MBW = B('mud_brick_wall'); MBS = B('mud_brick_slab'); MBST = B('mud_brick_slab', vertical_half='top')
SSS = B('smooth_sandstone_slab'); CSS = B('cut_sandstone_slab')
LANT_H = B('lantern', hanging=True); LANT = B('lantern')
def wall_mix(): return rng.choices([MB, PM, HC, MB], [55, 20, 8, 17])[0]
def pier_mix(): return rng.choices([MB, BR, PM], [60, 25, 15])[0]
def glazed(): return rng.choices([LAP, BLT, BC, B('blue_glazed_terracotta', facing_direction=2)], [55, 15, 20, 10])[0]
def pave(x, z): return (CS if (x + z) % 2 else SS) if (x // 3 + z // 3) % 3 else SAND


def stairs(mat, asc, up=False): return W.stairs(mat, asc, up)


def merlon_row(x, y, z, t, mat=MB, slab=MBS):
    """巴比倫階梯垛口：t%4 0..2 一格，t%4==1 再加頂。"""
    if t % 4 in (0, 1, 2):
        W.put(x, y, z, mat)
        if t % 4 == 1:
            W.put(x, y + 1, z, slab)


# ================= 地形 =================
def terrain():
    W.box(0, 0, 0, SX - 1, 1, SZ - 1, SAND)
    W.box(0, 2, 0, SX - 1, G - 1, SZ - 1, DIRT)
    W.box(0, G, 0, SX - 1, G, SZ - 1, GRASS)
    # 幼發拉底河 x4–25，z2–189；水面 y7
    for x in range(4, 26):
        for z in range(2, 190):
            edge = min(x - 4, 25 - x)
            bed = 2 if edge >= 3 else 3 + (2 - edge)
            W.box(x, bed, z, x, G, z, AIR)
            W.put(x, bed - 1, z, rng.choice([SANDB, SANDB, B('gravel'), B('clay')]))
            for y in range(bed, SEA + 1):
                W.put(x, y, z, WATER)
            if bed <= 4 and rng.random() < 0.05:
                W.put(x, bed, z, B('seagrass')); W.w2[x, bed, z] = True
            elif bed <= 3 and rng.random() < 0.02:
                for y in range(bed, bed + rng.randint(2, 3)): W.put(x, y, z, B('kelp', kelp_age=rng.randint(0, 20))); W.w2[x, y, z] = True
    # 西岸沙灘 x0–3，蘆葦
    for z in range(0, SZ):
        for x in range(0, 4):
            W.put(x, G, z, SANDB); W.put(x, G - 1, z, SANDB)
        if 2 <= z < 190 and rng.random() < 0.35:
            h = rng.randint(1, 3)
            for y in range(G + 1, G + 1 + h): W.put(3, y, z, B('reeds'))
    # 東岸碼頭 x26–30
    for z in range(2, 190):
        W.box(26, 3, z, 26, G, z, CS if z % 8 else SS)
        W.box(27, 3, z, 30, G - 1, z, SAND)
        for x in range(27, 31): W.put(x, G, z, pave(x, z))
        if z % 6 == 0: W.put(30, G + 1, z, MBW)
    # 碼頭下水階梯
    for z0 in (44, 120):
        for i in range(4):
            for z in range(z0, z0 + 3):
                W.put(26 + 0, G - i, z, AIR) if False else None
        for z in range(z0, z0 + 3):
            for i, x in enumerate((29, 28, 27, 26)):
                W.box(x, G - i + 1, z, x, G, z, AIR)
                W.put(x, G - i, z, stairs('sandstone_stairs', 'e'))
                if G - i <= SEA: W.w2[x, G - i, z] = True
                for y in range(G - i + 1, SEA + 1): W.put(x, y, z, WATER)


# ================= 空中花園 =================
def maps():
    X, Z = np.meshgrid(np.arange(SX), np.arange(SZ), indexing='ij')
    D = []
    for k in range(NL):
        x0, z0, x1, z1 = rect(k)
        D.append(np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Z - z0, z1 - Z)))
    K = np.full((SX, SZ), -1)
    for k in range(NL):
        K[D[k] >= 0] = k
    return D, K


D, K = maps()


def side(k, x, z):
    """格子在第 k 層矩形的哪一邊（最近的邊）；角落回 None。"""
    x0, z0, x1, z1 = rect(k)
    ds = {'w': x - x0, 'e': x1 - x, 'n': z - z0, 's': z1 - z}
    m = min(ds.values())
    ks = [s for s, v in ds.items() if v == m]
    return ks[0] if len(ks) == 1 else None


def tcoord(k, s, x, z):
    x0, z0, x1, z1 = rect(k)
    if s in 'ns': return x, x - x0, x1 - x
    return z, z - z0, z1 - z


def is_cascade(s, t, k):
    for c in casc_t(k, s):
        if abs(t - c) <= 1: return True
    return False


def in_trench_x(x, pad=0): return TR[0] - 1 - pad <= x <= TR[1] + 1 + pad


def bed_layout(k):
    """回傳 (植床欄 set, 水渠欄, 步道欄 set)"""
    if k == NL - 1:
        return set(range(1, 4)), 4, {5, 6}
    return set(range(1, 6)), 6, {7, 8}


def gardens():
    xs, zs = np.nonzero(K >= 0)
    # 1) 量體
    for x, z in zip(xs.tolist(), zs.tolist()):
        top = YT[K[x, z]]
        W.a[x, G + 1:top + 1, z] = PM
        W.a[x, G - 1:G + 1, z] = PM
    # 2) 牆面＋迴廊
    for m in range(NL):
        yb = ybase(m)
        x0, z0, x1, z1 = rect(m)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                d = D[m][x, z]
                if d > 5: continue
                s = side(m, x, z)
                if d == 0:
                    face_cell(m, x, z, s, yb)
                elif 1 <= d <= 4 and s is not None:
                    _, ta, tb = tcoord(m, s, x, z)
                    if min(ta, tb) < 1: continue
                    for r in range(1, 6): W.put(x, yb + r, z, AIR)
                    if d == 1: W.put(x, yb + 6, z, stairs('mud_brick_stairs', s, True))
                    elif d == 4: W.put(x, yb + 6, z, stairs('mud_brick_stairs', OPP[s], True))
                    else: W.put(x, yb + 6, z, AIR)
                    W.put(x, yb + 7, z, BR)
                    # 地板
                    W.put(x, yb, z, B('red_sandstone') if d in (2, 3) and (x + z) % 4 == 0 else (CS if d in (2, 3) else SS))
                elif d == 5 and s is not None:
                    _, ta, tb = tcoord(m, s, x, z)
                    if min(ta, tb) < 1: continue
                    for r in range(1, 7): W.put(x, yb + r, z, wall_mix())
                    W.put(x, yb + 3, z, glazed())
                elif 1 <= d <= 4 and s is None:
                    # 迴廊轉角：整格挖空，頂以磚
                    for r in range(1, 7): W.put(x, yb + r, z, AIR)
                    W.put(x, yb + 7, z, BR)
                    W.put(x, yb, z, SS)
    gallery_details()


def face_cell(m, x, z, s, yb):
    t, ta, tb = tcoord(m, s, x, z) if s else (0, 0, 0)
    corner = s is None or min(ta, tb) < 3
    ph = ta % 5
    opening = (not corner) and ph in (2, 3, 4) and not is_cascade(s, t, m) and not (s == 's' and in_trench_x(x, 2))
    for r in range(1, 10):
        y = yb + r
        if r == 9:
            W.put(x, y, z, SS); continue
        if r == 8:
            W.put(x, y, z, QZ if (t % 4 == 0 and not corner) else glazed()); continue
        if r == 7:
            W.put(x, y, z, CS if opening else pier_mix()); continue
        if opening:
            if r <= 5: W.put(x, y, z, AIR)
            else:
                asc = ('w' if s in 'ns' else 'n') if ph == 2 else (('e' if s in 'ns' else 's') if ph == 4 else None)
                W.put(x, y, z, stairs('mud_brick_stairs', asc, True) if asc else AIR)
        else:
            if r == 1: W.put(x, y, z, BR)
            elif corner and r in (3, 6): W.put(x, y, z, CH)
            else: W.put(x, y, z, pier_mix())


def gallery_details():
    """迴廊：燈、長椅、盆栽、發光漿果藤、壁龕。"""
    for m in range(NL):
        yb = ybase(m)
        x0, z0, x1, z1 = rect(m)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                d = D[m][x, z]; s = side(m, x, z)
                if s is None or d not in (2, 3, 4, 5): continue
                t, ta, tb = tcoord(m, s, x, z)
                if min(ta, tb) < 6: continue
                if s == 's' and in_trench_x(x, 1): continue
                ph = ta % 5
                if d in (2, 3) and ph == 3 and d == 2:
                    W.put(x, yb + 6, z, LANT_H)
                if d == 3 and ph == 0 and rng.random() < 0.5:
                    W.put(x, yb + 6, z, B('cave_vines_body_with_berries', growing_plant_age=1))
                    W.put(x, yb + 5, z, B('cave_vines_head_with_berries', growing_plant_age=1))
                if d == 4:
                    if ph in (1, 2) and (t // 10) % 2 == 0:
                        W.put(x, yb + 1, z, stairs('jungle_stairs', OPP[s]))   # 長椅背靠內牆
                    elif ph == 3:
                        W.put(x, yb + 1, z, rng.choice([B('flowering_azalea'), B('azalea'), B('decorated_pot', direction=0)]))
                    elif ph == 0 and (t // 10) % 2 == 1:
                        W.put(x, yb + 1, z, B('barrel', facing_direction=1))
                        W.put(x, yb + 2, z, B('flower_pot'))
                if d == 5 and ph == 3:
                    # 壁龕：凹一格放燈
                    dx, dz = OUTV[s]
                    W.put(x, yb + 2, z, AIR); W.put(x, yb + 3, z, AIR)
                    W.put(x, yb + 2, z, LANT)
                    W.put(x, yb + 4, z, GOLD if (t // 5) % 3 == 0 else CH)


def decks():
    """平台：女兒牆、植床、水渠、步道。"""
    for k in range(NL):
        beds, ch, walk = bed_layout(k)
        y = YT[k]
        x0, z0, x1, z1 = rect(k)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if K[x, z] != k: continue
                c = D[k][x, z]
                s = side(k, x, z)
                tt = x + z if s is None else tcoord(k, s, x, z)[0]
                if c == 0:
                    W.put(x, y, z, SS)
                    if s is None:   # 角塔
                        W.box(x, y + 1, z, x, y + 3, z, CH); W.put(x, y + 4, z, LANT)
                    else:
                        merlon_row(x, y + 1, z, tt)
                elif c in beds:
                    W.put(x, y, z, GRASS); W.put(x, y - 1, z, DIRT)
                elif c == ch:
                    W.put(x, y, z, WATER); W.put(x, y - 1, z, BR)
                    if rng.random() < 0.08: W.put(x, y + 1, z, B('waterlily'))
                elif c in walk:
                    W.put(x, y, z, pave(x, z))
                else:
                    W.put(x, y, z, pave(x, z))   # 頂層廣場
        # 水渠在轉角連成環；角落 4 格
    # 角塔之外每層轉角放銅火盆
    for k in range(NL):
        x0, z0, x1, z1 = rect(k); y = YT[k]
        _, _, walk = bed_layout(k)
        w = max(walk)
        for (x, z) in ((x0 + w, z0 + w), (x1 - w, z0 + w), (x0 + w, z1 - w), (x1 - w, z1 - w)):
            if K[x, z] == k:
                W.put(x, y + 1, z, B('campfire'))


def stair_trench():
    for m in range(NL):
        s0 = rect(m)[3]
        yb = ybase(m)
        for j in range(9):
            z = s0 - j; h = yb + 1 + j
            for x in range(TR[0], TR[1] + 1):
                W.box(x, yb + 1, z, x, h - 1, z, CS)
                W.put(x, h, z, stairs('sandstone_stairs', 'n') if j < 8 else pave(x, z))
                top = yb + 6 if j == 0 else SY - 1
                W.box(x, h + 1, z, x, top, z, AIR)
            for x in (TR[0] - 1, TR[1] + 1):
                mt = YT[K[x, z]] if K[x, z] >= 0 else G
                W.box(x, yb + 1, z, x, mt, z, wall_mix())
                if j < 7:
                    W.put(x, mt + 1, z, MBW if (j % 3) else CH)
                    if j % 3 == 0: W.put(x, mt + 2, z, LANT)
            if j == 0:   # 門洞拱
                W.put(TR[0], yb + 6, z, stairs('sandstone_stairs', 'w', True))
                W.put(TR[1], yb + 6, z, stairs('sandstone_stairs', 'e', True))
                for x in range(TR[0], TR[1] + 1):
                    W.put(x, yb + 7, z, CH if x in TR else CS)
                    W.put(x, yb + 8, z, GOLD if x in (95, 96) else glazed())
    # 地面起步前的兩座守門石獸座
    for x in (89, 102):
        W.box(x, G + 1, 129, x, G + 2, 129, CH)
        W.put(x, G + 3, 129, GOLD)


def cascades():
    """瀑布：牆內一格水源 → 前方落下 → 下層兩格深水池。"""
    srcs = []
    for m in range(NL):
        yb = ybase(m); x0, z0, x1, z1 = rect(m)
        for s in 'nsew':
            for t in casc_t(m, s):
                if s == 'n': fx, fz = t, z0
                elif s == 's': fx, fz = t, z1
                elif s == 'w': fx, fz = x0, t
                else: fx, fz = x1, t
                dx, dz = OUTV[s]
                W.put(fx, yb + 8, fz, WATER); srcs.append((fx, yb + 8, fz))
                W.put(fx, yb + 7, fz, CH)
                W.put(fx, yb + 9, fz, GOLD)    # 平台口金色獸首
                # 池：外側一格、沿牆 3 格
                for u in (-1, 0, 1):
                    px = fx + dx + (u if s in 'ns' else 0); pz = fz + dz + (u if s in 'ew' else 0)
                    W.put(px, yb, pz, WATER); W.put(px, yb - 1, pz, WATER); W.put(px, yb - 2, pz, BR)
                    for r in range(1, 9): W.put(px, yb + r, pz, AIR)
                    # 池外側再圍一圈（地面層）
                    if m == 0:
                        ox, oz = px + dx, pz + dz
                        W.put(ox, yb + 1, oz, MBW)
                for u in (-2, 2):
                    px = fx + dx + (u if s in 'ns' else 0); pz = fz + dz + (u if s in 'ew' else 0)
                    W.put(px, yb + 1, pz, B('mud_brick_wall')); W.put(px, yb + 2, pz, B('flower_pot'))
    return srcs


def vines():
    for m in range(NL):
        yb = ybase(m); x0, z0, x1, z1 = rect(m)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if D[m][x, z] != 0: continue
                s = side(m, x, z)
                if s is None: continue
                t, ta, tb = tcoord(m, s, x, z)
                if min(ta, tb) < 3: continue
                if s == 's' and in_trench_x(x, 3): continue
                if any(abs(t - c) <= 2 for c in casc_t(m, s)): continue
                dx, dz = OUTV[s]; vx, vz = x + dx, z + dz
                ph = ta % 5
                if ph in (2, 3, 4):
                    L = rng.choice([1, 2, 2])
                else:
                    L = rng.choice([3, 4, 5, 6, 6])
                if rng.random() < 0.25: continue
                v = B('vine', vine_direction_bits=VINE_BIT[s])
                for r in range(8, 8 - L, -1):
                    if W.get(vx, yb + r, vz) == AIR and W.get(x, yb + r, z) != AIR:
                        W.put(vx, yb + r, vz, v)
                # 垂落的樹葉簇（掛在女兒牆外）
                if ph in (0, 1) and rng.random() < 0.3 and m >= 0:
                    lf = rng.choice([B('azalea_leaves'), B('azalea_leaves_flowered'), B('jungle_leaves')])
                    if W.get(vx, yb + 9, vz) == AIR: W.put(vx, yb + 9, vz, lf)


# ---------- 植物 ----------
TRUNKS = []


def palm(x, y, z, h=None):
    h = h or rng.randint(6, 9)
    lean = rng.choice(list(DIRS.values()) + [(0, 0)] * 2)
    lx, lz = 0, 0
    for i in range(h):
        if i == h // 2 + 1: lx, lz = lean
        W.put(x + lx, y + i, z + lz, B('jungle_log'))
    cx, cy, cz = x + lx, y + h, z + lz
    lf = B('jungle_leaves')
    W.put(cx, cy, cz, lf)
    for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        for i, dy in ((1, 0), (2, 0), (3, -1), (4, -2)):
            W.put(cx + dx * i, cy + dy, cz + dz * i, lf, keep=True)
    for dx, dz in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
        for i, dy in ((1, 0), (2, -1), (3, -2)):
            W.put(cx + dx * i, cy + dy, cz + dz * i, lf, keep=True)
    W.put(cx, cy + 1, cz, lf)
    # 椰棗串（橙色陶土當果串）
    for dx, dz in rng.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], 2):
        W.put(cx + dx, cy - 1, cz + dz, B('orange_terracotta'), keep=True)


def cypress(x, y, z):
    h = rng.randint(8, 11)
    for i in range(h): W.put(x, y + i, z, B('spruce_log'))
    lf = B('spruce_leaves')
    for i in range(2, h + 2):
        W.put(x, y + i, z, lf, keep=True)
        if i < h:
            for dx, dz in DIRS.values(): W.put(x + dx, y + i, z + dz, lf, keep=True)
        if 3 <= i <= h - 3 and rng.random() < 0.5:
            dx, dz = rng.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)]); W.put(x + dx, y + i, z + dz, lf, keep=True)
    W.put(x, y + h + 2, z, lf)


def fruit(x, y, z):
    h = rng.randint(2, 3)
    for i in range(h): W.put(x, y + i, z, B('dark_oak_log'))
    lf = rng.choice([B('azalea_leaves_flowered'), B('azalea_leaves'), B('cherry_leaves')])
    lf2 = B('azalea_leaves')
    for dy in range(0, 3):
        r = 2 if dy == 1 else 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r + (1 if dy == 1 else 0) and rng.random() < 0.9:
                    W.put(x + dx, y + h + dy, z + dz, lf if rng.random() < 0.6 else lf2, keep=True)


FLOWERS = None


def understory(x, y, z):
    global FLOWERS
    if FLOWERS is None:
        FLOWERS = [B(n) for n in ('poppy', 'red_tulip', 'pink_tulip', 'allium', 'cornflower', 'oxeye_daisy', 'blue_orchid', 'lily_of_the_valley', 'dandelion')]
    r = rng.random()
    if r < 0.30: W.put(x, y, z, B('short_grass'))
    elif r < 0.52: W.put(x, y, z, rng.choice(FLOWERS))
    elif r < 0.62: W.put(x, y, z, rng.choice([B('azalea'), B('flowering_azalea')]))
    elif r < 0.70:
        n = rng.choice(['rose_bush', 'peony', 'large_fern', 'tall_grass'])
        if W.get(x, y + 1, z) == AIR:
            W.put(x, y, z, B(n, upper_block_bit=False)); W.put(x, y + 1, z, B(n, upper_block_bit=True))
    elif r < 0.76: W.put(x, y, z, B('fern'))


def far_from_trunks(x, z, dmin):
    return all(max(abs(x - a), abs(z - b)) >= dmin for a, b in TRUNKS)


def plant_beds():
    for k in range(NL):
        beds, ch, walk = bed_layout(k)
        mid = sorted(beds)[len(beds) // 2]
        y = YT[k] + 1
        x0, z0, x1, z1 = rect(k)
        cells = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1) if K[x, z] == k and D[k][x, z] in beds]
        rng.shuffle(cells)
        for x, z in cells:
            if D[k][x, z] == mid and W.get(x, y - 1, z) == GRASS and far_from_trunks(x, z, 4) and not in_trench_x(x, 1):
                r = rng.random()
                TRUNKS.append((x, z))
                if r < 0.45: palm(x, y, z)
                elif r < 0.72: cypress(x, y, z)
                else: fruit(x, y, z)
        for x, z in cells:
            if W.get(x, y - 1, z) == GRASS and W.get(x, y, z) == AIR:
                understory(x, y, z)


def crypt():
    """L0 內部拱頂地庫：14 間拱室＋三孔井（Koldewey 復原說）。"""
    y0 = G + 1
    W.box(60, y0, 70, 88, y0 + 6, 100, PM)
    # 中央東西走廊
    W.box(60, y0, 84, 90, y0 + 4, 86, AIR)
    for x in range(60, 91):
        W.put(x, y0 + 4, 84, stairs('mud_brick_stairs', 'n', True)); W.put(x, y0 + 4, 86, stairs('mud_brick_stairs', 's', True))
        for z in (84, 85, 86): W.put(x, y0 - 1, z, CS if z == 85 else SS)
        if x % 5 == 0: W.put(x, y0 + 4, 85, LANT_H)
    for i in range(7):
        xa = 60 + 4 * i
        for (za, zb, dz) in ((71, 83, 'n'), (87, 99, 's')):
            W.box(xa, y0, za, xa + 2, y0 + 3, zb, AIR)
            for z in range(za, zb + 1):
                W.put(xa, y0 + 4, z, stairs('mud_brick_stairs', 'w', True)); W.put(xa + 1, y0 + 4, z, AIR); W.put(xa + 2, y0 + 4, z, stairs('mud_brick_stairs', 'e', True))
                W.put(xa + 1, y0 + 5, z, BR)
                W.put(xa + 1, y0 - 1, z, SS)
            door_z = 83 if dz == 'n' else 87
            W.put(xa + 1, y0, door_z + (1 if dz == 'n' else -1), AIR); W.put(xa + 1, y0 + 1, door_z + (1 if dz == 'n' else -1), AIR)
            # 儲藏
            far = za if dz == 'n' else zb
            for x in (xa, xa + 2):
                for z in range(min(za, zb), max(za, zb) + 1, 3):
                    if i == 0 and dz == 'n': continue
                    W.put(x, y0, z, rng.choice([B('barrel', facing_direction=1), B('hay_block'), B('decorated_pot', direction=0), B('barrel', facing_direction=1)]))
            W.put(xa + 1, y0 + 3, far, LANT_H)
    # 三孔井（西北拱室）
    for z in (74, 77, 80):
        W.box(60, 3, z, 62, y0 - 1, z, BR)
        W.box(61, 3, z, 61, G, z, WATER)
        W.put(60, y0, z, MBW); W.put(62, y0, z, MBW)
        W.put(61, y0 + 3, z, B('iron_chain')); W.put(61, y0 + 2, z, B('cauldron', cauldron_liquid='water', fill_level=6))
    # 南北走廊接 L0 南迴廊
    W.box(89, y0, 87, 90, y0 + 3, 122, AIR)
    for z in range(87, 123):
        W.put(89, y0 - 1, z, SS); W.put(90, y0 - 1, z, SS)
        if z % 6 == 0: W.put(89, y0 + 3, z, LANT_H)
    W.put(89, y0 + 2, 122, CH); W.put(90, y0 + 2, 122, CH)


def top_level():
    """頂層：蓄水池、涼亭。"""
    y = YT[-1]
    # 蓄水池 x87–92 z75–82
    W.box(87, y + 1, 75, 92, y + 5, 82, MB)
    W.box(88, y + 1, 76, 91, y + 4, 81, WATER)
    for x in range(87, 93):
        for z in (75, 82): W.put(x, y + 5, z, MBS if x % 2 else CS)
    for z in range(75, 83):
        for x in (87, 92): W.put(x, y + 5, z, MBS if z % 2 else CS)
    for x in range(87, 93):
        W.put(x, y + 3, 82, glazed()); W.put(x, y + 3, 75, glazed())
    W.put(92, y + 3, 78, GOLD)
    # 涼亭 x97–104 z74–80
    x0, x1, z0, z1 = 97, 104, 74, 80
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            W.put(x, y, z, LAP if (x + z) % 2 else QZ)
            W.put(x, y + 1, z, AIR)
    for x in (x0, x0 + 3, x0 + 4, x1):
        for z in (z0, z1):
            if x in (x0, x1) or (x - x0) in (3, 4):
                W.box(x, y + 1, z, x, y + 4, z, B('quartz_pillar'))
                W.put(x, y + 5, z, CH)
    for z in (z0 + 3,):
        for x in (x0, x1): W.box(x, y + 1, z, x, y + 4, z, B('quartz_pillar')); W.put(x, y + 5, z, CH)
    W.box(x0, y + 6, z0, x1, y + 6, z1, CS)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                W.put(x, y + 5, z, glazed() if W.get(x, y + 5, z) == AIR else W.get(x, y + 5, z))
                merlon_row(x, y + 7, z, x + z, QZ, B('smooth_quartz_slab'))
    W.box(x0 + 1, y + 7, z0 + 1, x1 - 1, y + 7, z1 - 1, B('jungle_leaves'))   # 屋頂花園
    W.put(x0 + 3, y + 8, z0 + 3, B('flowering_azalea')); W.put(x0 + 5, y + 8, z0 + 2, B('azalea'))
    W.put((x0 + x1) // 2, y + 5, (z0 + z1) // 2, LANT_H)
    # 王座與地毯
    W.put(100, y + 1, 75, stairs('jungle_stairs', 'n')); W.put(101, y + 1, 75, stairs('jungle_stairs', 'n'))
    W.put(99, y + 1, 75, GOLD); W.put(102, y + 1, 75, GOLD)
    for z in range(76, 81):
        W.put(100, y + 1, z, B('red_carpet')); W.put(101, y + 1, z, B('red_carpet'))
    for p in ((98, 79), (103, 79), (98, 76), (103, 76)):
        W.put(p[0], y + 1, p[1], B('flowering_azalea'))
    # 廣場四角大花盆與火盆
    for p in ((94, 76), (94, 81), (105, 83), (93, 84)):
        if W.get(p[0], y + 1, p[1]) == AIR: W.put(p[0], y + 1, p[1], B('campfire'))


# ================= 提水系統 =================
def ring(cx, cy, cz, r, plane, fn):
    pts = set()
    for i in range(int(2 * math.pi * r * 3)):
        a = 2 * math.pi * i / int(2 * math.pi * r * 3)
        u, v = round(r * math.cos(a)), round(r * math.sin(a))
        pts.add((u, v))
    for u, v in pts:
        if plane == 'xy': fn(cx + u, cy + v, cz)
        else: fn(cx + u, cy, cz + v)


def tower():
    x0, x1, z0, z1 = 27, 37, 75, 85
    top = 59
    # 地下集水井
    W.box(x0, 1, z0, x1, G, z1, BR)
    W.box(x0 + 1, 2, z0 + 1, x1 - 1, SEA, z1 - 1, WATER)
    W.box(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, BR)
    W.box(x0 + 1, G, z0 + 1, x1 - 1, G, z1 - 1, AIR)
    # 進水口接河
    for z in range(79, 82):
        for y in range(3, SEA + 1):
            W.put(26, y, z, WATER); W.put(27, y, z, WATER)
    # 塔身
    for y in range(G, top + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    W.put(x, y, z, BR if (y - G) % 9 == 0 else pier_mix())
                elif y > G:
                    W.put(x, y, z, AIR)
        # 高處拱窗（看得到鏈斗）
        if y > G + 4 and (y - G) % 9 in (3, 4, 5, 6):
            for u in (79, 80, 81):
                if (y - G) % 9 == 3 and u != 80: continue
                W.put(x0, y, u, AIR) if False else None
                W.put(x1, y, u, AIR)
            for u in (31, 32, 33):
                if (y - G) % 9 == 3 and u != 32: continue
                W.put(u, y, z0, AIR); W.put(u, y, z1, AIR)
        if (y - G) % 9 == 7:
            for x in range(x0, x1 + 1):
                for z in (z0 - 1, z1 + 1): W.put(x, y, z, glazed())
            for z in range(z0, z1 + 1):
                for x in (x0 - 1, x1 + 1): W.put(x, y, z, glazed())
    # 內部步道平台（z83–84）與梯子
    for y in range(G, top, 9):
        W.box(x0 + 1, y, 83, x1 - 1, y, 84, CS if y > G else CS)
        W.put(32, y, 84, AIR) if y > G else None
    for y in range(G + 1, top + 1):
        W.put(32, y, 84, W.ladder('n'))
    W.door(x1, G + 1, 83, 'jungle_door', 'e')
    W.door(x1, G + 1, 84, 'jungle_door', 'e', hinge=True)
    # 頂部機房
    W.box(x0, top, z0, x1, top, z1, CS)
    W.box(x0 + 1, top, 78, x1 - 1, top, 82, AIR)
    W.put(32, top, 84, AIR)
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), (x0, 80), (x1, 80)):
        W.box(x, top + 1, z, x, top + 9, z, B('stripped_jungle_log'))
    W.box(x0, top + 10, z0, x1, top + 10, z1, B('jungle_planks'))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1): merlon_row(x, top + 11, z, x + z)
    # 鏈斗輪（上輪、下輪）
    def rim(x, y, z): W.put(x, y, z, B('stripped_jungle_log', pillar_axis='z'))
    for cy in (63, 6):
        ring(32, cy, 80, 4, 'xy', rim)
        for i in range(-3, 4):
            W.put(32 + i, cy, 80, B('jungle_planks')); W.put(32, cy + i, 80, B('jungle_planks'))
        for i in (-2, 2):
            W.put(32 + i, cy + i, 80, B('jungle_fence')); W.put(32 + i, cy - i, 80, B('jungle_fence'))
        W.box(32, cy, 76, 32, cy, 84, B('stripped_jungle_log', pillar_axis='z'))
        W.put(32, cy, 80, B('stripped_jungle_log', pillar_axis='z'))
    # 兩股鏈與水斗
    for x, full in ((28, True), (36, False)):
        for y in range(7, 63):
            if W.get(x, y, 80) in (WATER, AIR, B('stripped_jungle_log', pillar_axis='z')):
                W.put(x, y, 80, B('iron_chain'))
            if y % 4 == 0 and 7 < y < 60:
                W.put(x, y, 80, B('cauldron', cauldron_liquid='water', fill_level=6) if full else B('cauldron'))
    for z in (79, 81):
        for y in range(54, 59): W.put(x1, y, z, BR)
    # 出水槽（接渡槽）
    W.put(x1, 57, 80, WATER); W.put(x1, 56, 80, BR)
    W.put(x1 - 1, 57, 80, B('cauldron', cauldron_liquid='water', fill_level=6))


def aqueduct():
    """渡槽：z79–81，槽底 y56、水 y57，自塔東行到頂層蓄水池。"""
    for x in range(38, 88):
        W.put(x, 56, 80, BR); W.put(x, 57, 80, WATER)
        for z in (79, 81):
            W.put(x, 56, z, BR); W.put(x, 57, z, MB if x % 6 else glazed()); W.put(x, 58, z, MBS)
        W.put(x, 55, 79, BR); W.put(x, 55, 80, BR); W.put(x, 55, 81, BR)
    W.put(87, 57, 80, WATER)
    # 橋墩與拱
    for px in range(40, 82, 8):
        for x in (px, px + 1):
            for z in (79, 80, 81):
                y = 54
                while y > 0 and W.get(x, y, z) in (AIR,) or W.name(x, y, z) in ('short_grass', 'tall_grass', 'poppy', 'fern', 'jungle_leaves', 'spruce_leaves', 'azalea_leaves', 'vine', 'azalea', 'flowering_azalea', 'water', 'waterlily'):
                    W.put(x, y, z, pier_mix() if (y % 6) else CS)
                    y -= 1
        for z in (79, 80, 81):
            W.put(px - 1, 54, z, stairs('mud_brick_stairs', 'e', True))
            W.put(px + 2, 54, z, stairs('mud_brick_stairs', 'w', True))


def screws():
    """阿基米德螺旋提水器：河 → 北側高架灌溉渠 y9。"""
    for zc in (10, 20):
        for x in range(18, 34):
            y = 4 + (x - 18) * 5 // 15
            W.put(x, y, zc, B('stripped_jungle_log', pillar_axis='x'))
            ph = x % 4
            off = [(1, 0), (0, 1), (-1, 0), (0, -1)][ph]
            W.put(x, y + off[0], zc + off[1], B('jungle_planks'))
            off2 = [(1, 0), (0, 1), (-1, 0), (0, -1)][(ph + 2) % 4]
            W.put(x, y + off2[0], zc + off2[1], B('jungle_slab', vertical_half='top') if off2[0] == 1 else B('jungle_planks'))
            if x % 5 == 0:
                for y2 in range(2, y - 1):
                    if W.get(x, y2, zc) in (WATER, AIR) or W.name(x, y2, zc) in ('seagrass', 'kelp'):
                        W.put(x, y2, zc, B('jungle_fence'))
        # 頂端搖柄
        W.put(34, 10, zc, B('jungle_fence')); W.put(34, 11, zc, B('jungle_fence'))
        W.put(33, 11, zc, B('jungle_planks'))
        # 出水箱與高架渠
        W.box(34, G, zc - 1, 37, 9, zc + 1, MB)
        W.put(35, 9, zc, WATER); W.put(36, 9, zc, WATER)
        for x in range(37, 150):
            W.put(x, G, zc, BR); W.put(x, 9, zc, WATER)
            W.put(x, G, zc - 1, MB); W.put(x, 9, zc - 1, MB if x % 5 else CS)
            W.put(x, G, zc + 1, MB); W.put(x, 9, zc + 1, MB if x % 5 else CS)
        W.box(150, G, zc - 1, 150, 9, zc + 1, MB)
        # 跨渠小橋
        for x in (70, 110):
            for z in (zc - 1, zc, zc + 1): W.put(x, 10, z, CSS)
            W.put(x, 9, zc - 2, stairs('sandstone_stairs', 's')); W.put(x, 9, zc + 2, stairs('sandstone_stairs', 'n'))


def sakia():
    """牛拉水車院（x31–41 z90–100）。"""
    cx, cz = 36, 95
    for x in range(31, 42):
        for z in range(90, 101):
            dd = math.hypot(x - cx, z - cz)
            if dd <= 5.5: W.put(x, G, z, CDIRT if 3.5 < dd else B('packed_mud'))
    ring(cx, 11, cz, 3, 'xz', lambda x, y, z: W.put(x, y, z, B('stripped_jungle_log', pillar_axis='x')))
    W.box(cx, G + 1, cz, cx, 12, cz, B('stripped_jungle_log'))
    for i in range(1, 6): W.put(cx + i, 10, cz, B('jungle_fence'))
    W.put(cx + 5, 9, cz, B('jungle_fence'))
    for x in range(30, 43):
        for z in (89, 101):
            if x % 2 == 0: W.put(x, G + 1, z, B('jungle_fence'))
    W.put(30, G + 1, 95, B('hay_block')); W.put(42, G + 1, 92, B('hay_block'))


# ================= 城牆、伊什塔爾門 =================
BULL = ["H.H.........",
        ".BB.........",
        "BBBBBBBBBBB.",
        ".BBBBBBBBBBT",
        ".BBBBBBBBB.T",
        "..L.L..L.L..",
        "..L.L..L.L.."]
DRAGON = [".C..........",
          "HHH.........",
          ".HH......TT.",
          "..NBBBBBBB.T",
          "..NBBBBBBB..",
          "..F.F...K.K.",
          "..F.F...K.K."]
LION = ["........MMM.",
        "T.BBBBBBMMMH",
        ".TBBBBBBBMMM",
        "..BBBBBBBB..",
        "..L.L..L.L..",
        "..L.L..L.L.."]
SPR_COL = {'B': 'yellow_terracotta', 'H': 'yellow_terracotta', 'L': 'yellow_terracotta', 'T': 'yellow_terracotta'}


def paint(sprite, cols, place, flip=False):
    for r, row in enumerate(sprite):
        if flip: row = row[::-1]
        for c, ch in enumerate(row):
            if ch != '.':
                place(c, r, B(cols[ch]))


def city_walls():
    gx0, gx1 = 84, 107
    # 內牆 z158–161
    for x in range(4, SX):
        if gx0 <= x <= gx1: continue
        for z in range(158, 162):
            base = G if x > 25 else G
            for y in range(G, 27):
                W.put(x, y, z, BR if (y - G) % 6 == 0 else wall_mix())
            if x <= 25:
                for y in range(G, 11): W.put(x, y, z, AIR if z in (159, 160) and y < 10 else W.get(x, y, z))
        for z in (158, 161): merlon_row(x, 27, z, x)
        W.put(x, 26, 159, CS); W.put(x, 26, 160, CS)
    # 外牆 z165–167
    for x in range(4, SX):
        if gx0 <= x <= gx1: continue
        for z in range(165, 168):
            for y in range(G, 22): W.put(x, y, z, BR if (y - G) % 6 == 0 else wall_mix())
        merlon_row(x, 22, 167, x); merlon_row(x, 22, 165, x)
    # 河上水門：牆下保留水
    for x in range(4, 26):
        for z in range(158, 168):
            for y in range(3, SEA + 1):
                W.put(x, y, z, WATER)
            W.put(x, G, z, AIR); W.put(x, G - 1, z, AIR) if False else None
            W.put(x, G, z, stairs('mud_brick_stairs', 'n', True) if z in (158, 165) else (stairs('mud_brick_stairs', 's', True) if z in (161, 167) else W.get(x, G, z)))
        for z in range(158, 168):
            for y in range(G - 0, G + 1):
                if z in (159, 160, 166):
                    W.put(x, y, z, AIR)
            W.put(x, G + 1, z, BR) if z in range(158, 162) or z in range(165, 168) else None
    # 城塔
    for tx in list(range(36, 80, 22)) + list(range(118, 190, 22)):
        for (za, zb, ytop) in ((155, 162, 31), (165, 170, 26)):
            for x in range(tx, tx + 6):
                for z in range(za, zb + 1):
                    for y in range(G, ytop): W.put(x, y, z, BR if (y - G) % 6 == 0 else wall_mix())
                    if x in (tx, tx + 5) or z in (za, zb): merlon_row(x, ytop, z, x + z)
            for x in range(tx + 1, tx + 5):
                W.put(x, ytop - 3, zb if zb == 170 else za, glazed())
    # 兩牆之間的軍道
    for x in range(26, SX):
        if gx0 <= x <= gx1: continue
        for z in range(162, 165): W.put(x, G, z, CDIRT if rng.random() < 0.6 else GRASS)
    # 護城河 z174–187
    for x in range(4, 188):
        for z in range(174, 188):
            W.box(x, 3, z, x, G, z, AIR)
            W.put(x, 2, z, SANDB)
            for y in range(3, SEA + 1): W.put(x, y, z, WATER)
        for z in (173, 188): W.box(x, 3, z, x, G, z, CS)
    for z in range(174, 188):
        W.box(188, 3, z, 188, G, z, CS)
    # 河與護城河交接
    for x in range(4, 26):
        for z in range(168, 190):
            W.box(x, 3, z, x, G, z, AIR)
            for y in range(3, SEA + 1): W.put(x, y, z, WATER)
    # 城門前橋
    for z in range(173, 189):
        for x in range(92, 100):
            W.put(x, G, z, pave(x, z)); W.put(x, G - 1, z, CS)
        W.put(91, G + 1, z, MBW); W.put(100, G + 1, z, MBW)
        W.put(91, G, z, CS); W.put(100, G, z, CS)
        if z % 5 == 0:
            for x in range(91, 101): W.box(x, 3, z, x, G - 2, z, CS)
            W.put(91, G + 2, z, LANT); W.put(100, G + 2, z, LANT)
    for x in range(92, 100):
        for z in range(189, 192): W.put(x, G, z, pave(x, z))


def ishtar():
    """伊什塔爾門：藍釉磚、黃色公牛與龍浮雕、白色階梯垛口。"""
    def blk(x0, x1, z0, z1, ytop):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(G, ytop + 1):
                    W.put(x, y, z, glazed())
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    merlon_row(x, ytop + 1, z, x + z, QZ, B('smooth_quartz_slab'))
                    W.put(x, ytop, z, QZ if (x + z) % 2 else LAP)
        # 底座與玫瑰花帶
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    W.put(x, G + 1, z, CS)
                    W.put(x, G + 2, z, QZ if (x + z) % 3 == 0 else LAP)
                    W.put(x, ytop - 2, z, QZ if (x + z) % 2 == 0 else YT_)
    # 後段主門樓 z152–163、前段 z164–172
    blk(86, 105, 151, 163, 36)
    blk(84, 89, 164, 172, 40); blk(102, 107, 164, 172, 40)
    blk(90, 101, 165, 170, 32)
    # 內側左右塔
    blk(82, 87, 150, 156, 41); blk(104, 109, 150, 156, 41)
    # 拱門通道 x93–98，y9–20
    for z in range(150, 173):
        for x in range(93, 99):
            for y in range(G + 1, 21): W.put(x, y, z, AIR)
            W.put(x, G, z, pave(x, z))
        W.put(93, 19, z, stairs('sandstone_stairs', 'w', True)); W.put(98, 19, z, stairs('sandstone_stairs', 'e', True))
        W.put(93, 20, z, LAP); W.put(98, 20, z, LAP)
        W.put(94, 20, z, stairs('sandstone_stairs', 'w', True)); W.put(97, 20, z, stairs('sandstone_stairs', 'e', True))
        if z % 4 == 0: W.put(95, 20, z, LANT_H)
    # 門框
    for z in (172, 170, 150):
        for y in range(G + 1, 21):
            for x in (92, 99):
                if W.get(x, y, z) != AIR: W.put(x, y, z, YT_ if y % 2 else QZ)
    # 浮雕：南面（z=172 塔面、z=170 中段面），朝外 = +z；動物向門口走
    def front(zf, x_from, x_to, rows, flipl):
        for i, ytop in enumerate(rows):
            spr, cols = (BULL, {'B': 'yellow_terracotta', 'H': 'smooth_quartz', 'L': 'yellow_terracotta', 'T': 'yellow_terracotta'}) if i % 2 == 0 else \
                        (DRAGON, {'C': 'gold_block', 'H': 'smooth_quartz', 'N': 'smooth_quartz', 'B': 'smooth_quartz', 'F': 'smooth_quartz', 'K': 'gold_block', 'T': 'smooth_quartz'})
            w = len(spr[0])
            for x0 in range(x_from, x_to - w + 2, w + 2):
                paint(spr, cols, lambda c, r, b: W.put(x0 + c, ytop - r, zf, b), flip=flipl)
    # 塔面寬 6，放不下 12 寬：塔面用直立的玫瑰花柱；主面中段 z=170 x90–101
    for x in (84, 89, 102, 107):
        for y in range(G + 3, 39, 3): W.put(x, y, 172, QZ)
    for (xa, xb) in ((85, 88), (103, 106)):
        for y in range(G + 5, 38, 7):
            for x in range(xa, xb + 1): W.put(x, y, 172, YT_)
            W.put(xa + 1, y + 1, 172, YT_); W.put(xb - 1, y + 1, 172, YT_)
            W.put(xa + 1, y + 2, 172, QZ); W.put(xb - 1, y + 2, 172, QZ)
    # 門樓立面：通道兩側各一列（x84–92 左、x99–107 右在 z=164 的側面不可見；改畫在後段門樓北面與前段中牆）
    for y0, spr_i in ((31, 0), (28, 1), (25, 0)):
        pass
    # 中牆 x90–101 z170 只有通道兩側各 1 格寬 → 浮雕畫在拱上方
    for x in range(90, 102):
        W.put(x, 22, 170, QZ if x % 2 else YT_)
    paint(BULL, {'B': 'yellow_terracotta', 'H': 'smooth_quartz', 'L': 'yellow_terracotta', 'T': 'yellow_terracotta'},
          lambda c, r, b: W.put(90 + c, 30 - r, 170, b))
    # 北面（城內面）z=150/151：寬面，畫三排公牛與龍
    def north_face(zf, xa, xb):
        rows = [33, 25, 17]
        for i, ytop in enumerate(rows):
            spr, cols = (BULL, {'B': 'yellow_terracotta', 'H': 'smooth_quartz', 'L': 'yellow_terracotta', 'T': 'yellow_terracotta'}) if i % 2 == 0 else \
                        (DRAGON, {'C': 'gold_block', 'H': 'smooth_quartz', 'N': 'smooth_quartz', 'B': 'smooth_quartz', 'F': 'smooth_quartz', 'K': 'gold_block', 'T': 'smooth_quartz'})
            for x0 in (xa, xb):
                if ytop < 21 and x0 + 12 > 92 and x0 < 99: continue
                paint(spr, cols, lambda c, r, b: W.put(x0 + c, ytop - r, zf, b), flip=(x0 > 95))
    north_face(151, 79 + 8, 99 + 0)
    # 通道內壁（x92 西壁、x99 東壁），朝內，獅與龍
    for x in (92, 99):
        for z0 in range(152, 170, 14):
            paint(DRAGON if (z0 // 14) % 2 else BULL,
                  {'C': 'gold_block', 'H': 'smooth_quartz', 'N': 'smooth_quartz', 'B': 'smooth_quartz', 'F': 'smooth_quartz', 'K': 'gold_block', 'T': 'smooth_quartz', 'L': 'yellow_terracotta'} if (z0 // 14) % 2 else
                  {'B': 'yellow_terracotta', 'H': 'smooth_quartz', 'L': 'yellow_terracotta', 'T': 'yellow_terracotta'},
                  lambda c, r, b: W.put(x, 17 - r, z0 + c, b), flip=(x == 99))
    # 門前火盆
    for x in (90, 101):
        W.put(x, G + 1, 174, B('mud_bricks')); W.put(x, G + 2, 174, B('campfire'))


def processional():
    """遊行大道 x88–103 z128–149，兩側獅子牆。"""
    for z in range(128, 151):
        for x in range(88, 104):
            W.put(x, G, z, (B('red_sandstone') if x in (88, 103) else (QZ if (z % 4 == 0 and x in (95, 96)) else pave(x, z))))
            W.put(x, G - 1, z, CS)
    for (xw, face, flip) in ((86, 87, False), (104, 104, True)):
        for z in range(131, 151):
            for x in (xw, xw + 1):
                for y in range(G, 16): W.put(x, y, z, glazed())
                merlon_row(x, 16, z, z, QZ, B('smooth_quartz_slab'))
            W.put(face, G + 1, z, QZ if z % 3 == 0 else YT_)
            W.put(face, 15, z, QZ if z % 3 == 0 else YT_)
        for z0 in range(132, 148, 14):
            paint(LION, {'B': 'smooth_sandstone', 'M': 'yellow_terracotta', 'H': 'yellow_terracotta', 'L': 'smooth_sandstone', 'T': 'smooth_sandstone'},
                  lambda c, r, b: W.put(face, 14 - r - 1, z0 + c, b), flip=flip)
        W.put(face, G + 3, 149, LANT) if False else None


# ================= 王宮 =================
def palace():
    x0, x1, z0, z1 = 156, 189, 28, 124
    H = 22
    # 外牆 2 厚，扶壁
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = min(x - x0, x1 - x, z - z0, z1 - z)
            if edge <= 1:
                for y in range(G, H): W.put(x, y, z, BR if (y - G) % 7 == 0 else wall_mix())
                if edge == 0: merlon_row(x, H, z, x + z)
            W.put(x, G, z, pave(x, z))
    # 扶壁凹槽
    for z in range(z0 + 2, z1 - 1, 4):
        for y in range(G + 1, H - 1):
            W.put(x0, y, z, AIR if False else BR)
            W.put(x0 - 1, y, z, MB) if y < H - 1 else None
            W.put(x1 + 1, y, z, MB) if x1 + 1 < SX else None
    # 中庭 x164–181 z36–74
    cx0, cx1, cz0, cz1 = 164, 181, 36, 74
    # 中庭周圍房間（一層，屋頂 y15）
    for x in range(x0 + 2, x1 - 1):
        for z in range(z0 + 2, 80):
            if cx0 <= x <= cx1 and cz0 <= z <= cz1: continue
            W.put(x, 15, z, B('mud_brick_slab', vertical_half='top'))
            W.put(x, 16, z, MBS if (x + z) % 7 == 0 else AIR)
    for x in range(cx0 - 1, cx1 + 2):
        for z in (cz0 - 1, cz1 + 1):
            for y in range(G + 1, 16): W.put(x, y, z, wall_mix())
            merlon_row(x, 16, z, x)
    for z in range(cz0 - 1, cz1 + 2):
        for x in (cx0 - 1, cx1 + 1):
            for y in range(G + 1, 16): W.put(x, y, z, wall_mix())
            merlon_row(x, 16, z, z)
    # 房間隔牆與門
    for z in range(z0 + 2, cz1 + 2, 8):
        for x in list(range(x0 + 2, cx0 - 1)) + list(range(cx1 + 2, x1 - 1)):
            for y in range(G + 1, 15): W.put(x, y, z, MB)
    for z in range(z0 + 6, cz1, 8):
        W.door(cx0 - 1, G + 1, z, 'jungle_door', 'e')
        W.door(cx1 + 1, G + 1, z, 'jungle_door', 'w')
        for (xa, xb) in ((x0 + 2, cx0 - 2), (cx1 + 2, x1 - 2)):
            W.put(xa + 1, G + 1, z - 2, B('barrel', facing_direction=1)); W.put(xa + 1, G + 1, z + 2, B('crafting_table') if z % 16 else B('loom', direction=0))
            W.put((xa + xb) // 2, 14, z, LANT_H)
            for xx in range(xa, xb + 1): W.put(xx, G + 1, z, B('red_carpet') if (xx + z) % 3 else B('blue_carpet')) if W.get(xx, G + 1, z) == AIR else None
    for x in range(cx0 - 1, cx1 + 2, 6):
        W.door(x + 3, G + 1, cz0 - 1, 'jungle_door', 's')
    # 北側房間（z30–34）
    for x in range(x0 + 2, x1 - 1, 7):
        for z in range(z0 + 2, cz0 - 1):
            for y in range(G + 1, 15): W.put(x, y, z, MB)
    # 中庭地坪與水池、棕櫚
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            W.put(x, G, z, (B('blue_glazed_terracotta', facing_direction=2) if (x + z) % 6 == 0 else pave(x, z)))
    W.box(170, G - 1, 50, 175, G, 60, CS)
    W.box(171, G - 1, 51, 174, G, 59, WATER)
    W.box(170, G - 2, 50, 175, G - 2, 60, BR)
    for (x, z) in ((166, 40), (179, 40), (166, 70), (179, 70), (166, 55), (179, 55)):
        W.put(x, G, z, GRASS); W.put(x, G - 1, z, DIRT); palm(x, G + 1, z, 7)
    # 王座廳 x158–187 z80–104，高 H
    hx0, hx1, hz0, hz1 = 158, 187, 80, 104
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            edge = min(x - hx0, hx1 - x, z - hz0, hz1 - z)
            if edge <= 1:
                for y in range(G + 1, H): W.put(x, y, z, wall_mix())
            else:
                for y in range(G + 1, H - 1): W.put(x, y, z, AIR)
                W.put(x, G, z, pave(x, z))
                if 171 <= x <= 174: W.put(x, G + 1, z, B('red_carpet'))
                W.put(x, H - 1, z, B('jungle_planks'))
            W.put(x, H, z, MB) if edge > 0 else None
    W.box(hx0, H - 1, hz0, hx1, H - 1, hz1, B('jungle_planks'))
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            edge = min(x - hx0, hx1 - x, z - hz0, z1 - z)
            W.put(x, H, z, PM if (x // 2 + z // 2) % 2 else MB)
            if x in (hx0, hx1) or z in (hz0, hz1):
                W.put(x, H, z, glazed()); merlon_row(x, H + 1, z, x + z, QZ, B('smooth_quartz_slab'))
    for x in range(hx0 + 4, hx1 - 3, 6):
        W.put(x, H + 1, (hz0 + hz1) // 2, B('campfire'))
    for x in range(hx0 + 2, hx1 - 1, 3):
        W.put(x, H - 2, (hz0 + hz1) // 2, B('iron_chain')); W.put(x, H - 3, (hz0 + hz1) // 2, LANT_H)
    # 北立面（面向中庭 z=79 外側 z=80）：藍釉＋棕櫚柱紋
    for x in range(hx0, hx1 + 1):
        for y in range(G + 1, H):
            W.put(x, y, hz0, glazed())
        W.put(x, G + 1, hz0, CS); W.put(x, H - 2, hz0, QZ if x % 2 else YT_)
        if x % 6 == 2:
            for y in range(G + 2, H - 4): W.put(x, y, hz0, YT_)
            W.put(x - 1, H - 4, hz0, QZ); W.put(x + 1, H - 4, hz0, QZ); W.put(x, H - 4, hz0, GOLD)
            W.put(x - 1, H - 5, hz0, QZ); W.put(x + 1, H - 5, hz0, QZ)
        if x % 6 == 5:
            for y in range(G + 4, H - 6, 3): W.put(x, y, hz0, QZ)
    # 中央大門與兩側小門
    for (xa, xb, hh) in ((171, 174, 9), (163, 164, 6), (181, 182, 6)):
        for x in range(xa, xb + 1):
            for z in (hz0, hz0 + 1):
                for y in range(G + 1, G + 1 + hh): W.put(x, y, z, AIR)
            W.put(x, G + 1 + hh, hz0, GOLD)
    # 王座：南牆壁龕
    for x in range(171, 175):
        W.put(x, G + 1, hz1 - 2, B('smooth_quartz')); W.put(x, G + 1, hz1 - 3, B('smooth_quartz_slab'))
        for y in range(G + 1, G + 9): W.put(x, y, hz1 - 1, AIR if 172 <= x <= 173 and y < G + 8 else LAP)
    W.put(172, G + 2, hz1 - 2, stairs('quartz_stairs', 's')); W.put(173, G + 2, hz1 - 2, stairs('quartz_stairs', 's'))
    W.put(171, G + 2, hz1 - 2, GOLD); W.put(174, G + 2, hz1 - 2, GOLD)
    for (x, z) in ((169, hz1 - 3), (176, hz1 - 3), (161, 84), (184, 84), (161, 100), (184, 100)):
        W.put(x, G + 1, z, B('mud_bricks')); W.put(x, G + 2, z, B('campfire'))
    # 王座廳內部柱列（雪松木柱）
    for x in range(163, 184, 5):
        for z in (86, 98):
            W.box(x, G + 1, z, x, H - 2, z, B('stripped_spruce_log'))
            W.put(x, H - 2, z, CH)
    # 南側私殿 z106–122：小房間
    for x in range(x0 + 2, x1 - 1):
        for z in range(106, z1 - 1):
            W.put(x, 15, z, MBST)
    for x in range(x0 + 2, x1 - 1, 8):
        for z in range(106, z1 - 1):
            for y in range(G + 1, 15): W.put(x, y, z, MB)
    for z in (106,):
        for x in range(x0 + 2, x1 - 1):
            for y in range(G + 1, 15): W.put(x, y, z, MB)
    for xa in range(x0 + 2, x1 - 1, 8):
        xm = xa + 4
        if xm >= x1 - 1: continue
        W.door(xm, G + 1, 106, 'jungle_door', 'n')
        W.bed(xm - 2, G + 1, 110, 'n', 'red'); W.put(xm + 2, G + 1, 110, B('barrel', facing_direction=1))
        W.put(xm, 14, 114, LANT_H)
        for z in range(108, 121):
            for x in range(xa + 1, xa + 8):
                if W.get(x, G + 1, z) == AIR and (x + z) % 5 == 0: W.put(x, G + 1, z, B('blue_carpet'))
    # 王座廳與私殿之間門
    W.box(160, G + 1, hz1 - 1, 161, G + 2, hz1 + 2, AIR) if False else None
    W.door(160, G + 1, hz1, 'jungle_door', 's'); W.box(160, G + 1, hz1 - 1, 160, G + 2, hz1 - 1, AIR); W.box(160, G + 1, hz1 + 1, 160, G + 2, hz1 + 1, AIR)
    # 中庭南側通往王座廳的門廊 x171–174 z75–79
    for x in range(171, 175):
        for z in range(cz1 + 1, hz0):
            for y in range(G + 1, G + 10): W.put(x, y, z, AIR)
            W.put(x, G, z, B('red_carpet') if False else pave(x, z))
            W.put(x, G + 10, z, GOLD if x in (172, 173) else glazed())
    # 主入口：西牆 z50 通中庭
    for z in range(48, 53):
        for x in range(x0, cx0):
            for y in range(G + 1, G + 9): W.put(x, y, z, AIR)
            W.put(x, G, z, pave(x, z))
    for z in (47, 53):
        for y in range(G + 1, H + 3): W.put(x0 - 1, y, z, glazed())
        merlon_row(x0 - 1, H + 3, z, 0, QZ, B('smooth_quartz_slab'))
    for z in range(47, 54):
        W.put(x0, G + 9, z, GOLD if z == 50 else YT_)
    # 通往花園的道路
    for x in range(148, 156):
        for z in range(47, 54): W.put(x, G, z, pave(x, z))


# ================= 民宅 =================
def houses():
    blocks = [(32, 82, 132, 154), (108, 150, 132, 154)]
    cols = [(MB, PM), (PM, MB), (B('smooth_sandstone'), CS), (HC, MB)]
    n = 0
    for bx0, bx1, bz0, bz1 in blocks:
        x = bx0
        while x < bx1 - 6:
            z = bz0
            w = rng.randint(7, 10)
            while z < bz1 - 6:
                d = rng.randint(7, 9)
                if x + w > bx1 or z + d > bz1: break
                house(x, z, w, d, cols[n % len(cols)], n)
                n += 1
                z += d + 3
            x += w + 3
    # 街道：碎土小路
    for bx0, bx1, bz0, bz1 in blocks:
        for x in range(bx0, bx1 + 1):
            for z in range(bz0, bz1 + 1):
                if W.get(x, G, z) == GRASS and rng.random() < 0.7: W.put(x, G, z, rng.choice([CDIRT, B('packed_mud'), B('grass_path')]))


def house(x0, z0, w, d, mats, n):
    m1, m2 = mats
    x1, z1 = x0 + w - 1, z0 + d - 1
    h = 5 if n % 3 else 9
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(G + 1, G + h + 1):
                W.put(x, y, z, (m1 if rng.random() < 0.8 else m2) if wall else AIR)
            W.put(x, G, z, B('packed_mud'))
            W.put(x, G + h + 1, z, m1)
            if wall: merlon_row(x, G + h + 2, z, x + z) if (n % 2 == 0) else W.put(x, G + h + 2, z, MBW)
            if h == 9 and not wall: W.put(x, G + 5, z, B('jungle_planks'))
    # 門（朝南或北，朝街）
    dz_face = 's' if (z1 + 2) < 155 else 'n'
    dx = x0 + w // 2
    W.door(dx, G + 1, z1 if dz_face == 's' else z0, 'jungle_door', dz_face)
    W.put(dx, G + 3, z1 + 1 if dz_face == 's' else z0 - 1, stairs('jungle_stairs', 'n' if dz_face == 's' else 's', True))
    # 窗
    for y in (G + 3,) + ((G + 7,) if h == 9 else ()):
        for x in range(x0 + 2, x1 - 1, 3):
            if x != dx: W.put(x, y, z0, B('jungle_trapdoor', direction=3, open_bit=True)) if False else W.put(x, y, z0, AIR)
            if x != dx: W.put(x, y, z1, AIR)
    # 室內
    W.put(x0 + 1, G + 1, z0 + 1, B('barrel', facing_direction=1)); W.put(x1 - 1, G + 1, z0 + 1, B('cauldron', cauldron_liquid='water', fill_level=6))
    W.put(x0 + 1, G + 1, z1 - 1, B('crafting_table') if n % 2 else B('loom', direction=0))
    for x in range(x0 + 2, x1 - 1):
        for z in range(z0 + 2, z1 - 1):
            if (x + z) % 2 == 0: W.put(x, G + 1, z, B('red_carpet' if n % 2 else 'orange_carpet'))
    W.put(x1 - 1, G + h, z1 - 1, LANT_H)
    for y in range(G + 1, G + h + 1): W.put(x1 - 1, y, z0 + 1 if False else z1 - 1, W.ladder('n')) if False else None
    # 屋頂：梯子＋遮陽篷
    for y in range(G + 1, G + h + 1): W.put(x0 + 1, y, z0 + 2, W.ladder('s')) if False else None
    lx, lz = x1 - 1, z0 + 2
    for y in range(G + 1, G + h + 2): W.put(lx, y, lz, W.ladder('w'))
    if h == 9: W.put(lx, G + 5, lz, W.ladder('w'))
    for x in range(x0 + 1, x0 + 4):
        for z in range(z0 + 1, z0 + 4):
            W.put(x, G + h + 4, z, B(['white_wool', 'red_wool', 'blue_wool', 'yellow_wool'][n % 4]))
    for (x, z) in ((x0 + 1, z0 + 1), (x0 + 3, z0 + 1), (x0 + 1, z0 + 3), (x0 + 3, z0 + 3)):
        W.box(x, G + h + 2, z, x, G + h + 3, z, B('jungle_fence'))
    W.put(x1 - 2, G + h + 2, z1 - 1, B('flower_pot')); W.put(x0 + 2, G + h + 2, z1 - 1, B('decorated_pot', direction=0))


# ================= 地面植栽 =================
def ground_flora():
    occ = W.a
    def free(x, z, r=1):
        for xx in range(x - r, x + r + 1):
            for zz in range(z - r, z + r + 1):
                if not (0 <= xx < SX and 0 <= zz < SZ): return False
                if W.get(xx, G, zz) != GRASS or W.get(xx, G + 1, zz) != AIR: return False
        return True
    # 北側椰棗林
    for _ in range(900):
        x = rng.randint(32, 186); z = rng.randint(2, 30)
        if free(x, z, 1) and far_from_trunks(x, z, 5):
            TRUNKS.append((x, z)); palm(x, G + 1, z)
    # 其他空地：棕櫚、柏樹
    for _ in range(1600):
        x = rng.randint(30, 190); z = rng.randint(30, 156)
        if free(x, z, 2) and far_from_trunks(x, z, 7) and not (84 <= x <= 107 and z > 125) and not (38 <= x <= 153 and 26 <= z <= 133):
            TRUNKS.append((x, z))
            (palm if rng.random() < 0.7 else cypress)(x, G + 1, z)
    # 城外
    for _ in range(300):
        x = rng.randint(30, 186); z = rng.randint(188, 191)
        if free(x, z, 0) and far_from_trunks(x, z, 6):
            TRUNKS.append((x, z)); palm(x, G + 1, z, 6)
    for x in range(0, SX):
        for z in range(0, SZ):
            if W.get(x, G, z) == GRASS and W.get(x, G + 1, z) == AIR and rng.random() < 0.18:
                r = rng.random()
                W.put(x, G + 1, z, B('short_grass') if r < 0.75 else (B('fern') if r < 0.85 else rng.choice(FLOWERS)))


def life_points():
    return {}


def main():
    terrain()
    gardens()
    decks()
    crypt()
    stair_trench()
    top_level()
    srcs = cascades()
    vines()
    tower(); aqueduct(); screws(); sakia()
    plant_beds()
    city_walls(); ishtar(); processional(); palace(); houses()
    ground_flora()
    return W, srcs


if __name__ == '__main__':
    import time
    t = time.time(); main(); print('built', round(time.time() - t, 1), W.stats())
