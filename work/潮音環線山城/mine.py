"""金礦場：山腹礦坑（主坑室、支坑道、通山頂的豎井）、坑口礦場、運金礦車鐵路（坑室 → 東城舊機務段）。"""
import numpy as np
from core import *
from terrain import *
import town

FL = 46                       # 坑道地面方塊 y
TZ = 60                       # 主坑道與出坑鐵路的 z
CH = (128, 150, 52, 68)       # 主坑室 x0,x1,z0,z1
PORTAL_X = 164
YARD = (164, 175, 54, 66)
GX = 202                      # 黃金專用線南北段的 x
PIER_END = 240                # 黃金碼頭突堤末端 z


def prepare(W, T):
    """整平坑口礦場，並用石階工具做出坑外路基（之後才鋪軌）。"""
    B = W.B; a = W.a; h = T['h']
    x0, x1, z0, z1 = YARD
    T['reserved'][x0 - 1:x1 + 2, z0 - 1:z1 + 2] = True
    stone = W.mix((B('cobblestone'), 45), (B('gravel'), 25), (B('andesite'), 30))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(min(int(h[x, z]), FL) - 1, FL): a[x, y, z] = B('stone')
            a[x, FL, z] = stone(); a[x, FL - 1, z] = B('stone')
            a[x, FL + 1:FL + 14, z] = 0
            h[x, z] = FL
    # 黃金專用鐵路：坑口 → 沿台地下坡往東 → x=202 一路往南 → 從環線高架底下穿過 → 黃金碼頭突堤
    cells = town.line(170, TZ, 'e', GX - 169) + town.line(GX, TZ + 1, 's', PIER_END - TZ)
    saved = {}
    for (x, z) in cells:                               # 穿越環線處：暫時把高度視為地面 22，做出橋下箱涵
        for dx in (-1, 0, 1):
            c = (x + dx, z)
            if T['cor2'][c] and c not in saved:
                saved[c] = int(h[c]); h[c] = 22
    path = town.stair_path(W, T, cells, None, 1, rail=True)
    for c, v in saved.items():
        h[c] = v
        for y in range(23, 27): a[c[0], y, c[1]] = 0
        a[c[0], 22, c[1]] = B('stone_bricks'); a[c[0], 27, c[1]] = B('stone_bricks')
        T['street'][c] = False
    zs = sorted(c[1] for c in saved)
    for zz in (zs[0], zs[-1]):                         # 箱涵洞口門框
        for dx in (-2, 2):
            for y in range(23, 27):
                if a[GX + dx, y, zz] == 0: a[GX + dx, y, zz] = B('stone_bricks')
        for dx in range(-2, 3):
            if a[GX + dx, 27, zz] == 0: a[GX + dx, 27, zz] = B('stone_bricks')
    T['underpass'] = (GX, 23, zs[0] - 2)
    for (x, z), y in path: T['street'][x, z] = False
    T['mine_out'] = path


