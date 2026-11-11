"""地標：海濱總站、教堂廣場、纜索鐵道、市場、港口、燈塔、山頂、山後小站、機務段。"""
import math
import numpy as np
from core import *
from terrain import *
import town


def _mats(W):
    B = W.B
    m = dict(
        cream=W.mix((B('smooth_sandstone'), 86), (B('cut_sandstone'), 14)),
        stone=W.mix((B('stone_bricks'), 70), (B('mossy_stone_bricks'), 12), (B('cracked_stone_bricks'), 10), (B('cobblestone'), 8)),
        white=W.mix((B('white_concrete'), 80), (B('calcite'), 20)),
        floor=lambda x, z: B('polished_andesite') if (x + z) % 2 else B('polished_diorite'),
    )
    return m


# ================================================================ 海濱總站
def main_station(W, T):
    B = W.B; a = W.a; M = _mats(W)
    x0, x1 = 106, 140
    G = 22                      # 地面
    P = RAIL_Y                  # 月台方塊 y
    pand, sst, dslab = B('polished_andesite'), B('smooth_stone'), B('dark_oak_slab')
    pane = B('glass_pane'); lant = W.lantern(True)
    # 清掉走廊邊的護欄
    for x in range(x0 - 2, x1 + 3):
        for z in (196, 200):
            a[x, P:P + 5, z] = 0
    # ---- 一樓大廳 z=188..195 ----
    for x in range(x0, x1 + 1):
        for z in range(188, 196):
            a[x, G, z] = M['floor'](x, z)
            a[x, G + 1:P - 1, z] = 0
            a[x, P - 1, z] = sst; a[x, P, z] = pand
        a[x, P, 196] = pand
    for y in range(G + 1, P - 1):
        for x in range(x0, x1 + 1):
            arch = (x - x0) % 4 != 0 and y <= G + 4
            a[x, y, 188] = 0 if arch else (M['stone']() if y == G + 1 else M['cream']())
            if (x - x0) % 4 in (1, 3) and y == G + 4:
                a[x, y, 188] = W.stairs('smooth_sandstone_stairs', 'w' if (x - x0) % 4 == 1 else 'e', True)
        for z in range(188, 196):
            for x in (x0, x1):
                a[x, y, z] = M['stone']() if y == G + 1 else M['cream']()
                if y in (G + 2, G + 3) and z in (190, 191, 193): a[x, y, z] = pane
    for x in range(x0 - 1, x1 + 2):          # 簷口
        a[x, P - 1, 187] = W.slab('smooth_sandstone_slab', True)
    # 柱與吊燈
    for x in range(x0 + 4, x1, 8):
        for y in range(G + 1, P - 1): a[x, y, 192] = B('stone_brick_wall') if y < P - 2 else B('stone_bricks')
        a[x + 2, P - 2, 190] = lant
    # 售票亭與長椅
    for x in range(132, 139):
        a[x, G + 1, 192] = W.slab('spruce_slab', True) if x % 2 else B('barrel', facing_direction=1)
        a[x, G + 3, 192] = W.slab('spruce_slab', True)
    a[131, G + 1, 192] = B('spruce_planks'); a[131, G + 2, 192] = B('spruce_fence'); a[131, G + 3, 192] = B('spruce_planks')
    for x in range(118, 130, 3):
        a[x, G + 1, 191] = W.stairs('spruce_stairs', 's'); a[x + 1, G + 1, 191] = W.stairs('spruce_stairs', 's')
    a[135, G + 1, 194] = B('bookshelf'); a[136, G + 1, 194] = W.facing('chest', 'n'); a[137, G + 1, 194] = B('lectern', cardinal_direction='north')
    # 樓梯上月台：z=193..194，x=109→116
    for i in range(8):
        x = 109 + i; y = G + 1 + i
        for z in (193, 194):
            for yy in range(G + 1, y): a[x, yy, z] = M['stone']()
            a[x, y, z] = W.stairs('stone_brick_stairs', 'e')
            a[x, y + 1:P + 4, z] = 0
    for z in (193, 194):
        a[108, P - 1:P + 1, z] = 0
        a[108, P + 1, z] = 0
    for x in range(107, 116):                 # 樓梯口欄杆
        a[x, P + 1, 192] = B('iron_bars')
    a[107, P + 1, 193] = B('iron_bars'); a[107, P + 1, 194] = B('iron_bars'); a[107, P, 193] = pand; a[107, P, 194] = pand
    # ---- 二樓候車室 x=114..132, z=188..191 ----
    F = Frame(W, 114, P + 1, 188, 19, 4, 's'); F._wm = M['cream']
    for ly in range(4):
        for lx in range(19):
            for lz in range(4):
                if lx in (0, 18) or lz in (0, 3):
                    F.put(lx, ly, lz, M['cream']())
    for lx in (3, 9, 15):                     # 通月台的門洞
        F.put(lx, 0, 3, 0); F.put(lx, 1, 3, 0)
    for lx in (2, 5, 7, 11, 13, 16):
        F.put(lx, 1, 0, pane); F.put(lx, 2, 0, pane)
        if lx not in (9,): F.put(lx, 1, 3, pane)
    for lx in (4, 10, 14):
        F.stairs(lx, 0, 1, 'spruce_stairs', 'n'); F.put(lx, 2, 1, lant) if False else None
    F.put(9, 3, 1, lant) if False else None
    town.roof_gable(F, 19, 4, 4, 'brick', 'x')
    for lx in (4, 9, 14): F.put(lx, 3, 2, B('lantern', hanging=True))
    # ---- 鐘塔 x=121..125, z=184..188 ----
    for y in range(G + 1, 47):
        for x in range(121, 126):
            for z in range(184, 189):
                rim = x in (121, 125) or z in (184, 188)
                corner = x in (121, 125) and z in (184, 188)
                if not rim:
                    a[x, y, z] = 0; continue
                a[x, y, z] = M['stone']() if (corner or y == G + 1) else M['cream']()
        if y in (33, 40):
            for x in range(120, 127):
                for z in range(183, 190):
                    if x in (120, 126) or z in (183, 189): a[x, y, z] = W.slab('smooth_sandstone_slab', True)
    for x in (122, 123, 124):                 # 穿堂入口
        for y in range(G + 1, G + 5):
            a[x, y, 184] = 0; a[x, y, 188] = 0
    for y in range(G + 1, G + 4):
        for z in (185, 186, 187): a[121, y, z] = M['cream'](); a[125, y, z] = M['cream']()
    black, quartz = B('black_concrete'), B('smooth_quartz')
    for y in range(41, 46):                   # 鐘面（南北兩面）
        for x in (122, 123, 124):
            for z in (184, 188):
                a[x, y, z] = quartz if y in (42, 43, 44) else a[x, y, z]
    for z in (184, 188):
        a[123, 43, z] = black; a[123, 44, z] = B('gold_block')
    for y in range(35, 39):
        for x in (123,):
            a[x, y, 184] = pane; a[x, y, 188] = pane
    for i in range(3):                        # 尖頂
        y = 47 + i
        for x in range(121 + i - 1, 126 - i + 1):
            for z in range(184 + i - 1, 189 - i + 1):
                lo, hi = 121 + i - 1, 125 - i + 1
                zl, zh = 184 + i - 1, 188 - i + 1
                if x == lo: a[x, y, z] = W.stairs('brick_stairs', 'e')
                elif x == hi: a[x, y, z] = W.stairs('brick_stairs', 'w')
                elif z == zl: a[x, y, z] = W.stairs('brick_stairs', 's')
                elif z == zh: a[x, y, z] = W.stairs('brick_stairs', 'n')
                else: a[x, y, z] = B('brick_block')
    a[123, 50, 186] = B('brick_block'); a[123, 51, 186] = B('lightning_rod', facing_direction=1)
    a[123, 46, 186] = B('glowstone')
    # ---- A 側月台雨棚 z=192..196 ----
    for x in range(x0, x1 + 1):
        for z in range(192, 197):
            if a[x, P + 4, z] == 0: a[x, P + 4, z] = dslab if (x + z) % 7 else W.slab('spruce_slab')
        if (x - x0) % 6 == 2:
            for y in range(P + 1, P + 4): a[x, y, 195] = B('dark_oak_fence')
            a[x, P + 3, 194] = lant
    for x in range(118, 131, 4):              # 月台長椅
        a[x, P + 1, 193] = W.stairs('spruce_stairs', 'n')
    # ---- B 側（面海）月台 z=200..203, x=110..136 ----
    for x in range(110, 137):
        pier = x % 8 in (0, 1)
        for z in range(200, 204):
            g = int(T['h'][x, z])
            if z > 200:
                if pier:
                    for y in range(g, P - 1): a[x, y, z] = M['stone']()
                else:
                    k = x % 8 - 2
                    a[x, P - 2, z] = M['stone']() if k not in (0, 5) else W.stairs('stone_brick_stairs', 'w' if k == 0 else 'e', True)
                a[x, P - 1, z] = sst
            a[x, P, z] = pand
            if a[x, P + 4, z] == 0: a[x, P + 4, z] = dslab
        a[x, P + 1, 203] = B('stone_brick_wall')
        if x % 6 == 2:
            for y in range(P + 1, P + 4): a[x, y, 202] = B('dark_oak_fence')
            a[x, P + 3, 201] = lant
    for i in range(9):                        # 下沙灘的樓梯
        x = 137 + i; y = P - i
        for z in (201, 202):
            g = int(T['h'][x, z])
            for yy in range(g, y): a[x, yy, z] = M['stone']()
            a[x, y, z] = W.stairs('stone_brick_stairs', 'w')
            a[x, y + 1:y + 4, z] = 0
        if i < 6: a[x, y + 1, 203] = B('stone_brick_wall'); a[x, y, 203] = M['stone']()
        for yy in range(int(T['h'][x, 203]), y):
            if i < 6: a[x, yy, 203] = M['stone']()
    # ---- 停靠拉桿：預設通電（直通），關掉就會在站內停車 ----
    for z, lz in ((197, 196), (199, 200)):
        for x in (122, 123):
            a[x, RAIL_Y, z] = B('golden_rail', rail_direction=1, rail_data_bit=True)
            if W.names[a[x, RAIL_Y - 1, z]] == 'redstone_block': a[x, RAIL_Y - 1, z] = B('stone_bricks')
        a[122, P + 1, lz] = B('lever', lever_direction='up_east_west', open_bit=True)
        a[124, P + 1, lz] = B('stone_brick_wall'); a[124, P + 2, lz] = W.lantern()
    T['levers'] = [(122, P + 1, 196), (122, P + 1, 200)]


