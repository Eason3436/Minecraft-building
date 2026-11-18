"""地景：地基、道路、哈利法塔公園（Y 形水道）、哈利法湖與杜拜噴泉、步行橋、杜拜購物中心、巴哈爾市集、棕櫚、路燈。"""
import math
import numpy as np
from core import *
import tower as T

LAKE = (150.0, 168.0, 92.0, 40.0)
MALL = (164, 252, 20, 118)
SOUK = (24, 112, 216, 250)
BRIDGE = (70, 73, 140, 196)
LOW_H = 40

xs = np.arange(SX) + 0.5
GX, GZ = np.meshgrid(xs, xs, indexing='ij')


def lake_e():
    cx, cz, rx, rz = LAKE
    return ((GX - cx) / rx) ** 2 + ((GZ - cz) / rz) ** 2


def build_land(W, info):
    B = W.B
    rng = W.rng
    e = lake_e()
    lake = e <= 1.0
    W.a[:, 0:3, :] = B('sandstone')
    # ---- 地面分區 ----
    surf = np.full((SX, SZ), B('smooth_sandstone'), np.uint16)
    grid = ((np.arange(SX)[:, None] % 8 == 0) | (np.arange(SZ)[None, :] % 8 == 0))
    surf[grid] = B('cut_sandstone')
    # 公園
    dT = np.hypot(GX - T.CC, GZ - T.CC)
    park = (dT <= 80) & ~lake & (e > 1.12)
    surf[park] = B('grass_block')
    # 公園步道：三條分角線、環道
    path = np.zeros_like(park)
    for d in T.DIRV:
        bx, bz = -d[0], -d[1]
        t = (GX - T.CC) * bx + (GZ - T.CC) * bz; s = np.abs(-(GX - T.CC) * bz + (GZ - T.CC) * bx)
        path |= (t > 0) & (s <= 1.6)
    path |= np.abs(dT - 62) <= 1.2
    surf[park & path] = B('smooth_sandstone')
    # 塔前廣場
    base = np.zeros((SX, SZ), bool)
    base[T.X0:T.X1, T.X0:T.X1] = T.dilate(T.dilate(T.dilate(T.dilate(T.dilate(T.dilate(T.mask(T.F0)))))))
    surf[base & park] = B('polished_diorite')
    surf[base & park & (((np.arange(SX)[:, None] + np.arange(SZ)[None, :]) % 4) == 0)] = B('quartz_block')
    # 湖岸步道
    prom = (e > 1.0) & (e <= 1.12)
    surf[prom] = B('polished_diorite')
    # 道路
    road = np.zeros_like(park); road[:, 0:10] = True; road[0:10, :] = True
    side = np.zeros_like(park); side[:, 10:12] = True; side[10:12, :] = True; side &= ~road
    surf[road] = B('black_concrete')
    surf[side] = B('smooth_stone')
    for x in range(0, SX, 6):
        for k in range(3): surf[x + k if x + k < SX else x, 5] = B('white_concrete')
    for z in range(12, SZ, 6):
        for k in range(3): surf[5, z + k if z + k < SZ else z] = B('white_concrete')
    W.a[:, 3, :] = surf
    # ---- 湖 ----
    for y in (1, 2, 3):
        W.a[:, y, :][lake] = B('water')
    W.a[:, 0, :][lake] = B('sand')
    # ---- Y 形水道 ----
    chan = np.zeros_like(park)
    for i, d in enumerate(T.DIRV):
        t = (GX - T.CC) * d[0] + (GZ - T.CC) * d[1]; s = np.abs(-(GX - T.CC) * d[1] + (GZ - T.CC) * d[0])
        chan |= (t >= T.L0 + 13) & (t <= T.L0 + 36) & (s <= 2.4)
    chan &= park
    rim = T.dilate(chan) & ~chan
    W.a[:, 3, :][rim] = B('smooth_quartz')
    W.a[:, 2, :][chan] = B('prismarine')
    W.a[:, 3, :][chan] = B('water')
    jets = 0
    for i, d in enumerate(T.DIRV):
        for t in range(int(T.L0 + 15), int(T.L0 + 35), 4):
            x = int(T.CC + t * d[0]); z = int(T.CC + t * d[1])
            if chan[x, z]:
                W.put(x, 3, z, B('sea_lantern'))
                for y in (4, 5):
                    W.put(x, y, z, B('white_stained_glass'))
                jets += 1
    # ---- 步行橋 ----
    x0, x1, z0, z1 = BRIDGE
    for z in range(z0, z1 + 1):
        for x in range(x0, x1 + 1):
            W.put(x, 5, z, B('spruce_planks'))
            if x in (x0, x1):
                W.put(x, 6, z, B('spruce_fence'))
        if z % 8 == 0:
            for x in (x0, x1):
                for y in range(1, 5):
                    W.put(x, y, z, B('smooth_sandstone'))
                W.put(x, 7, z, W.lantern())
    for z in (z0 - 1, z1 + 1):        # 橋頭台階
        for x in range(x0, x1 + 1):
            W.put(x, 4, z, W.stairs('smooth_sandstone_stairs', 's' if z == z0 - 1 else 'n'))
    # ---- 杜拜噴泉 ----
    fountain(W, info)
    mall(W, info)
    souk(W, info)
    # ---- 棕櫚與路燈 ----
    palms = 0
    taken = set()
    def spot_ok(x, z):
        if (x // 5, z // 5) in taken: return False
        return W.get(x, 4, z) == 0 and W.get(x, 5, z) == 0
    for _ in range(9000):
        x, z = rng.randrange(14, SX - 2), rng.randrange(14, SZ - 2)
        if W.name(x, 3, z) == 'grass_block' and not path[x, z] and spot_ok(x, z) and dT[x, z] > T.L0 + 12:
            if rng.random() < .28:
                palm(W, x, z, rng); palms += 1; taken.add((x // 5, z // 5))
            elif rng.random() < .3:
                W.put(x, 4, z, B(rng.choice(['short_grass', 'azalea', 'flowering_azalea', 'red_tulip', 'pink_tulip'])))
    # 路邊與湖岸棕櫚
    for x in range(16, SX - 4, 9):
        if spot_ok(x, 11): palm(W, x, 11, rng); palms += 1
    for z in range(16, SZ - 4, 9):
        if spot_ok(11, z): palm(W, 11, z, rng); palms += 1
    for k in range(3, 360, 9):
        a = math.radians(k)
        cx, cz, rx, rz = LAKE
        x = int(cx + rx * 1.2 * math.cos(a)); z = int(cz + rz * 1.25 * math.sin(a))
        if 12 < x < SX - 2 and 12 < z < SZ - 2 and W.name(x, 3, z) in ('smooth_sandstone', 'cut_sandstone') and spot_ok(x, z):
            palm(W, x, z, rng); palms += 1
    lamps = 0
    for k in range(0, 360, 6):
        a = math.radians(k)
        cx, cz, rx, rz = LAKE
        x = int(cx + rx * 1.06 * math.cos(a)); z = int(cz + rz * 1.06 * math.sin(a))
        if 0 < x < SX and 0 < z < SZ and W.get(x, 4, z) == 0 and W.name(x, 3, z) == 'polished_diorite':
            for y in (4, 5, 6):
                W.put(x, y, z, B('polished_blackstone_wall'))
            W.put(x, 7, z, W.lantern())
            lamps += 1
    info.update(palms=palms, lamps=lamps, channel_jets=jets)
    # 水面封閉檢查
    wat = W.B('water')
    leak = 0
    for y in (1, 2, 3):
        m = W.a[:, y, :] == wat
        p = np.pad(W.a[:, y, :] == 0, 1, constant_values=False)
        nb_air = p[2:, 1:-1] | p[:-2, 1:-1] | p[1:-1, 2:] | p[1:-1, :-2]
        leak += int((m & nb_air).sum())
    info['water_leaks'] = leak


def palm(W, x, z, rng):
    B = W.B
    h = rng.randrange(6, 10)
    lean = rng.choice(list(DIRS.values()))
    cx, cz = x, z
    for y in range(4, 4 + h):
        if y == 4 + h // 2 + 1 and rng.random() < .6:
            cx += lean[0]; cz += lean[1]
        W.put(cx, y, cz, B('jungle_log'))
    top = 4 + h
    lv = B('jungle_leaves')
    W.put(cx, top, cz, lv)
    for dx, dz in list(DIRS.values()) + [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        diag = dx and dz
        n = 2 if diag else 3
        for k in range(1, n + 1):
            yy = top if k < n else top - 1
            W.put(cx + dx * k, yy, cz + dz * k, lv, keep=True)
    W.put(cx, top + 1, cz, lv)


def fountain(W, info):
    B = W.B
    cx, cz = 150, 168
    pts = []
    for k in range(0, 360, 6):
        a = math.radians(k)
        pts.append((int(cx + 64 * math.cos(a)), int(cz + 20 * math.sin(a)), 7 + int(9 * abs(math.sin(a * 3)))))
    for x in range(92, 210, 5):
        pts.append((x, cz, 12 + int(9 * abs(math.cos((x - cx) / 14.0)))))
    for x in range(110, 192, 6):
        pts.append((x, cz - 9, 6 + (x // 6) % 4)); pts.append((x, cz + 9, 6 + (x // 6) % 4))
    seen = set(); n = 0
    for x, z, h in pts:
        if (x, z) in seen or W.name(x, 3, z) != 'water': continue
        seen.add((x, z))
        W.put(x, 3, z, B('sea_lantern'))
        for y in range(4, 4 + h):
            W.put(x, y, z, B('white_stained_glass') if y < 2 + h else B('light_blue_stained_glass'))
        W.put(x, 4 + h, z, B('white_stained_glass'))
        n += 1
    info['fountain_jets'] = n
    info['fountain_center'] = (cx, 4, cz)


def mall(W, info):
    """杜拜購物中心（簡化外觀＋水族館）"""
    B = W.B
    x0, x1, z0, z1 = MALL
    H = 26
    sand = B('smooth_sandstone'); cut = B('cut_sandstone'); gl = B('light_blue_stained_glass'); roof = B('white_concrete')
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            W.put(x, 3, z, B('polished_diorite') if (x + z) % 2 else B('quartz_block'))
            for y in range(4, H):
                if edge:
                    k = (x - x0) if z in (z0, z1) else (z - z0)
                    if k % 6 == 0: b = cut
                    elif y in (13, 14, 22, 23): b = cut
                    elif z == z1 and 176 <= x <= 240: b = gl
                    elif 6 <= y <= 11 or 16 <= y <= 20: b = gl
                    else: b = sand
                    W.put(x, y, z, b)
            W.put(x, H, z, roof)
            if x in (x0, x1) or z in (z0, z1):
                W.put(x, H + 1, z, sand if (x + z) % 2 else B('sandstone_slab'))
    # 二樓樓板與中庭
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            atrium = 188 <= x <= 228 and 36 <= z <= 104
            if not atrium:
                W.put(x, 14, z, B('smooth_stone'))
                if x % 6 == 0 and z % 6 == 0:
                    W.put(x, 14, z, B('sea_lantern'))
            elif x % 4 == 0 or z % 4 == 0:
                W.put(x, H, z, B('glass'))
            if (x % 6 == 0 and z % 6 == 0):
                W.put(x, H, z, B('sea_lantern')) if not atrium else None
    # 中庭欄杆
    for x in range(187, 230):
        for z in (35, 105):
            W.put(x, 15, z, B('glass_pane'))
    for z in range(35, 106):
        for x in (187, 229):
            W.put(x, 15, z, B('glass_pane'))
    # 店面隔間（沿北、東牆）
    cols = ['red', 'yellow', 'lime', 'light_blue', 'magenta', 'orange', 'pink', 'cyan']
    for i, x in enumerate(range(x0 + 2, x1 - 6, 8)):
        c = cols[i % len(cols)]
        for fy in (4, 15):
            for z in range(z0 + 1, z0 + 8):
                W.put(x, fy, z, B('smooth_quartz')); W.put(x, fy + 1, z, B('smooth_quartz')); W.put(x, fy + 2, z, B('smooth_quartz'))
            for xx in range(x + 1, x + 8):
                if xx >= x1: break
                for y in (fy, fy + 1, fy + 2):
                    W.put(xx, y, z0 + 8, B(c + '_stained_glass') if not (xx == x + 4 and y < fy + 2) else 0)
                W.put(xx, fy + 3, z0 + 8, B(c + '_concrete'))
                W.put(xx, fy, z0 + 3, B('barrel', facing_direction=1) if xx % 2 else B(c + '_wool'))
    # 水族館（Dubai Aquarium）
    ax0, ax1, az0, az1 = 196, 220, 62, 74
    for x in range(ax0, ax1 + 1):
        for z in range(az0, az1 + 1):
            for y in range(4, 21):
                edge = x in (ax0, ax1) or z in (az0, az1) or y == 20
                W.put(x, y, z, B('glass') if edge else B('water'))
            if ax0 < x < ax1 and az0 < z < az1:
                W.put(x, 3, z, B('sand'))
                r = (x * 7 + z * 13) % 11
                if r == 0: W.put(x, 4, z, B('tube_coral_block')); W.put(x, 5, z, B('brain_coral_block'))
                elif r == 3: W.put(x, 4, z, B('fire_coral_block'))
                elif r == 6: W.put(x, 4, z, B('sea_lantern'))
                elif r == 8: W.put(x, 4, z, B('prismarine'))
    # 臨湖大門與雨庇
    for x in range(200, 217):
        for y in (4, 5, 6):
            W.put(x, y, z1, 0)
        for z in range(z1 + 1, z1 + 6):
            W.put(x, 9, z, B('smooth_quartz_slab'))
    for x in (200, 216):
        for y in range(4, 9):
            W.put(x, y, z1 + 5, B('quartz_pillar'))
    # 北側入口
    for x in range(204, 213):
        for y in (4, 5, 6):
            W.put(x, y, z0, 0)
    info['mall'] = (x0, 4, z0, x1, H, z1)
    info['aquarium'] = (ax0, 4, az0)


def souk(W, info):
    """巴哈爾市集（阿拉伯風）"""
    B = W.B
    x0, x1, z0, z1 = SOUK
    H = 14
    sand = B('smooth_sandstone'); cut = B('cut_sandstone'); chis = B('chiseled_sandstone'); ss = B('sandstone')
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            W.put(x, 3, z, B('hardened_clay') if (x + z) % 3 == 0 else B('smooth_sandstone'))
            if edge:
                for y in range(4, H):
                    k = (x - x0) if z in (z0, z1) else (z - z0)
                    b = sand
                    if y in (9, H - 1): b = cut
                    if k % 8 == 0: b = chis if y in (8, 12) else ss
                    W.put(x, y, z, b)
            W.put(x, H, z, sand)
            if edge:
                W.put(x, H + 1, z, cut if (x + z) % 2 == 0 else 0)
    # 臨湖拱廊（北面）
    for ax in range(x0 + 4, x1 - 2, 8):
        for x in range(ax - 1, ax + 2):
            for y in (4, 5, 6):
                W.put(x, y, z0, 0)
        W.put(ax - 1, 7, z0, W.stairs('sandstone_stairs', 'w', True))
        W.put(ax + 1, 7, z0, W.stairs('sandstone_stairs', 'e', True))
        W.put(ax, 7, z0, B('chiseled_sandstone'))
        # 窗：小格子
        for y in (10, 11):
            W.put(ax + 4, y, z0, B('dark_oak_trapdoor', direction=2, open_bit=True))
    # 室內走道與攤位
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if z == z0 + 9 or z == z0 + 26:
                continue
            if (z - z0) % 9 == 4 and x % 5 == 0:
                W.put(x, 4, z, B('barrel', facing_direction=1))
                W.put(x, 5, z, B(['red_carpet', 'orange_carpet', 'yellow_carpet', 'purple_carpet'][(x // 5) % 4]))
            if x % 7 == 0 and z % 7 == 0:
                W.put(x, H - 1, z, W.lantern(hanging=True))
    # 二樓地板
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if not (z0 + 12 <= z <= z0 + 22 and (x - x0) % 20 < 12):
                W.put(x, 9, z, sand)
    # 風塔與圓頂
    towers = []
    for tx in (x0 + 6, x0 + 34, x0 + 62, x1 - 6):
        tz = z0 + 6
        for x in range(tx - 2, tx + 2):
            for z in range(tz - 2, tz + 2):
                for y in range(H, H + 11):
                    edge = x in (tx - 2, tx + 1) or z in (tz - 2, tz + 1)
                    if not edge: continue
                    slit = y in range(H + 6, H + 10) and ((x + z) % 2 == 0)
                    W.put(x, y, z, B('dark_oak_fence') if slit else (cut if y == H + 10 else sand))
                W.put(x, H + 11, z, B('sandstone_slab'))
        towers.append((tx, H + 11, tz))
    for dx, dz in ((x0 + 20, z0 + 20), (x0 + 48, z0 + 20), (x0 + 76, z0 + 22)):
        for x in range(dx - 4, dx + 5):
            for z in range(dz - 4, dz + 5):
                for y in range(H + 1, H + 6):
                    r = math.sqrt((x - dx) ** 2 + (z - dz) ** 2 + ((y - H - 1) * 1.1) ** 2)
                    if 3.2 <= r <= 4.4:
                        W.put(x, y, z, sand)
        W.put(dx, H + 6, dz, B('chiseled_sandstone'))
        W.put(dx, H + 7, dz, B('end_rod', facing_direction=1))
    info['souk'] = (x0, 4, z0)
    info['windtowers'] = towers