def build(W, T):
    B = W.B; a = W.a; h = T['h']
    rs = np.random.RandomState(88)
    gold, dgold, raw = B('gold_ore'), B('deepslate_gold_ore'), B('raw_gold_block')
    log = lambda ax='y': W.log('spruce_log', ax)
    lant = W.lantern(True)
    cx0, cx1, cz0, cz1 = CH
    air_cells = []
    def carve(x, y, z):
        if a[x, y, z] != 0: a[x, y, z] = 0
        air_cells.append((x, y, z))
    # ---- 主坑道：x=cx1..PORTAL_X-1，寬 5（z=58..62），淨高 4 ----
    for x in range(cx1, PORTAL_X):
        for z in range(TZ - 2, TZ + 3):
            for y in range(FL + 1, FL + 5): carve(x, y, z)
            a[x, FL, z] = B('gravel') if z != TZ and rs.rand() < 0.5 else B('cobblestone'); a[x, FL - 1, z] = B('stone')
        if (x - cx1) % 4 == 0:
            for z in (TZ - 2, TZ + 2):
                for y in range(FL + 1, FL + 4): a[x, y, z] = log()
            for z in range(TZ - 2, TZ + 3): a[x, FL + 4, z] = log('z')
        elif (x - cx1) % 4 == 2:
            a[x, FL + 4, TZ - 1] = lant
    # ---- 主坑室：不規則穹頂，留兩根岩柱 ----
    nz = fbm((SX, SZ), 9, 55, 2)
    mx, mz = (cx0 + cx1) / 2, (cz0 + cz1) / 2
    pillars = [(136, 56), (143, 65)]
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            d = ((x - mx) / ((cx1 - cx0) / 2 + 0.5)) ** 2 + ((z - mz) / ((cz1 - cz0) / 2 + 0.5)) ** 2
            if d > 1.0 + nz[x, z] * 0.15: continue
            if any(abs(x - px) <= 1 and abs(z - pz) <= 1 for px, pz in pillars): continue
            top = FL + int(4 + 5 * (1 - d) + nz[x, z] * 2)
            for y in range(FL + 1, top + 1): carve(x, y, z)
            a[x, FL, z] = [B('cobblestone'), B('gravel'), B('andesite'), B('stone')][rs.randint(4)]
            a[x, FL - 1, z] = B('stone')
    # ---- 支坑道 ----
    def drift(x0, z0, x1, z1, hgt=3):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                for y in range(FL + 1, FL + 1 + hgt): carve(x, y, z)
                a[x, FL, z] = B('cobblestone') if rs.rand() < 0.6 else B('gravel'); a[x, FL - 1, z] = B('stone')
    drift(139, 40, 141, cz0 + 1)                       # 北坑道
    drift(126, 66, 128, 75)                            # 通豎井
    drift(146, cz1 - 1, 148, 76)                       # 南坑道
    for (x, z, ax) in [(140, zz, 'x') for zz in range(42, cz0, 4)] + [(127, zz, 'x') for zz in range(69, 75, 4)] + [(147, zz, 'x') for zz in range(70, 76, 4)]:
        for dx in (-1, 1):
            for y in range(FL + 1, FL + 3): a[x + dx, y, z] = B('spruce_fence')
        for dx in (-1, 0, 1): a[x + dx, FL + 3, z] = log('x')
        a[x, FL + 2, z + 1] = lant if a[x, FL + 3, z + 1] != 0 else 0
    # ---- 金礦脈：所有挖空格相鄰的岩壁 ----
    rock = {B('stone'), B('andesite'), B('tuff'), B('cobblestone'), B('deepslate'), B('mossy_cobblestone'), B('calcite')}
    vein = fbm((SX, SZ), 6, 77, 2)
    seen = set(); n_ore = 0
    for (x, y, z) in air_cells:
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
            q = (x + dx, y + dy, z + dz)
            if q in seen: continue
            seen.add(q)
            if int(a[q]) in rock:
                r = rs.rand()
                p = 0.16 + max(0.0, vein[q[0], q[2]]) * 0.9 + (0.12 if cx0 <= q[0] <= cx1 else 0)
                if r < p: a[q] = gold if rs.rand() < 0.75 else dgold; n_ore += 1
                elif r < p + 0.03: a[q] = raw; n_ore += 1
    for (x, z) in ((140, 40), (139, 40), (141, 40), (146, 76), (147, 76), (148, 76)):      # 掌子面
        for y in range(FL + 1, FL + 4): a[x, y, z - 1 if z == 40 else z + 1] = gold if rs.rand() < 0.8 else raw
    # ---- 坑室設備 ----
    for (x, z) in ((131, 56), (132, 56), (131, 57), (134, 64), (135, 65), (148, 56)):       # 原金堆
        a[x, FL + 1, z] = raw
    a[131, FL + 2, 56] = raw
    for i, x in enumerate(range(137, 143)):                                                  # 北側工作台列
        a[x, FL + 1, 53] = [B('chest', cardinal_direction='south'), B('barrel', facing_direction=1), B('crafting_table'), B('blast_furnace', cardinal_direction='south'), B('blast_furnace', cardinal_direction='south'), B('chest', cardinal_direction='south')][i]
    a[144, FL + 1, 54] = B('anvil', cardinal_direction='south'); a[145, FL + 1, 54] = B('cauldron', fill_level=6, cauldron_liquid='water')
    for x in range(130, 136):                                                                # 木棧台（二層）
        for z in (65, 66):
            a[x, FL + 3, z] = W.slab('spruce_slab', True)
        if x in (130, 135):
            for y in (FL + 1, FL + 2): a[x, y, 65] = B('spruce_fence')
    a[136, FL + 1, 66] = B('scaffolding'); a[136, FL + 2, 66] = B('scaffolding'); a[136, FL + 3, 66] = B('scaffolding')
    a[132, FL + 4, 66] = B('barrel', facing_direction=1); a[133, FL + 4, 66] = raw
    for (x, z) in ((133, 58), (146, 62), (139, 62), (133, 62), (146, 58)):                   # 立燈
        a[x, FL + 1, z] = B('spruce_fence'); a[x, FL + 2, z] = B('spruce_fence'); a[x, FL + 3, z] = W.lantern()
    for px, pz in pillars: a[px, FL + 2, pz + 2] = B('glowstone') if a[px, FL + 2, pz + 2] != 0 else a[px, FL + 2, pz + 2]
    # ---- 豎井：通到山頂平台 ----
    sx, sz = 125, 73
    px, pg, pz = T['summit']
    top = pg
    for y in range(FL + 1, top + 1):
        a[sx, y, sz] = W.ladder('e')
        if a[sx - 1, y, sz] == 0: a[sx - 1, y, sz] = B('stone_bricks')
    a[sx, top + 1, sz] = 0; a[sx, top + 2, sz] = 0
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):                                       # 井架
        for y in range(top + 1, top + 5):
            if a[sx + dx, y, sz + dz] == 0: a[sx + dx, y, sz + dz] = B('spruce_fence')
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if a[sx + dx, top + 5, sz + dz] == 0: a[sx + dx, top + 5, sz + dz] = W.slab('spruce_slab') if (dx, dz) != (0, 0) else log('x')
    a[sx, top + 4, sz] = B('iron_chain')
    T['mine_shaft'] = (sx + 1, top + 1, sz)
    # ---- 坑口與礦場 ----
    x0, x1, z0, z1 = YARD
    for z in range(TZ - 3, TZ + 4):                                                           # 洞門
        for y in range(FL + 1, FL + 8):
            if abs(z - TZ) <= 2 and y <= FL + 4: continue
            if a[PORTAL_X - 1, y, z] != 0 or y <= FL + 6: a[PORTAL_X, y, z] = B('stone_bricks') if (y + z) % 3 else B('mossy_stone_bricks')
    for z in (TZ - 2, TZ + 2):
        for y in range(FL + 1, FL + 5): a[PORTAL_X, y, z] = log()
    for z in range(TZ - 2, TZ + 3): a[PORTAL_X, FL + 5, z] = log('z')
    a[PORTAL_X + 1, FL + 5, TZ] = B('gold_block'); a[PORTAL_X + 1, FL + 4, TZ - 1] = lant if False else 0
    a[PORTAL_X + 1, FL + 4, TZ + 2] = W.lantern(True) if False else 0
    for i, (x, z) in enumerate(((167, 63), (168, 63), (167, 64), (168, 64), (169, 64), (167, 65), (170, 63))):   # 礦石堆
        a[x, FL + 1, z] = raw if i % 3 else gold
    a[167, FL + 2, 64] = raw; a[168, FL + 2, 64] = gold
    for x in (171, 172, 173):                                                                 # 礦石斗（軌道旁）
        a[x, FL + 1, 62] = B('hopper', facing_direction=0, toggle_bit=False) if x != 172 else B('chest', cardinal_direction='north')
        a[x, FL + 2, 62] = raw if x != 172 else 0
    for (x, z) in ((165, 56), (174, 56), (165, 65), (174, 65)):
        a[x, FL + 1, z] = B('spruce_fence'); a[x, FL + 2, z] = B('spruce_fence'); a[x, FL + 3, z] = W.lantern()
    town.house(W, T, 167, 54, 6, 5, 's', FL, 1, W.rng, style=dict(color='ochre', roof='mud', rooftype='gable'))
    # 起重架
    for y in range(FL + 1, FL + 6): a[173, y, 64] = log()
    for x in range(170, 175): a[x, FL + 6, 64] = log('x')
    a[170, FL + 5, 64] = B('iron_chain'); a[170, FL + 4, 64] = B('iron_chain'); a[170, FL + 3, 64] = raw
    # ---- 機務段卸金台 ----
    G = 28
    for z in range(116, 123):
        a[219, G + 1, z] = raw if z % 2 else B('gold_block') if z == 118 else B('chest', cardinal_direction='west')
        if z % 3 == 0: a[219, G + 2, z] = raw
    a[215, G + 1, 122] = B('spruce_fence'); a[215, G + 2, 122] = B('spruce_fence'); a[215, G + 3, 122] = W.lantern()
    # ---- 鋪軌：坑室端 → 坑口 → 坑外路基 → 機務段 ----
    inner = [((x, TZ), FL) for x in range(cx0 + 4, 170)]
    path = inner + T['mine_out']
    red = B('redstone_block'); sb = B('stone_bricks')
    n = len(path)
    for i, ((x, z), y) in enumerate(path):
        p = path[i - 1] if i > 0 else None; q = path[i + 1] if i + 1 < n else None
        a[x, y + 1:y + 4, z] = 0
        def dirto(o):
            return {(1, 0): 'e', (-1, 0): 'w', (0, 1): 's', (0, -1): 'n'}[(o[0][0] - x, o[0][1] - z)]
        ds = {dirto(o) for o in (p, q) if o}
        up = [dirto(o) for o in (p, q) if o and o[1] > y]
        if len(ds) == 2 and ds not in ({'n', 's'}, {'e', 'w'}):
            assert not up and all(o[1] == y for o in (p, q)), ('彎軌處必須水平', x, y, z)
            a[x, y + 1, z] = B('rail', rail_direction={frozenset('se'): 6, frozenset('sw'): 7, frozenset('nw'): 8, frozenset('ne'): 9}[frozenset(ds)])
            a[x, y, z] = sb
            continue
        assert len(up) <= 1
        ax = 0 if ds <= {'n', 's'} else 1
        st = {'e': 2, 'w': 3, 'n': 4, 's': 5}[up[0]] if up else ax
        a[x, y + 1, z] = B('golden_rail', rail_direction=st, rail_data_bit=True)
        a[x, y, z] = red if (i % 3 == 0 or up) else sb
        if a[x, y - 1, z] == 0: a[x, y - 1, z] = sb
    (x, z), y = path[0]; a[x - 1, y + 1, z] = B('stone_bricks'); a[x - 1, y + 2, z] = B('spruce_fence')
    (x, z), y = path[-1]; a[x, y + 1, z + 1] = B('stone_bricks'); a[x, y + 2, z + 1] = B('spruce_fence')
    T['mine_path'] = path
    return dict(ore=n_ore, track=n, drop=path[0][1] - path[-1][1])