# ================================================================ 纜索鐵道
def funicular(W, T):
    B = W.B; a = W.a
    path = T['stairs']['funi']
    red = B('redstone_block'); sb = B('stone_bricks')
    n = len(path)
    for i, ((x, z), y) in enumerate(path):
        up = i + 1 < n and path[i + 1][1] > y
        a[x, y + 1, z] = B('golden_rail', rail_direction=4 if up else 0, rail_data_bit=True)
        a[x, y, z] = red if i % 2 == 0 else sb
        a[x, y + 2:y + 5, z] = 0
    (x, z), y = path[0]
    a[x, y + 1, z + 1] = sb; a[x, y + 2, z + 1] = B('stone_brick_wall'); a[x, y + 3, z + 1] = W.lantern()
    (x, z), y = path[-1]
    a[x, y + 1, z - 1] = sb; a[x, y + 2, z - 1] = B('stone_brick_wall'); a[x, y + 3, z - 1] = W.lantern()
    # 上下站雨棚
    for (x, z), y in (path[1], path[-2]):
        for dx in (-2, 2):
            for yy in range(y + 1, y + 4): a[x + dx, yy, z] = B('dark_oak_fence')
        for dx in range(-2, 3):
            for dz in (-1, 0, 1): a[x + dx, y + 4, z + dz] = W.slab('brick_slab')
    T['funi'] = path


def verify_funicular(W, T):
    path = T['funi']
    for i, ((x, z), y) in enumerate(path):
        k = W.get(x, y + 1, z); assert W.names[k] == 'golden_rail', (x, y, z, W.names[k])
        d = W.pal[k][1]['rail_direction']
        if i + 1 < len(path):
            dy = path[i + 1][1] - y
            assert dy in (0, 1) and d == (4 if dy == 1 else 0), (i, dy, d)
        assert W.names[W.get(x, y, z)] not in ('air', 'water')
        assert W.get(x, y + 2, z) == 0 and W.get(x, y + 3, z) == 0, (x, y + 2, z, W.names[W.get(x, y + 2, z)])
    return len(path), path[-1][1] - path[0][1]


# ================================================================ 教堂廣場
def church_plaza(W, T):
    B = W.B; a = W.a; M = _mats(W)
    G = 58
    # 鋪面
    for x in range(104, 143):
        for z in range(90, 113):
            if T['h'][x, z] != G: continue
            a[x, G, z] = B('polished_andesite') if (x % 4 == 0 or z % 4 == 0) else B('stone_bricks') if (x + z) % 3 else B('andesite')
            a[x, G + 1:G + 30, z] = 0 if a[x, G + 1, z] != 0 and False else a[x, G + 1:G + 30, z]
            T['street'][x, z] = True
    # ---- 教堂：x=109..121（寬 13），z=91..108（深 18），正面朝南 ----
    cx0, cx1, cz0, cz1 = 109, 121, 91, 108
    wh = 11
    sg = [B(c + '_stained_glass_pane') for c in ('blue', 'red', 'yellow', 'light_blue', 'orange')]
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            rim = x in (cx0, cx1) or z in (cz0, cz1)
            a[x, G, z] = B('polished_diorite') if (x + z) % 2 else B('polished_andesite')
            for y in range(G + 1, G + wh + 1):
                a[x, y, z] = (M['stone']() if (y <= G + 2 or (x in (cx0, cx1) and z in (cz0, cz1))) else M['white']()) if rim else 0
    # 扶壁與側窗
    for z in range(cz0 + 3, cz1 - 1, 4):
        for x, ox in ((cx0, -1), (cx1, 1)):
            for y in range(G + 1, G + 8): a[x + ox, y, z - 2] = M['stone']()
            a[x + ox, G + 8, z - 2] = W.stairs('stone_brick_stairs', 'e' if ox < 0 else 'w')
            for y in range(G + 4, G + 9): a[x, y, z] = sg[(z + y) % 5]
            a[x, G + 9, z] = W.stairs('stone_brick_stairs', 'n', True) if False else sg[z % 5]
    # 屋頂：陡坡樓梯，屋脊沿 z
    for i in range(7):
        y = G + wh + 1 + i
        for z in range(cz0 - 1, cz1 + 2):
            xl, xr = cx0 - 1 + i, cx1 + 1 - i
            if xl < xr:
                a[xl, y, z] = W.stairs('brick_stairs', 'e'); a[xr, y, z] = W.stairs('brick_stairs', 'w')
            else:
                a[xl, y, z] = W.slab('brick_slab')
        for z in (cz0, cz1):                   # 山牆
            for x in range(cx0 + i, cx1 - i + 1):
                if cx0 - 1 + i < x < cx1 + 1 - i: a[x, y, z] = M['white']()
    # 正面：門、玫瑰窗、十字
    mx = (cx0 + cx1) // 2
    for x in (mx - 1, mx, mx + 1):
        for y in range(G + 1, G + 5): a[x, y, cz1] = 0
    a[mx - 1, G + 4, cz1] = W.stairs('stone_brick_stairs', 'w', True); a[mx + 1, G + 4, cz1] = W.stairs('stone_brick_stairs', 'e', True)
    a[mx, G + 4, cz1] = 0
    W.door(mx, G + 1, cz1, 'dark_oak_door', 's');
    for x in (mx - 1, mx + 1):
        for y in (G + 1, G + 2, G + 3): a[x, y, cz1] = M['stone']()
    a[mx, G + 3, cz1] = M['stone'](); a[mx, G + 4, cz1] = M['stone']()
    for x in (mx - 2, mx + 2):
        for y in range(G + 1, G + 6): a[x, y, cz1 + 1] = B('stone_brick_wall') if y > G + 1 else B('stone_bricks')
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                a[mx + dx, G + 9 + dy, cz1] = sg[(abs(dx) + abs(dy)) % 5] if dx * dx + dy * dy > 0 else B('glowstone')
    a[mx, G + wh + 8, cz1] = M['stone'](); a[mx, G + wh + 9, cz1] = B('stone_brick_wall'); a[mx, G + wh + 10, cz1] = B('stone_brick_wall')
    for x in (mx - 3, mx - 2, mx + 2, mx + 3): a[x, G, cz1 + 1] = B('stone_bricks')
    for x in range(mx - 2, mx + 3): a[x, G + 1, cz1 + 1] = 0
    # 室內：紅毯、長椅、祭壇、吊燈
    for z in range(cz0 + 4, cz1):
        a[mx, G + 1, z] = B('red_carpet')
        if z % 2 == 0 and z < cz1 - 2:
            for x in list(range(cx0 + 2, mx - 1)) + list(range(mx + 2, cx1 - 1)):
                a[x, G + 1, z] = W.stairs('spruce_stairs', 's')
    for x in range(mx - 2, mx + 3):
        a[x, G + 1, cz0 + 2] = B('smooth_quartz'); a[x, G + 1, cz0 + 3] = W.slab('smooth_quartz_slab')
    a[mx, G + 2, cz0 + 2] = B('gold_block'); a[mx - 2, G + 2, cz0 + 2] = B('candle', candles=2, lit=True); a[mx + 2, G + 2, cz0 + 2] = B('candle', candles=2, lit=True)
    a[mx + 3, G + 1, cz0 + 4] = B('lectern', cardinal_direction='south')
    for y in range(G + 5, G + 10): a[mx, y, cz0] = sg[y % 5]; a[mx - 1, y, cz0] = sg[(y + 2) % 5]; a[mx + 1, y, cz0] = sg[(y + 3) % 5]
    for z in range(cz0 + 4, cz1 - 1, 4):
        for y in range(G + wh + 1, G + wh + 5): a[mx, y, z] = B('iron_chain')
        a[mx, G + wh, z] = W.lantern(True); a[mx, G + wh + 1, z] = B('iron_chain')
    # ---- 鐘樓：x=103..107 → 貼教堂西側 x=104..108, z=92..96 ----
    tx0, tz0 = 104, 92
    th = 30
    for y in range(G + 1, G + th + 1):
        for x in range(tx0, tx0 + 5):
            for z in range(tz0, tz0 + 5):
                rim = x in (tx0, tx0 + 4) or z in (tz0, tz0 + 4)
                corner = x in (tx0, tx0 + 4) and z in (tz0, tz0 + 4)
                belfry = G + th - 5 <= y <= G + th - 2
                if not rim: a[x, y, z] = 0
                elif belfry and not corner and (x == tx0 + 2 or z == tz0 + 2 or True) and not (x in (tx0 + 1, tx0 + 3) and False):
                    a[x, y, z] = 0 if (x in (tx0 + 1, tx0 + 2, tx0 + 3) or z in (tz0 + 1, tz0 + 2, tz0 + 3)) else M['stone']()
                else:
                    a[x, y, z] = M['stone']() if (corner or y <= G + 2) else M['white']()
        if (y - G) % 8 == 0 and y < G + th - 6:
            a[tx0 + 2, y - 3, tz0 + 4] = B('glass_pane'); a[tx0 + 2, y - 4, tz0 + 4] = B('glass_pane')
    for x in range(tx0 + 1, tx0 + 4):
        for z in range(tz0 + 1, tz0 + 4):
            a[x, G + th - 6, z] = B('spruce_planks')
    a[tx0 + 2, G + th - 2, tz0 + 2] = B('bell', attachment='hanging'); a[tx0 + 2, G + th - 1, tz0 + 2] = B('dark_oak_fence')
    for x in range(tx0, tx0 + 5):
        for z in range(tz0, tz0 + 5): a[x, G + th - 1, z] = M['stone']() if a[x, G + th - 1, z] == 0 and (x, z) != (tx0 + 2, tz0 + 2) else a[x, G + th - 1, z]
    for i in range(4):
        y = G + th + 1 + i
        for x in range(tx0 - 1 + i, tx0 + 6 - i):
            for z in range(tz0 - 1 + i, tz0 + 6 - i):
                lo, hi, zl, zh = tx0 - 1 + i, tx0 + 5 - i, tz0 - 1 + i, tz0 + 5 - i
                if x == lo: a[x, y, z] = W.stairs('brick_stairs', 'e')
                elif x == hi: a[x, y, z] = W.stairs('brick_stairs', 'w')
                elif z == zl: a[x, y, z] = W.stairs('brick_stairs', 's')
                elif z == zh: a[x, y, z] = W.stairs('brick_stairs', 'n')
                else: a[x, y, z] = B('brick_block')
    a[tx0 + 2, G + th + 4, tz0 + 2] = B('brick_block'); a[tx0 + 2, G + th + 5, tz0 + 2] = B('lightning_rod', facing_direction=1)
    for y in range(G + 1, G + th - 6): a[tx0 + 1, y, tz0 + 1] = W.ladder('s') if False else a[tx0 + 1, y, tz0 + 1]
    for y in range(G + 1, G + th - 5): a[tx0 + 2, y, tz0 + 1] = W.ladder('s')
    a[tx0 + 2, G + th - 6, tz0 + 1] = W.ladder('s')
    W.door(tx0 + 4, G + 1, tz0 + 2, 'spruce_door', 'e'); a[tx0 + 4, G + 3, tz0 + 2] = M['stone']()
    for y in (G + 1, G + 2):                 # 與教堂相通
        a[cx0, y, tz0 + 2] = 0
    # ---- 市政廳：x=133..141, z=95..108，正面朝西 ----
    info = town.house(W, T, 133, 95, 13, 9, 'w', G, 3, W.rng, style=dict(color='cream', roof='brick', rooftype='gable'))
    for z in range(95, 108, 4):               # 拱廊
        for y in range(G + 1, G + 5): a[132, y, z] = B('stone_brick_wall') if y < G + 4 else B('stone_bricks')
    for z in range(95, 108):
        a[132, G + 4, z] = B('stone_bricks') if z % 4 == 3 else W.slab('stone_brick_slab', True); a[131, G + 4, z] = W.slab('stone_brick_slab', True)
    a[132, info['top'] + 1, 101] = B('dark_oak_fence'); a[132, info['top'] + 2, 101] = B('dark_oak_fence')
    a[132, info['top'] + 2, 102] = B('red_wool'); a[132, info['top'] + 2, 103] = B('white_wool')
    # ---- 噴泉 (127,104) ----
    fx, fz = 127, 103
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            r = max(abs(dx), abs(dz))
            if r == 2 and abs(dx) + abs(dz) < 4: a[fx + dx, G + 1, fz + dz] = W.slab('stone_brick_slab') if False else B('stone_bricks')
            elif r < 2: a[fx + dx, G + 1, fz + dz] = B('water'); a[fx + dx, G, fz + dz] = B('prismarine_bricks')
    a[fx, G + 1, fz] = B('stone_bricks'); a[fx, G + 2, fz] = B('stone_brick_wall'); a[fx, G + 3, fz] = B('sea_lantern')
    # 廣場樹與長椅、觀景台欄杆
    for x, z in ((129, 111), (135, 111), (124, 97), (130, 97)):
        a[x, G + 1, z] = W.stairs('spruce_stairs', 's' if z > 100 else 'n')
        a[x + 1, G + 1, z] = W.stairs('spruce_stairs', 's' if z > 100 else 'n')
    T['plaza_trees'] = [(107, 104), (107, 110), (128, 93), (137, 111), (124, 93)]