def verify(W, T):
    path = T['mine_path']; n = len(path)
    for i, ((x, z), y) in enumerate(path):
        k = W.get(x, y + 1, z); nm = W.names[k]
        assert nm in ('rail', 'golden_rail'), (x, y + 1, z, nm)
        d = W.pal[k][1]['rail_direction']
        assert W.get(x, y + 2, z) == 0 and W.get(x, y + 3, z) == 0, ('淨空', x, y + 2, z, W.names[W.get(x, y + 2, z)], W.names[W.get(x, y + 3, z)])
        assert W.names[W.get(x, y, z)] not in ('air', 'water', 'gravel')
        if i + 1 < n:
            (x2, z2), y2 = path[i + 1]
            assert abs(x2 - x) + abs(z2 - z) == 1 and abs(y2 - y) <= 1, (i, path[i], path[i + 1])
            dd = {(1, 0): 'e', (-1, 0): 'w', (0, 1): 's', (0, -1): 'n'}[(x2 - x, z2 - z)]
            if y2 > y: assert d == {'e': 2, 'w': 3, 'n': 4, 's': 5}[dd], (i, d)
            if y2 < y:
                d2 = W.pal[W.get(x2, y2 + 1, z2)][1]['rail_direction']
                assert d2 == {'e': 2, 'w': 3, 'n': 4, 's': 5}[OPP[dd]], (i, d2)
        if nm == 'golden_rail':
            # 8 格內要有紅石塊供電
            ok = any(W.names[W.get(path[j][0][0], path[j][1], path[j][0][1])] == 'redstone_block' for j in range(max(0, i - 6), min(n, i + 7)))
            assert ok, ('無供電', x, y, z)
    return n