# ================================================================ 市場
def market(W, T):
    B = W.B; a = W.a
    G = 22
    cols = [('red_wool', 'white_wool'), ('yellow_wool', 'white_wool'), ('blue_wool', 'white_wool'), ('lime_wool', 'white_wool'), ('orange_wool', 'white_wool'), ('light_blue_wool', 'white_wool')]
    goods = ['hay_block', 'melon_block', 'pumpkin', 'barrel', 'composter', 'bee_nest']
    k = 0
    for sx in (88, 94):
        for sz in (185, 191):
            c = cols[k % 6]
            for dx, dz in ((0, 0), (3, 0), (0, 2), (3, 2)):
                for y in (G + 1, G + 2): a[sx + dx, y, sz + dz] = B('spruce_fence')
            for dx in range(-0, 4):
                for dz in range(0, 3):
                    a[sx + dx, G + 3, sz + dz] = B(c[dx % 2])
            a[sx + 1, G + 1, sz] = B(goods[k % 6]) if goods[k % 6] != 'barrel' else B('barrel', facing_direction=1)
            a[sx + 2, G + 1, sz] = W.slab('spruce_slab', True)
            a[sx + 1, G + 1, sz + 2] = B(goods[(k + 2) % 6]) if goods[(k + 2) % 6] != 'barrel' else B('barrel', facing_direction=1)
            a[sx + 2, G + 1, sz + 2] = B('chest', cardinal_direction='south')
            k += 1
    # 水井
    wx, wz = 101, 190
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            a[wx + dx, G + 1, wz + dz] = B('water') if (dx, dz) == (0, 0) else B('cobblestone')
    a[wx, G, wz] = B('water'); a[wx, G - 1, wz] = B('water')
    for dx, dz in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
        a[wx + dx, G + 2, wz + dz] = B('spruce_fence'); a[wx + dx, G + 3, wz + dz] = B('spruce_fence')
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1): a[wx + dx, G + 4, wz + dz] = W.slab('brick_slab')


# ================================================================ 港口
def boat(W, x0, z0, L, sail, hull='spruce_planks', trim='dark_oak_planks', axis='z', hw=None, cargo=False):
    """小船／帆船。x0,z0＝船身中心線起點（船尾），沿 axis 延伸 L 格。船底在海面下 1 格。"""
    B = W.B
    def P(i, j, y, b):                         # i 沿船身，j 橫向
        x, z = (x0 + j, z0 + i) if axis == 'z' else (x0 + i, z0 + j)
        W.put(x, y, z, b)
        if y <= SEA and 0 <= x < SX and 0 <= z < SZ and b != 0 and W.names[b] not in ('air',): W.w2[x, y, z] = False
    hw = hw or (1 if L <= 7 else 2)
    for i in range(L):
        t = i / (L - 1)
        wdt = hw if 0.18 < t < 0.8 else max(hw - 1, 0) if 0.06 < t < 0.94 else 0
        for j in range(-wdt, wdt + 1):
            edge = abs(j) == wdt
            P(i, j, SEA - 1, B(hull)); P(i, j, SEA, B(hull) if edge or wdt == 0 else 0)
            if edge or wdt == 0:
                P(i, j, SEA + 1, B(trim) if L > 7 else W.slab('spruce_slab'))
            else:
                P(i, j, SEA, W.slab('spruce_slab')); P(i, j, SEA + 1, 0)
        if L > 7 and (i in (0, 1) or i >= L - 2):
            for j in range(-wdt, wdt + 1): P(i, j, SEA + 1, B(trim)); P(i, j, SEA + 2, W.slab('dark_oak_slab'))
    if sail:
        masts = [L // 2] if L <= 12 else [L // 3, 2 * L // 3] if L <= 24 else [L // 5 + 1, L // 2, 4 * L // 5 - 1]
        for m in masts:
            H = 6 if L <= 7 else 11 if L <= 24 else (13 if m != L // 2 else 16)
            for y in range(SEA, SEA + H + 1): P(m, 0, y, B('spruce_fence') if L <= 7 else W.log('spruce_log'))
            sc = B(sail[0]); sc2 = B(sail[1])
            for yy in range(3, H):
                wd = (1 if L <= 7 else 3 if L <= 24 else hw + 1) - (1 if yy > H - 3 and L > 7 else 0)
                for j in range(-wd, wd + 1):
                    if j != 0 or True: P(m + 1, j, SEA + yy, sc if (yy // 2) % 2 == 0 else sc2)
            P(m, 0, SEA + H + 1, B('red_wool'))
        if L > 7:
            P(L - 1, 0, SEA + 2, B('spruce_fence')); P(L, 0, SEA + 2, B('spruce_fence'))
            P(L // 2 + 2, 1, SEA + 1, B('barrel', facing_direction=1)); P(2, 0, SEA + 2, B('lantern'))
    else:
        P(L // 2, 0, SEA + 1, B('barrel', facing_direction=1))
    if cargo:                                  # 甲板上的黃金貨物
        mset = set(masts) | {m + 1 for m in masts}
        k = 0
        for i in range(4, L - 4):
            if i in mset: continue
            for j in (-(hw - 1), hw - 1):
                k += 1
                if k % 3 == 0: continue
                P(i, j, SEA + 1, B('gold_block') if k % 4 == 1 else B('raw_gold_block') if k % 4 == 2 else B('chest', cardinal_direction='south'))
                if k % 5 == 1: P(i, j, SEA + 2, B('raw_gold_block'))


def harbor(W, T):
    B = W.B; a = W.a; M = _mats(W)
    h = T['h']
    Q = 22
    water = B('water')
    # 石碼頭：站前 x=96..152, z=204..212
    for x in range(96, 153):
        for z in range(204, 214):
            for y in range(min(int(h[x, z]), Q - 6), Q): a[x, y, z] = M['stone']()
            a[x, Q, z] = B('polished_andesite') if (z in (204, 213) or x in (96, 152)) else B('stone_bricks') if (x + z) % 3 else B('andesite')
            a[x, Q + 1:Q + 6, z] = np.where(a[x, Q + 1:Q + 6, z] == water, 0, a[x, Q + 1:Q + 6, z])
            h[x, z] = Q; T['street'][x, z] = True
    # 商港突堤：x=146..150, z=214..244
    for x in range(146, 151):
        for z in range(214, 245):
            for y in range(int(h[x, z]), Q): a[x, y, z] = M['stone']()
            a[x, Q, z] = B('polished_andesite') if x in (146, 150) or z == 244 else B('stone_bricks')
            h[x, z] = Q
        if True:
            pass
    for z in range(216, 244, 6):
        a[146, Q + 1, z] = B('dark_oak_log'); a[150, Q + 1, z] = B('dark_oak_log')        # 繫船柱
        a[148, Q + 1, z + 3] = B('stone_brick_wall'); a[148, Q + 2, z + 3] = B('stone_brick_wall'); a[148, Q + 3, z + 3] = W.lantern()
    # 起重機
    cx, cz = 148, 241
    for y in range(Q + 1, Q + 9): a[cx, y, cz] = W.log('spruce_log')
    for i in range(-2, 6): a[cx + i, Q + 8, cz] = W.log('stripped_spruce_log', 'x')
    a[cx - 1, Q + 7, cz] = B('spruce_fence'); a[cx + 1, Q + 7, cz] = B('spruce_fence')
    for y in range(Q + 4, Q + 8): a[cx + 5, y, cz] = B('iron_chain')
    a[cx + 5, Q + 3, cz] = B('barrel', facing_direction=1)
    for (x, z) in ((147, 218), (149, 226), (147, 232), (149, 236)):
        a[x, Q + 1, z] = B('barrel', facing_direction=1) if (x + z) % 2 else B('hay_block')
    a[147, Q + 2, 218] = B('barrel', facing_direction=1)
    # 漁港木棧橋：x=102..104, z=214..238 ＋ T 形
    plank = B('spruce_planks'); slab = W.slab('spruce_slab', True)
    def deck(x, z):
        a[x, Q, z] = plank if (x + z) % 4 else B('stripped_spruce_log', pillar_axis='x'); a[x, Q + 1:Q + 4, z] = 0
        a[x, SEA + 1, z] = 0 if a[x, SEA + 1, z] == water else a[x, SEA + 1, z]
    for z in range(214, 239):
        for x in (102, 103, 104): deck(x, z)
    for x in range(96, 111):
        for z in (237, 238, 239): deck(x, z)
    for (x, z) in [(102, zz) for zz in range(216, 238, 5)] + [(104, zz) for zz in range(216, 238, 5)] + [(96, 239), (110, 239), (96, 237), (110, 237)]:
        for y in range(int(h[x, z]), Q): a[x, y, z] = W.log('spruce_log'); W.w2[x, y, z] = y <= SEA
        a[x, Q + 1, z] = B('spruce_fence');
        if (x + z) % 3 == 0: a[x, Q + 2, z] = W.lantern()
    a[103, Q + 1, 239] = B('barrel', facing_direction=1); a[98, Q + 1, 239] = B('composter'); a[108, Q + 1, 238] = B('chest', cardinal_direction='north')
    # 船
    boat(W, 155, 218, 19, ('white_wool', 'red_wool'), axis='z')
    boat(W, 141, 222, 15, ('white_wool', 'blue_wool'), axis='z')
    for (x, z, c, ax) in ((99, 220, 'red', 'z'), (107, 224, 'blue', 'z'), (99, 229, 'yellow', 'z'), (114, 243, 'green', 'x'), (88, 243, 'white', 'x'), (120, 217, 'orange', 'z'), (128, 219, 'light_blue', 'z')):
        boat(W, x, z, 6, None if c in ('green', 'white') else ('white_wool', 'white_wool'), hull=c + '_concrete' if c not in ('white',) else 'white_concrete', axis=ax)
    # 防波堤：從東岸往西南的亂石堤
    rs = np.random.RandomState(9)
    pts = []
    for t in np.linspace(0, 1, 60):
        pts.append((234 - 14 * t * t, 206 + 46 * t))
    for i, (px, pz) in enumerate(pts):
        r = 3.6 + 0.8 * math.sin(i / 3.0)
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                x, z = int(px + dx), int(pz + dz)
                if not (0 <= x < SX and 0 <= z < SZ): continue
                dd = math.hypot(dx, dz)
                if dd <= r + rs.rand() * 0.8:
                    top = Q - (1 if dd > r - 1.2 else 0) - (1 if rs.rand() < 0.2 else 0)
                    for y in range(min(int(h[x, z]), top), top + 1):
                        a[x, y, z] = [B('cobblestone'), B('andesite'), B('stone'), B('mossy_cobblestone'), B('tuff')][rs.randint(5)]
                    if top < Q: pass
                    h[x, z] = max(h[x, z], top)
    ex, ez = int(pts[-1][0]), int(pts[-1][1])
    for y in range(Q, Q + 5): a[ex, y, ez] = B('stone_bricks') if y < Q + 3 else B('stone_brick_wall')
    a[ex, Q + 5, ez] = B('sea_lantern'); a[ex, Q + 6, ez] = W.slab('red_sandstone_slab')
    # 沙灘陽傘與小舟
    k = 0
    for x in list(range(48, 92, 9)) + list(range(160, 215, 9)):
        z = 203 + (k % 2) * 2
        if T['sea'][x, z] or h[x, z] > 22 or a[x, int(h[x, z]) + 1, z] != 0 or T['street'][x, z] or T['reserved'][x, z]: k += 1; continue
        y = int(h[x, z])
        a[x, y + 1, z] = B('birch_fence'); a[x, y + 2, z] = B('birch_fence')
        c = ['red', 'yellow', 'light_blue', 'orange', 'lime', 'pink'][k % 6]
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1): a[x + dx, y + 3, z + dz] = B((c if (dx + dz) % 2 == 0 else 'white') + '_carpet') if (dx, dz) != (0, 0) else B(c + '_wool')
        for dx in (-1, 1):
            for dz in (-1, 1): a[x + dx, y + 3, z + dz] = 0
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)): a[x + dx, y + 3, z + dz] = B(c + '_wool') if False else W.slab('birch_slab', True) if False else B((c if (dx + dz) % 2 else 'white') + '_wool')
        a[x + 1, y + 1, z + 1] = B(c + '_carpet')
        k += 1


# ================================================================ 燈塔
def lighthouse(W, T):
    B = W.B; a = W.a; h = T['h']
    cx, cz = 245, 190
    G = int(h[cx - 3:cx + 4, cz - 3:cz + 4].max())
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            x, z = cx + dx, cz + dz
            if not (0 <= x < SX and 0 <= z < SZ): continue
            if dx * dx + dz * dz <= 27 and not T['sea'][x, z]:
                for y in range(int(h[x, z]), G + 1): a[x, y, z] = B('stone_bricks') if y == G else B('cobblestone')
                h[x, z] = G
    Ht = 24
    for i in range(Ht):
        y = G + 1 + i
        r = 3.6 if i < 6 else 3.1 if i < 16 else 2.6
        col = B('white_concrete') if (i // 4) % 2 == 0 else B('red_concrete')
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx, dz)
                if d <= r: a[cx + dx, y, cz + dz] = col if d > r - 1.2 else 0
        a[cx, y, cz] = W.log('spruce_log')                        # 中柱
        a[cx, y, cz + 1] = W.ladder('s')
        if i % 6 == 3: a[cx + int(r), y, cz] = B('glass_pane'); a[cx - int(r), y, cz] = B('glass_pane')
    W.door(cx, G + 1, cz - 3, 'spruce_door', 'n'); a[cx, G + 1, cz - 2] = 0; a[cx, G + 2, cz - 2] = 0
    y = G + 1 + Ht                                               # 迴廊
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            d = math.hypot(dx, dz)
            if d <= 4.3: a[cx + dx, y, cz + dz] = B('smooth_stone') if d <= 2.6 else W.slab('smooth_stone_slab', True)
            if 3.4 < d <= 4.3: a[cx + dx, y + 1, cz + dz] = B('iron_bars')
    a[cx, y, cz + 1] = W.ladder('s'); a[cx, y, cz] = W.log('spruce_log')
    for i in range(1, 5):                                        # 燈室
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                d = math.hypot(dx, dz)
                if 1.5 < d <= 2.3: a[cx + dx, y + i, cz + dz] = B('glass') if i < 4 else B('red_concrete')
                elif d <= 1.5 and i == 4: a[cx + dx, y + i, cz + dz] = B('red_concrete')
    a[cx, y + 1, cz] = B('sea_lantern'); a[cx, y + 2, cz] = B('sea_lantern'); a[cx, y + 3, cz] = B('glowstone')
    a[cx, y + 1, cz + 1] = 0
    a[cx, y + 5, cz] = B('red_concrete'); a[cx, y + 6, cz] = B('lightning_rod', facing_direction=1)
    # 守燈人小屋
    for x in range(236, 242):
        for z in range(184, 190):
            for yy in range(int(h[x, z]), G + 1): a[x, yy, z] = B('cobblestone')
            h[x, z] = G
    town.house(W, T, 236, 184, 6, 5, 'e', G, 1, W.rng, style=dict(color='white', roof='brick', rooftype='gable'))


# ================================================================ 山頂
def summit(W, T):
    B = W.B; a = W.a; h = T['h']; M = _mats(W)
    sub = h[100:145, 55:95]
    ix = np.unravel_index(np.argmax(sub), sub.shape); px, pz = 100 + ix[0], 55 + ix[1]
    G = int(h[px, pz]) - 2
    for dx in range(-5, 6):                                      # 山頂平台
        for dz in range(-5, 6):
            x, z = px + dx, pz + dz
            if dx * dx + dz * dz <= 30:
                a[x, G + 1:G + 8, z] = 0
                for y in range(min(int(h[x, z]), G) - 1, G + 1): a[x, y, z] = M['stone']()
                a[x, G, z] = B('stone_bricks') if (dx + dz) % 2 else B('cobblestone'); h[x, z] = G
    # 瞭望鐘樓 5x5
    for i in range(16):
        y = G + 1 + i
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                rim = abs(dx) == 2 or abs(dz) == 2
                if rim:
                    open_ = i >= 12 and i < 15 and (abs(dx) < 2 or abs(dz) < 2)
                    a[px + dx, y, pz + dz] = 0 if open_ else M['stone']()
                else:
                    a[px + dx, y, pz + dz] = B('spruce_planks') if i == 11 else 0
        if i in (4, 8): a[px + 2, y, pz] = B('glass_pane'); a[px, y, pz + 2] = B('glass_pane')
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if max(abs(dx), abs(dz)) == 3:
                a[px + dx, G + 16, pz + dz] = W.slab('stone_brick_slab', True)
                if (dx + dz) % 2 == 0: a[px + dx, G + 17, pz + dz] = B('stone_brick_wall')
            else: a[px + dx, G + 16, pz + dz] = B('stone_bricks')
    a[px, G + 17, pz] = B('netherrack'); a[px, G + 18, pz] = B('fire') if False else B('campfire', extinguished=False)
    a[px, G + 14, pz] = B('bell', attachment='hanging'); a[px, G + 15, pz] = B('dark_oak_fence')
    for y in range(G + 1, G + 12): a[px - 1, y, pz - 1] = W.ladder('s')
    a[px - 1, G + 12, pz - 1] = 0
    for y in (G + 1, G + 2): a[px, y, pz + 2] = 0
    # 城堡遺跡：殘牆
    rs = np.random.RandomState(4)
    for (x0, z0, x1, z1) in ((px - 12, pz + 5, px - 5, pz + 5), (px - 12, pz - 2, px - 12, pz + 5), (px + 6, pz + 4, px + 12, pz + 4), (px + 12, pz - 3, px + 12, pz + 4)):
        n = max(abs(x1 - x0), abs(z1 - z0)) + 1
        for i in range(n):
            x = x0 + (x1 - x0) * i // max(n - 1, 1); z = z0 + (z1 - z0) * i // max(n - 1, 1)
            g = int(h[x, z]); top = g + int(2 + 4 * abs(math.sin(i * 1.3)) + rs.randint(2))
            for y in range(g + 1, top + 1): a[x, y, z] = M['stone']() if rs.rand() < 0.85 else B('mossy_cobblestone')
            if i % 3 == 1 and top - g > 4: a[x, g + 3, z] = 0; a[x, g + 4, z] = 0
    T['summit'] = (px, G, pz)


# ================================================================ 後山地下車站
def underground_station(W, T):
    """北段地下鐵路的車站：A 軌 z=30、B 軌 z=28，軌面 y=34。兩側月台＋挑高大廳，樓梯往南通到後山山腰出口。"""
    B = W.B; a = W.a; M = _mats(W); h = T['h']
    P = 34; x0, x1 = 82, 110
    tile = W.mix((B('calcite'), 70), (B('smooth_quartz'), 30))
    band = B('light_blue_terracotta'); pand = B('polished_andesite')
    for x in range(x0 - 1, x1 + 2):
        for z in range(22, 37):
            shell = x in (x0 - 1, x1 + 1) or z in (22, 36)
            track = 27 <= z <= 31
            if shell:
                if track and x in (x0 - 1, x1 + 1): continue      # 隧道口
                for y in range(P - 1, P + 8): a[x, y, z] = band if y == P + 3 else tile()
                continue
            a[x, P + 7, z] = M['stone']() if (x + z) % 4 else B('glowstone')
            for y in range(P + 1, P + 7): a[x, y, z] = 0
            if track:
                if z in (27, 31): a[x, P, z] = pand; a[x, P - 1, z] = M['stone']()      # 月台邊緣
                continue
            a[x, P - 1, z] = M['stone'](); a[x, P, z] = pand if (x + z) % 2 else B('polished_diorite')
    for x in range(x0 + 2, x1, 6):                # 柱、吊燈、長椅
        for z in (25, 33):
            for y in range(P + 1, P + 7): a[x, y, z] = B('polished_andesite') if y in (P + 1, P + 6) else B('stone_brick_wall')
        a[x + 3, P + 6, 24] = W.lantern(True); a[x + 3, P + 6, 34] = W.lantern(True)
        a[x + 2, P + 1, 23] = W.stairs('spruce_stairs', 'n'); a[x + 3, P + 1, 23] = W.stairs('spruce_stairs', 'n')
        a[x + 2, P + 1, 35] = W.stairs('spruce_stairs', 's') if x + 2 not in (95, 96, 97) else 0
    # 兩月台之間直接跨軌通行（道床比月台低一階）
    # 出口樓梯：x=95..97，從南月台 (z=36) 往南 1:1 上升到地表
    exit_ = None
    for k in range(0, 40):
        z = 36 + k; y = P + 1 + k
        g = min(int(h[x, z]) for x in (95, 96, 97))
        if y > g + 1:
            exit_ = (96, y - 1, z); break
        for x in (94, 98):
            for yy in range(y - 1, y + 5):
                if a[x, yy, z] != 0: a[x, yy, z] = tile() if yy != y + 2 else band
        for x in (95, 96, 97):
            a[x, y - 1, z] = M['stone'](); a[x, y, z] = W.stairs('stone_brick_stairs', 's')
            for yy in range(y + 1, y + 5): a[x, yy, z] = 0
            if a[x, y + 5, z] != 0: a[x, y + 5, z] = M['stone']()
            T['reserved'][x, z] = True
        if k % 4 == 2: a[96, y + 4, z] = W.lantern(True)
        T['reserved'][94, z] = True; T['reserved'][98, z] = True
    for x in (95, 96, 97):                        # 月台側開口
        for yy in range(P + 1, P + 5): a[x, yy, 36] = 0
        a[x, P, 36] = pand
    a[95, P + 1, 36] = 0
    # 出口涼亭
    ex, ey, ez = exit_
    for x in range(93, 100):
        for z in range(ez, ez + 6):
            a[x, ey, z] = B('stone_bricks') if (x + z) % 3 else B('andesite')
            for yy in range(int(h[x, z]), ey): a[x, yy, z] = M['stone']()
            for yy in range(ey + 1, ey + 6): a[x, yy, z] = 0
            h[x, z] = ey; T['street'][x, z] = True; T['reserved'][x, z] = True
    for x in (93, 99):
        for z in (ez, ez + 5):
            for yy in range(ey + 1, ey + 4): a[x, yy, z] = B('spruce_fence')
    for x in range(92, 101):
        for z in range(ez - 1, ez + 7): a[x, ey + 4, z] = W.slab('brick_slab') if (x in (92, 100) or z in (ez - 1, ez + 6)) else W.slab('brick_slab', True)
    a[96, ey + 3, ez + 3] = W.lantern(True)
    a[93, ey + 1, ez + 2] = W.stairs('spruce_stairs', 'w'); a[93, ey + 1, ez + 3] = W.stairs('spruce_stairs', 'w')
    T['ug_exit'] = (96, ey, ez + 5)
    T['ug_station'] = (96, P, 33)


# ================================================================ 機務段與靜態列車
def loco(W, x, y, z0):
    """沿 z 軸的蒸汽機車＋兩節車廂（靜態模型）。x＝中心，y＝軌面。"""
    B = W.B
    bk, gy, rd, gold = B('black_concrete'), B('gray_concrete'), B('red_concrete'), B('gold_block')
    def P(dx, dy, dz, b): W.put(x + dx, y + dy, z0 + dz, b)
    for dz in range(0, 9):
        for dx in (-1, 0, 1):
            P(dx, 0, dz, B('polished_blackstone') if dz % 3 != 1 or dx == 0 else B('coal_block'))
    for dz in range(0, 6):                    # 鍋爐
        for dx in (-1, 0, 1):
            P(dx, 1, dz, bk);
        P(0, 2, dz, bk); P(-1, 2, dz, W.stairs('polished_blackstone_stairs', 'e')); P(1, 2, dz, W.stairs('polished_blackstone_stairs', 'w'))
    P(0, 1, 0, rd); P(0, 2, 0, B('redstone_lamp')); P(0, 3, 1, B('polished_blackstone_wall')); P(0, 4, 1, B('polished_blackstone_wall')); P(0, 5, 1, B('campfire', extinguished=False))
    P(0, 3, 3, gold); P(0, 0, -1, W.stairs('polished_blackstone_stairs', 's'))
    for dz in range(6, 9):                    # 駕駛室
        for dx in (-1, 0, 1):
            for dy in (1, 2, 3):
                P(dx, dy, dz, rd if (abs(dx) == 1 or dz == 8) and dy < 3 else (B('glass_pane') if abs(dx) == 1 and dy == 3 and dz == 7 else rd if dy == 3 and abs(dx) == 1 else 0))
            P(dx, 4, dz, W.slab('polished_blackstone_slab'))
        P(0, 1, dz, 0); P(0, 2, dz, 0)
    for c, zc in ((B('spruce_planks'), 10), (B('mangrove_planks'), 18)):       # 車廂
        for dz in range(zc, zc + 7):
            for dx in (-1, 0, 1):
                P(dx, 0, dz, B('polished_blackstone') if dz in (zc + 1, zc + 5) else W.slab('polished_blackstone_slab', True))
                for dy in (1, 2, 3):
                    wall = abs(dx) == 1 or dz in (zc, zc + 6)
                    P(dx, dy, dz, (B('glass_pane') if dy == 2 and abs(dx) == 1 and (dz - zc) % 2 == 1 else c) if wall else 0)
                P(dx, 4, dz, W.slab('dark_oak_slab'))
        P(0, 1, zc + 7, B('iron_chain', pillar_axis='z')) if zc == 10 else None
    P(0, 1, 9, B('iron_chain', pillar_axis='z'))


def depot(W, T):
    B = W.B; a = W.a; M = _mats(W)
    G = 28
    x0, x1, z0, z1 = 211, 219, 106, 148
    T['reserved'][x0 - 1:x1 + 2, z0 - 1:z1 + 2] = True
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            a[x, G, z] = B('gravel') if (x + z * 2) % 4 else B('cobblestone'); a[x, G - 1, z] = B('stone'); a[x, G + 1:G + 12, z] = 0
    for tx in (213, 217):                     # 兩條側線
        for z in range(z0 + 1, z1):
            a[tx, G + 1, z] = B('rail', rail_direction=0)
            a[tx, G, z] = B('spruce_planks') if z % 2 else B('gravel')
        a[tx, G + 1, z0] = B('stone_bricks'); a[tx, G + 1, z1] = B('stone_bricks')
    # 車庫 z=150..168
    for z in range(128, 147):
        for x in (x0, x1):
            for y in range(G + 1, G + 7): a[x, y, z] = B('brick_block') if (y + z) % 5 else B('granite')
            if z % 4 == 0: a[x, G + 3, z] = B('glass_pane'); a[x, G + 4, z] = B('glass_pane')
        for i in range(5):
            y = G + 7 + i
            xl, xr = x0 - 1 + i, x1 + 1 - i
            if xl < xr: a[xl, y, z] = W.stairs('deepslate_tile_stairs', 'e'); a[xr, y, z] = W.stairs('deepslate_tile_stairs', 'w')
            else: a[xl, y, z] = W.slab('deepslate_tile_slab')
            if z in (128, 146):
                for x in range(xl + 1, xr): a[x, y, z] = B('brick_block')
        if z % 5 == 0:
            a[215, G + 6, z] = W.lantern(True)
            for yy in range(G + 7, G + 11): a[215, yy, z] = B('iron_chain')
    for x in range(x0, x1 + 1):               # 山牆面（兩端開大門）
        for y in range(G + 1, G + 7):
            op = x in (212, 213, 214, 216, 217, 218) and y <= G + 5
            for z in (128, 146):
                a[x, y, z] = 0 if op else B('brick_block')
    for tx in (213, 217):
        for dx in (-1, 0, 1):
            for z in (128, 146): a[tx + dx, G + 1, z] = 0
        a[tx, G + 1, 128] = B('rail', rail_direction=0); a[tx, G + 1, 146] = B('rail', rail_direction=0)
    loco(W, 213, G + 1, 108)
    # 水塔與煤台
    for y in range(G + 1, G + 6):
        for dx, dz in ((0, 0), (2, 0), (0, 2), (2, 2)): a[222 - 1 + dx, y, 141 + dz] = B('spruce_fence') if False else a[222 - 1 + dx, y, 141 + dz]
    for z in range(138, 144):
        a[217, G + 2, z] = B('coal_block') if z % 2 else B('polished_blackstone')
    for z in range(111, 117): a[218, G + 1, z] = B('coal_block'); a[219, G + 1, z] = B('coal_block') if z % 2 else B('spruce_planks'); a[218, G + 2, z] = B('coal_block') if z % 3 else 0
    for z in (110, 117): a[218, G + 1, z] = B('spruce_planks'); a[219, G + 1, z] = B('spruce_planks')


# ================================================================ 風車
def windmill(W, T):
    B = W.B; a = W.a; h = T['h']
    best = None
    for x in range(44, 100, 2):
        for z in range(56, 130, 2):
            if T['reserved'][x - 4:x + 5, z - 4:z + 5].any() or T['cor2'][x - 5:x + 6, z - 5:z + 6].any(): continue
            c = int(T['farm'][x - 4:x + 5, z - 4:z + 5].sum())
            if c >= 70 and (best is None or (c, h[x, z]) > best[3]): best = (int(h[x, z]), x, z, (c, h[x, z]))
    if not best: return None
    G, cx, cz = best[:3]
    for x in range(cx - 4, cx + 5):               # 整平基座
        for z in range(cz - 4, cz + 5):
            for yy in range(min(int(h[x, z]), G) - 1, G): a[x, yy, z] = B('cobblestone')
            a[x, G, z] = B('grass_block') if max(abs(x - cx), abs(z - cz)) == 4 else B('cobblestone')
            a[x, G + 1:G + 20, z] = 0; h[x, z] = G
    best = (G, cx, cz)
    G, cx, cz = best
    T['reserved'][cx - 4:cx + 5, cz - 4:cz + 5] = True
    stone = W.mix((B('cobblestone'), 50), (B('stone_bricks'), 30), (B('mossy_cobblestone'), 20))
    for i in range(11):
        r = 3.3 - i * 0.09
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx, dz)
                if d <= r: a[cx + dx, G + 1 + i, cz + dz] = (stone() if i < 4 else B('white_concrete') if (dx + dz + i) % 9 else B('calcite')) if d > r - 1.25 else (B('spruce_planks') if i == 5 else 0)
    for i in range(4):
        r = 3.6 - i
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                if math.hypot(dx, dz) <= r: a[cx + dx, G + 12 + i, cz + dz] = B('spruce_planks') if i < 3 else W.slab('spruce_slab')
    W.door(cx, G + 1, cz + 3, 'spruce_door', 's'); a[cx, G + 1, cz + 2] = 0; a[cx, G + 2, cz + 2] = 0
    for y in range(G + 1, G + 6): a[cx - 1, y, cz - 1] = W.ladder('s')
    a[cx + 1, G + 1, cz] = B('hay_block'); a[cx + 1, G + 1, cz - 1] = B('barrel', facing_direction=1); a[cx, G + 4, cz] = W.lantern(True)
    a[cx + 2, G + 8, cz] = B('glass_pane'); a[cx - 2, G + 8, cz] = B('glass_pane')
    # 風帆：朝西（面向溺谷），在 x=cx-4 的平面
    hx, hy = cx - 4, G + 10
    a[cx - 3, hy, cz] = W.log('spruce_log', 'x'); a[hx, hy, cz] = W.log('stripped_spruce_log', 'x')
    for k in range(1, 7):
        for (dy, dz) in ((k, 0), (-k, 0), (0, k), (0, -k)):
            a[hx, hy + dy, cz + dz] = B('spruce_fence')
            if k >= 2:
                sy, sz = (0, 1) if dy else (1, 0)
                s2 = 1 if (dy > 0 or dz < 0) else -1
                a[hx, hy + dy + sy * s2 * (1 if not dy else 0), cz + dz + sz * s2 * (1 if dy else 0)] = B('white_wool')
    T['windmill'] = (cx, G, cz)
    return best


# ================================================================ 金市（站前廣場東側）
def gold_market(W, T):
    B = W.B; a = W.a
    G = 22
    x0, x1, z0, z1 = 147, 157, 182, 194
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if T['cor'][x, z]: continue
            a[x, G, z] = B('polished_andesite') if (x + z) % 2 else B('smooth_sandstone'); a[x, G + 1:G + 6, z] = 0
            T['street'][x, z] = True
    goods = [('gold_block', 'raw_gold_block'), ('raw_gold_block', 'gold_ore'), ('gold_block', 'bell'), ('raw_gold_block', 'gold_block')]
    k = 0
    for sx in (148, 153):
        for sz in (183, 189):
            for dx, dz in ((0, 0), (3, 0), (0, 2), (3, 2)):
                for y in (G + 1, G + 2): a[sx + dx, y, sz + dz] = B('birch_fence')
            for dx in range(4):
                for dz in range(3): a[sx + dx, G + 3, sz + dz] = B('yellow_wool') if (dx + dz) % 2 == 0 else B('white_wool')
            g1, g2 = goods[k]
            a[sx + 1, G + 1, sz] = B(g1); a[sx + 2, G + 1, sz] = W.slab('smooth_quartz_slab', True)
            a[sx + 2, G + 2, sz] = B(g2) if g2 != 'bell' else B('bell', attachment='standing')
            a[sx + 1, G + 1, sz + 2] = B('chest', cardinal_direction='south'); a[sx + 2, G + 1, sz + 2] = B(g2 if g2 != 'bell' else 'gold_block')
            a[sx + 1, G + 2, sz + 1] = W.lantern(True)
            k += 1
    # 中央：金秤台
    cx, cz = 152, 187
    a[cx, G + 1, cz] = B('chiseled_stone_bricks'); a[cx, G + 2, cz] = B('gold_block'); a[cx, G + 3, cz] = B('stone_brick_wall'); a[cx, G + 4, cz] = W.lantern()
    T['gold_market'] = (152, G + 1, 188)


# ================================================================ 黃金碼頭（出口港）
def gold_wharf(W, T):
    """港口東側加大：黃金專用鐵路的終點。石岸壁、突堤、保稅金庫倉、兩座起重機、裝金的大商船。先整地（鐵路之後才鋪）。"""
    B = W.B; a = W.a; M = _mats(W); h = T['h']
    Q = 22; water = B('water')
    def slab_area(x0, x1, z0, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(min(int(h[x, z]), Q - 8), Q): a[x, y, z] = M['stone']()
                edge = x in (x0, x1) or z in (z0, z1)
                a[x, Q, z] = B('polished_andesite') if edge else B('stone_bricks') if (x + z) % 3 else B('andesite')
                col = a[x, Q + 1:Q + 8, z]; col[col == water] = 0
                h[x, z] = Q; T['street'][x, z] = True; T['reserved'][x, z] = True; T['sea'][x, z] = False
    slab_area(184, 218, 203, 214)                  # 岸壁
    slab_area(198, 206, 215, 244)                  # 突堤（鐵路走中央 x=202）
    T['gold_wharf'] = (205, Q + 1, 212)


def gold_wharf_fit(W, T):
    """鐵路鋪好後的碼頭設施。"""
    B = W.B; a = W.a; M = _mats(W)
    Q = 22
    # 保稅金庫倉 x=185..196, z=204..212
    for x in range(185, 197):
        for z in range(204, 213):
            rim = x in (185, 196) or z in (204, 212)
            for y in range(Q + 1, Q + 7):
                a[x, y, z] = (B('brick_block') if (x + y + z) % 6 else B('granite')) if rim else 0
            a[x, Q, z] = B('polished_andesite')
        for i in range(6):
            y = Q + 7 + i; zl, zr = 203 + i, 213 - i
            if zl < zr: a[x, y, zl] = W.stairs('deepslate_tile_stairs', 's'); a[x, y, zr] = W.stairs('deepslate_tile_stairs', 'n')
            else: a[x, y, zl] = W.slab('deepslate_tile_slab')
            if x in (185, 196):
                for z in range(zl + 1, zr): a[x, y, z] = B('brick_block')
    for z in (207, 208, 209):                      # 面向鐵路的大門
        for y in range(Q + 1, Q + 5): a[196, y, z] = 0
    a[196, Q + 5, 208] = B('gold_block')
    for x in range(187, 195, 3):
        for y in (Q + 3, Q + 4): a[x, y, 204] = B('iron_bars'); a[x, y, 212] = B('iron_bars')
    for x in range(186, 195):                      # 庫內金磚垛
        for z in (205, 206, 210, 211):
            if (x + z) % 3 == 0: continue
            a[x, Q + 1, z] = B('gold_block') if (x + z) % 2 else B('raw_gold_block')
            if (x * 3 + z) % 4 == 0: a[x, Q + 2, z] = B('gold_block')
    for x in (188, 192): a[x, Q + 5, 208] = W.lantern(True); a[x, Q + 6, 208] = B('iron_chain')
    a[195, Q + 1, 205] = B('chest', cardinal_direction='south'); a[195, Q + 1, 211] = B('barrel', facing_direction=1); a[194, Q + 1, 211] = B('lectern', cardinal_direction='north')
    # 兩座門型起重機，橫跨鐵路
    for cz in (222, 234):
        for x in (199, 205):
            for y in range(Q + 1, Q + 9): a[x, y, cz] = W.log('spruce_log')
        for x in range(197, 212): a[x, Q + 9, cz] = W.log('stripped_spruce_log', 'x')
        for y in range(Q + 5, Q + 9): a[210, y, cz] = B('iron_chain')
        a[210, Q + 4, cz] = B('gold_block'); a[210, Q + 3, cz] = B('gold_block') if cz == 222 else B('chest', cardinal_direction='south')
        a[199, Q + 8, cz + 1] = W.lantern(True) if False else 0
    # 突堤上的金箱堆、繫船柱、燈柱
    for z in range(217, 243, 4):
        a[198, Q + 1, z] = B('dark_oak_log'); a[206, Q + 1, z] = B('dark_oak_log')
        if z % 8 == 1:
            a[200, Q + 1, z + 1] = B('stone_brick_wall'); a[200, Q + 2, z + 1] = B('stone_brick_wall'); a[200, Q + 3, z + 1] = W.lantern()
    for (x, z, b) in ((204, 218, 'gold_block'), (204, 219, 'raw_gold_block'), (205, 219, 'chest'), (204, 227, 'raw_gold_block'), (205, 227, 'gold_block'), (204, 228, 'gold_block'),
                      (200, 230, 'chest'), (200, 238, 'raw_gold_block'), (204, 239, 'gold_block'), (204, 240, 'barrel'), (200, 239, 'gold_block')):
        if a[x, Q + 1, z] != 0: continue
        a[x, Q + 1, z] = B('chest', cardinal_direction='west') if b == 'chest' else B('barrel', facing_direction=1) if b == 'barrel' else B(b)
    a[204, Q + 2, 218] = B('gold_block'); a[204, Q + 2, 227] = B('raw_gold_block')
    # 岸壁上的秤量所與柵門
    for x in range(208, 217):
        a[x, Q + 1, 204] = B('iron_bars')
    for (x, z) in ((208, 208), (214, 210), (209, 212)):
        a[x, Q + 1, z] = B('raw_gold_block'); 
    a[214, Q + 2, 210] = B('gold_block')
    for (x, z) in ((185, 214), (218, 203), (218, 214), (207, 214)):
        a[x, Q + 1, z] = B('stone_brick_wall'); a[x, Q + 2, z] = B('stone_brick_wall'); a[x, Q + 3, z] = W.lantern()
    # 商船：大型三桅運金船靠突堤東側，另一艘雙桅船靠西側
    boat(W, 212, 216, 29, ('white_wool', 'yellow_wool'), hull='dark_oak_planks', trim='spruce_planks', axis='z', hw=4, cargo=True)
    boat(W, 193, 220, 19, ('white_wool', 'orange_wool'), axis='z', cargo=True)
    for z in (224, 232):                           # 跳板
        for x in (207,): a[x, Q, z] = W.slab('spruce_slab', True)
