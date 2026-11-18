"""吉薩大金字塔 1:1 生成器。座標：x 東、z 南、y 上；m＝離金字塔底面的高度（第 m 層在 y=G+1+m）。"""
import math
import numpy as np
from core import *

PX, PZ = 140, 140          # 大金字塔中心
HW0, HGT = 115, 146.6      # 底半寬、原高
TOPK = 146                 # 最上一層 k
QX = PX + 7                # 通道平面西側那一格（通道寬 2：QX, QX+1）

rng = np.random.RandomState(261118)


def Y(m):
    return G + 1 + m


def hw_of(k, hw0=HW0, h=HGT):
    return int(round(hw0 * (1 - k / h)))


class Ctx:
    pass


def mats(W):
    M = {}
    def pick(*pairs):
        ids = np.array([p[0] for p in pairs], np.uint16); w = np.array([p[1] for p in pairs], float); w /= w.sum()
        return lambda n=None: (ids[rng.choice(len(ids), p=w)] if n is None else ids[rng.choice(len(ids), size=n, p=w)])
    B = W.B
    M['casing'] = pick((B('smooth_quartz'), 9), (B('quartz_block'), 1))
    M['core'] = pick((B('sandstone'), 6), (B('cut_sandstone'), 2), (B('smooth_sandstone'), 1), (B('end_stone'), 1))
    M['fine'] = pick((B('smooth_sandstone'), 7), (B('cut_sandstone'), 2), (B('sandstone'), 1))       # 圖拉細石灰岩內襯
    M['granite'] = pick((B('polished_granite'), 8), (B('granite'), 2))
    M['rock'] = pick((B('end_stone'), 7), (B('sandstone'), 3))
    M['rough'] = pick((B('sandstone'), 4), (B('end_stone'), 3), (B('gravel'), 1), (B('cut_sandstone'), 1))
    M['pave'] = pick((B('smooth_sandstone'), 6), (B('cut_sandstone'), 3), (B('sandstone'), 1))
    M['sand'] = pick((B('sand'), 60), (B('red_sand'), 1))
    M['mastaba'] = pick((B('smooth_sandstone'), 5), (B('cut_sandstone'), 3), (B('sandstone'), 2))
    return M


# ------------------------------------------------------------------ 地形
def terrain(W, M, C):
    X, Yn, Z = W.size
    a = W.a
    a[:, :G - 2, :] = M['rock']((X, G - 2, Z))
    a[:, G - 2:G + 1, :] = M['sand']((X, 3, Z))
    # 鋪石台：大金字塔圍牆內
    a[16:265, G, 16:265] = M['pave']((249, 249))
    grid = np.zeros((249, 249), bool); grid[::4, :] = True; grid[:, ::4] = True
    sub = a[16:265, G, 16:265]; sub[grid] = W.B('cut_sandstone')
    a[16:265, G - 1, 16:265] = M['rock']((249, 249))
    C.reserved = np.zeros((X, Z), bool)
    C.reserved[8:272, 8:272] = True


def dunes(W, M, C):
    X, _, Z = W.size
    n = fbm((X, Z), 70, 7, 4)
    n2 = fbm((X, Z), 18, 9, 3)
    h = np.clip((n * 3.2 + n2 * 1.2), 0, 4).astype(int)
    res = C.reserved.copy()
    # 膨脹 4 格當緩衝
    for _ in range(4):
        r2 = res.copy(); r2[1:] |= res[:-1]; r2[:-1] |= res[1:]; r2[:, 1:] |= res[:, :-1]; r2[:, :-1] |= res[:, 1:]; res = r2
    sand = W.B('sand'); dead = W.B('deadbush'); dg = W.B('short_dry_grass'); tg = W.B('tall_dry_grass')
    for x in range(X):
        for z in range(Z):
            if res[x, z]:
                continue
            for d in range(1, h[x, z] + 1):
                W.a[x, G + d, z] = sand
            r = rng.rand()
            top = G + h[x, z]
            if W.a[x, top, z] == sand and W.a[x, top + 1, z] == 0:
                if r < 0.004: W.a[x, top + 1, z] = dead
                elif r < 0.010: W.a[x, top + 1, z] = dg
                elif r < 0.012: W.a[x, top + 1, z] = tg


# ------------------------------------------------------------------ 金字塔（大、小共用）
def pyramid(W, M, C, cx, cz, hw0, h, gold_top=False, zone=None):
    """實心金字塔＋兩格外殼＋外緣樓梯。回傳 top k。"""
    a = W.a
    kmax = int(math.floor(h))
    hws = [int(round(hw0 * (1 - k / h))) for k in range(kmax + 2)]
    stq = {d: W.stairs('smooth_quartz_stairs', d) for d in 'nesw'}
    stq2 = {d: W.stairs('quartz_stairs', d) for d in 'nesw'}
    gold = W.B('gold_block')
    for k in range(kmax + 1):
        hw = hws[k]; y = G + 1 + k
        if y >= W.size[1]: break
        x0, x1, z0, z1 = cx - hw, cx + hw, cz - hw, cz + hw
        n = 2 * hw + 1
        a[x0:x1 + 1, y, z0:z1 + 1] = M['core']((n, n))
        dx = np.abs(np.arange(-hw, hw + 1))
        cheb = np.maximum(dx[:, None], dx[None, :])
        cas = cheb >= hw - 1
        sub = a[x0:x1 + 1, y, z0:z1 + 1]
        sub[cas] = M['casing'](int(cas.sum()))
        if zone is not None:
            zs = zone[x0:x1 + 1, y, z0:z1 + 1]; zs[:] = 1; zs[cas] = 2
        if gold_top and hw <= 2:
            sub[:] = gold
            continue
        if hws[k + 1] < hw and hw > 0:
            for i in range(-hw, hw + 1):
                for (xx, zz, d) in ((cx + i, cz - hw, 's'), (cx + i, cz + hw, 'n'), (cx - hw, cz + i, 'e'), (cx + hw, cz + i, 'w')):
                    if d in 'ew' and abs(i) == hw:
                        continue      # 角由南北邊負責
                    a[xx, y, zz] = (stq2 if rng.rand() < 0.1 else stq)[d]
    return kmax


# ------------------------------------------------------------------ 內部空腔
class Voids:
    """標籤陣列：每個空腔區域給內襯材料（水平向/垂直向可不同）。"""
    def __init__(self, W):
        self.W = W
        self.V = np.zeros(W.size, np.uint8)
        self.info = {0: None}
        self.post = []   # 挖完後才放的方塊 (x,y,z,b)

    def label(self, name, side, vert=None, light=True):
        i = len(self.info)
        self.info[i] = dict(name=name, side=side, vert=vert or side, light=light)
        return i

    def box(self, L, x0, m0, z0, x1, m1, z1):
        x0, x1 = sorted((x0, x1)); z0, z1 = sorted((z0, z1)); m0, m1 = sorted((m0, m1))
        self.V[x0:x1 + 1, Y(m0):Y(m1) + 1, z0:z1 + 1] = L

    def cell(self, L, x, m, z):
        self.V[x, Y(m), z] = L

    def put(self, x, m, z, b):
        self.post.append((x, Y(m), z, b))


def slope_z(VD, L, x0, x1, z0, z1, floor, H, mat_st, ceil_st=True):
    """沿 z 的通道；floor(z) 回傳地板第一格空氣的 m。自動加樓梯地板與倒樓梯天花板。"""
    W = VD.W
    for z in range(z0, z1 + 1):
        s = floor(z)
        VD.box(L, x0, s, z, x1, s + H - 1, z)
    for z in range(z0, z1 + 1):
        s = floor(z)
        for dz, d in ((1, 's'), (-1, 'n')):
            zn = z + dz
            if z0 <= zn <= z1:
                if floor(zn) == s + 1:
                    for x in range(x0, x1 + 1):
                        VD.put(x, s, z, W.stairs(mat_st, d))
                if ceil_st and floor(zn) + H == s + H + 1:
                    for x in range(x0, x1 + 1):
                        VD.put(x, s + H, z, ('ceil', W.stairs(mat_st, OPP[d], True)))


def shaft(VD, L, x, m, z, dz, slope, horiz=2, max_len=400, stop_len=None):
    """1×1 斜孔：先水平 horiz 格，再以 slope（升/水平）斜上，6 連通。回傳最後一格。"""
    W = VD.W
    cells = []
    for i in range(horiz):
        z += dz; cells.append((x, m, z))
    base_m, base_z, d = m, z, 0
    while d < max_len:
        d += 1
        tgt = base_m + int(round(slope * d))
        while m < tgt:
            m += 1; cells.append((x, m, z))
        z += dz; cells.append((x, m, z))
        if stop_len and math.hypot(d, d * slope) >= stop_len:
            break
        if W.a[x, Y(m), z] == 0 and W.a[x, Y(m) + 1, z] == 0:   # 已出外殼
            break
    for (cx, cm, cz) in cells:
        VD.cell(L, cx, cm, cz)
    return cells


def interior(W, M, C, VD):
    B = W.B
    fine = VD.label('細石灰岩通道', 'fine')
    gran = VD.label('花崗岩', 'granite')
    relief = VD.label('減壓室', 'fine', 'granite')
    rough = VD.label('盜洞', 'rough')
    rock = VD.label('岩盤', 'rock')
    sealed = VD.label('密封空腔', 'fine', light=False)
    shaftL = VD.label('通氣孔', None, light=False)
    C.L = dict(fine=fine, gran=gran, relief=relief, rough=rough, rock=rock, sealed=sealed, shaft=shaftL)
    P = {}
    ZE = PZ - 102                                   # 原始入口
    desc = lambda z: 17 - (z - ZE) // 2               # 下降通道地板
    zbot = ZE + 2 * 44                               # 地板 -27
    slope_z(VD, fine, QX, QX + 1, ZE, zbot + 1, lambda z: max(desc(z), -27), 3, 'smooth_sandstone_stairs')
    P['entrance'] = (QX, 17, ZE)
    # 水平通道到地下室（岩盤）
    VD.box(rock, QX, -27, zbot + 2, QX + 1, -25, PZ - 6)
    VD.box(rock, QX - 1, -27, PZ - 10, QX - 1, -26, PZ - 10)          # 小凹室
    # 地下室：東半平、西半未完工岩丘
    sx0, sx1, sz0, sz1 = PX - 5, PX + 8, PZ - 5, PZ + 2
    VD.box(rock, sx0, -28, sz0, sx1, -25, sz1)
    for x in range(sx0, PX + 1):
        for z in range(sz0, sz1 + 1):
            hh = int((PX + 1 - x) * 0.45 + (1.2 if (z - sz0) % 3 == 1 else 0) + rng.rand() * 1.3)
            for k in range(min(hh, 3)):
                VD.put(x, -28 + k, z, ('solid', M['rough']()))
    VD.box(rock, PX + 3, -33, PZ - 2, PX + 4, -29, PZ - 1)          # 坑
    VD.box(rock, PX + 1, -28, sz1 + 1, PX + 2, -27, sz1 + 16)        # 南側死路
    P['sub'] = (PX + 6, -28, PZ - 2)
    # 上升通道：從下降通道頂分岔，地板 22 於 z=PZ-42
    Z0 = PZ - 42
    asc = lambda z: 22 - (Z0 - z + 1) // 2
    slope_z(VD, fine, QX, QX + 1, PZ - 76, Z0 - 1, asc, 3, 'smooth_sandstone_stairs')
    for z in range(PZ - 75, PZ - 70):                                 # 三塊花崗岩塞
        s = asc(z)
        for x in (QX, QX + 1):
            for m in range(s - 1, s + 3):
                VD.put(x, m, z, ('solid', B('polished_granite')))
    # 阿爾-馬蒙盜洞
    zf = PZ - hw_of(7)
    VD.box(rough, PX + 3, 7, zf - 2, PX + 5, 9, PZ - 69)
    for z in range(zf, PZ - 69):
        if rng.rand() < 0.35: VD.cell(rough, PX + 2, 7 + rng.randint(0, 3), z)
        if rng.rand() < 0.35: VD.cell(rough, PX + 6, 7 + rng.randint(0, 3), z) if z < PZ - 82 else None
        if rng.rand() < 0.3: VD.cell(rough, PX + 3 + rng.randint(0, 3), 10, z)
    VD.box(rough, PX + 5, 8, PZ - 70, QX + 1, 10, PZ - 69)            # 接上升通道（塞石上方）
    VD.box(rough, PX + 5, 7, PZ - 80, PX + 6, 9, PZ - 79)              # 接下降通道
    P['mamun'] = (PX + 4, 7, zf - 1)
    # 現代階梯（盜洞口）
    st = W.stairs('sandstone_stairs', 's')
    for x in range(PX + 2, PX + 7):
        for z in range(zf - 6, zf):
            for m in range(-1, 7):
                VD.put(x, m, z, ('keep', M['pave']()))
        for j in range(1, 7):
            z = zf - 6 - j; m = 6 - j
            VD.put(x, m, z, ('keep', st))
            for mm in range(-1, m):
                VD.put(x, mm, z, ('keep', B('cut_sandstone')))
    for z in range(zf - 12, zf):
        top = 6 if z >= zf - 6 else 6 - (zf - 6 - z)
        for x in (PX + 1, PX + 7):
            for mm in range(-1, top + 1):
                VD.put(x, mm, z, ('keep', B('cut_sandstone')))
            VD.put(x, top + 1, z, ('keep', B('sandstone_wall')))
    # 王后墓室通道與墓室
    VD.box(fine, QX, 22, Z0, QX + 1, 24, PZ - 9)
    VD.box(fine, QX, 21, PZ - 8, QX + 1, 23, PZ - 3)                  # 末段下降一階
    qx0, qx1, qz0, qz1 = PX + 3, PX + 8, PZ - 2, PZ + 2
    VD.box(fine, qx0, 21, qz0, qx1, 25, qz1)
    VD.box(fine, qx0, 26, qz0 + 1, qx1, 26, qz1 - 1)
    VD.box(fine, qx0, 27, qz0 + 2, qx1, 27, qz1 - 2)
    for x in range(qx0, qx1 + 1):
        VD.put(x, 26, qz0, ('ceil', W.stairs('smooth_sandstone_stairs', 'n', True)))
        VD.put(x, 26, qz1, ('ceil', W.stairs('smooth_sandstone_stairs', 's', True)))
        VD.put(x, 27, qz0 + 1, ('ceil', W.stairs('smooth_sandstone_stairs', 'n', True)))
        VD.put(x, 27, qz1 - 1, ('ceil', W.stairs('smooth_sandstone_stairs', 's', True)))
    VD.box(fine, qx1 + 1, 21, PZ, qx1 + 1, 23, PZ + 1)                 # 東牆疊澀龕
    VD.box(fine, qx1 + 1, 24, PZ, qx1 + 1, 25, PZ)
    VD.box(rough, qx1 + 2, 21, PZ, qx1 + 5, 22, PZ)                   # 尋寶者在龕後挖的洞
    for x in range(qx0, qx1 + 1):                                     # 未完工粗地板
        if rng.rand() < 0.5: VD.put(x, 20, qz0 + rng.randint(0, 5), ('solid', M['rough']()))
    P['queen'] = (PX + 5, 21, PZ)
    # 王后墓室通氣孔（未通到外面）
    n_end = shaft(VD, shaftL, PX + 5, 22, qz0, -1, 0.82, horiz=2, stop_len=58)[-1]
    s_end = shaft(VD, shaftL, PX + 5, 22, qz1, 1, 0.82, horiz=2, stop_len=60)[-1]
    VD.put(s_end[0], s_end[1], s_end[2] + 1, ('solid', B('copper_block')))   # 甘騰布林克小門
    VD.put(n_end[0], n_end[1], n_end[2] - 1, ('solid', B('copper_block')))
    P['gant'] = s_end
    # 大走廊
    gal = lambda z: 22 + (z - Z0) // 2
    zg1 = PZ - 3
    stair_g = 'smooth_sandstone_stairs'
    for z in range(Z0, zg1 + 1):
        s = gal(z)
        low = z < Z0 + 8
        bot = 22 if low else s
        VD.box(fine, QX - 1, bot, z, QX + 2, s + 4, z)
        VD.box(fine, QX, s + 5, z, QX + 1, s + 8, z)
        VD.put(QX - 1, s + 5, z, ('ceil', W.stairs(stair_g, 'w', True)))
        VD.put(QX + 2, s + 5, z, ('ceil', W.stairs(stair_g, 'e', True)))
        if not low:
            for x, side in ((QX - 1, 'w'), (QX + 2, 'e')):
                VD.put(x, s, z, ('solid', B('chiseled_sandstone') if (z - Z0) % 3 == 0 else B('smooth_sandstone')))
    for z in range(Z0 + 8, zg1 + 1):
        s = gal(z)
        for dz, d in ((1, 's'), (-1, 'n')):
            zn = z + dz
            if Z0 + 8 <= zn <= zg1 and gal(zn) == s + 1:
                for x in (QX, QX + 1):
                    VD.put(x, s, z, W.stairs(stair_g, d))
            if Z0 <= zn <= zg1 and gal(zn) == s + 1:
                for x in (QX, QX + 1):
                    VD.put(x, s + 9, z, ('ceil', W.stairs(stair_g, OPP[d], True)))
                for x in (QX - 1, QX + 2):
                    VD.put(x, s + 5, z, ('ceil', W.stairs(stair_g, 'w' if x == QX - 1 else 'e', True)))
    # 走廊下端：現代木梯（跨過王后通道口）
    sp = lambda d: W.stairs('spruce_stairs', d)
    for i in range(4):
        VD.put(QX + 2, 22 + i, Z0 + 1 + i, sp('s'))
        for m in range(22, 22 + i):
            VD.put(QX + 2, m, Z0 + 1 + i, ('solid', B('spruce_planks')))
    for z in range(Z0 + 5, Z0 + 8):
        VD.put(QX + 2, 25, z, ('solid', B('spruce_planks')))
        for m in range(22, 25):
            VD.put(QX + 2, m, z, B('spruce_fence') if z == Z0 + 5 else 0)
    VD.put(QX + 2, 26, Z0 + 8, W.stairs(stair_g, 's'))
    P['gallery'] = (QX, gal(Z0 + 10), Z0 + 10)
    # 井道：大走廊下端西牆 → 下降通道
    wx, wz = PX + 5, PZ - 41
    VD.box(fine, wx, -10, wz, wx, 24, wz)
    for m in range(-10, 25):
        VD.put(wx, m, wz, W.ladder('e'))
    for z in range(wz - 2, wz + 3):                                    # 洞穴（天然岩洞）
        for x in range(wx + 1, wx + 4):
            for m in range(3, 7):
                if rng.rand() < 0.8 or (x == wx + 1 and m < 6):
                    VD.cell(rough, x, m, z)
    for i in range(1, 8):
        z = wz + i; s = -10 - i
        VD.box(rough, wx, s, z, wx, s + 2, z)
        VD.put(wx, s, z, W.stairs('sandstone_stairs', 'n'))
    VD.box(rough, wx + 1, -17, wz + 7, wx + 1, -15, wz + 7)
    P['grotto'] = (wx + 2, 3, wz)
    # 大台階、前室、國王墓室
    VD.box(fine, QX - 1, 42, zg1 + 1, QX + 2, 50, zg1 + 2)
    for x in (QX, QX + 1):
        VD.put(x, 41, zg1, W.stairs(stair_g, 's'))
        VD.put(x, 42, zg1 + 2, W.stairs('polished_granite_stairs', 's'))
    VD.box(gran, QX, 43, zg1 + 3, QX + 1, 44, zg1 + 4)                # 低通道
    VD.box(gran, QX, 43, zg1 + 5, QX + 1, 46, zg1 + 7)                # 前室
    for z in (zg1 + 5, zg1 + 6, zg1 + 7):
        for x in (QX - 1, QX + 2):
            VD.box(gran, x, 45, z, x, 46, z)                          # 吊門槽
    for x in (QX, QX + 1):
        VD.put(x, 46, zg1 + 5, ('solid', B('polished_granite')))     # 花崗岩橫板（granite leaf）
        VD.put(x, 45, zg1 + 5, ('solid', W.slab('polished_granite_slab', True)))
    VD.box(gran, QX, 43, zg1 + 8, QX + 1, 44, zg1 + 9)
    kx0, kx1, kz0, kz1 = PX - 1, PX + 8, zg1 + 10, zg1 + 14
    VD.box(gran, kx0, 43, kz0, kx1, 48, kz1)
    # 石棺（放大 1.5 倍）
    for x in range(PX, PX + 3):
        for z in range(kz0, kz0 + 4):
            if not (x == PX + 1 and kz0 + 1 <= z <= kz0 + 2) and not (x == PX + 2 and z == kz0 + 3):
                VD.put(x, 43, z, ('solid', B('granite')))
    VD.put(PX + 2, 43, kz0 + 3, ('solid', W.slab('granite_slab')))
    P['king'] = (PX + 5, 43, kz0 + 2)
    # 國王墓室通氣孔（通到外面）
    shaft(VD, shaftL, PX + 4, 44, kz0, -1, 0.637, horiz=2)
    shaft(VD, shaftL, PX + 4, 44, kz1, 1, 1.0, horiz=2)
    # 減壓室 5 層
    rows = [(50, 51), (53, 54), (56, 57), (59, 60), (62, 63)]
    for (m0, m1) in rows:
        VD.box(relief, kx0, m0, kz0, kx1, m1, kz1)
    VD.box(relief, kx0, 64, kz0 + 1, kx1, 64, kz1 - 1)
    VD.box(relief, kx0, 65, kz0 + 2, kx1, 65, kz1 - 2)
    for x in range(kx0, kx1 + 1):
        VD.put(x, 64, kz0, ('ceil', W.stairs('smooth_sandstone_stairs', 'n', True)))
        VD.put(x, 64, kz1, ('ceil', W.stairs('smooth_sandstone_stairs', 's', True)))
        VD.put(x, 65, kz0 + 1, ('ceil', W.stairs('smooth_sandstone_stairs', 'n', True)))
        VD.put(x, 65, kz1 - 1, ('ceil', W.stairs('smooth_sandstone_stairs', 's', True)))
    # 戴維森通道（走廊頂東側）＋維斯炸開的梯井
    VD.box(rough, QX + 3, 42, zg1 + 1, QX + 3, 49, zg1 + 1)
    for m in range(42, 50):
        VD.put(QX + 3, m, zg1 + 1, W.ladder('w'))
    VD.box(rough, QX + 3, 48, zg1 + 2, QX + 3, 49, kz0 + 2)
    lx, lz = QX + 3, kz0 + 2
    VD.box(rough, lx, 48, lz, lx, 63, lz)
    for m in range(48, 64):
        VD.put(lx, m, lz, W.ladder('n'))
    for (m0, m1) in rows:
        VD.box(rough, kx1 + 1, m0, lz, kx1 + 1, m1, lz)
    P['relief'] = (PX + 3, 62, kz0 + 2)
    # 坎貝爾室紅色塗鴉（施工隊名＋古夫王名框）
    red = B('red_terracotta')
    for (dx, dm) in ((0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (3, 1), (1, 1), (5, 0), (6, 1), (7, 0)):
        VD.put(PX + dx, 62 + dm, kz0 - 1, ('wall', red))
    # 北面走廊（2023 ScanPyramids）
    zn0 = PZ - hw_of(24) + 2
    VD.box(sealed, QX, 24, zn0, QX + 1, 25, zn0 + 8)
    for z in range(zn0, zn0 + 9):
        VD.put(QX, 26, z, ('ceil', W.stairs('smooth_sandstone_stairs', 'w', True)))
        VD.put(QX + 1, 26, z, ('ceil', W.stairs('smooth_sandstone_stairs', 'e', True)))
    # 大空洞（2017 緲子成像，形狀未知，示意）
    VD.box(sealed, QX, 53, PZ - 36, QX + 1, 58, PZ - 7)
    C.P = P
    C.ZE, C.Z0, C.zg1, C.kz = ZE, Z0, zg1, (kz0, kz1)


def chevrons(W, M, C):
    """原始入口上方的山形石（立面上可見）。"""
    a = W.a
    st = lambda d: W.stairs('smooth_sandstone_stairs', d)
    for m, pairs in ((20, ((QX - 1, 'e'), (QX + 2, 'w'))), (21, ((QX, 'e'), (QX + 1, 'w'))),
                     (22, ((QX - 2, 'e'), (QX + 3, 'w'))), (23, ((QX - 1, 'e'), (QX + 2, 'w')))):
        z = PZ - hw_of(m)
        for x, d in pairs:
            a[x, Y(m), z] = st(d)
    for m in (20,):
        z = PZ - hw_of(m)
        a[QX, Y(m), z] = a[QX + 1, Y(m), z] = W.B('chiseled_sandstone')


def apply_voids(W, M, C, VD, zone):
    a = W.a; V = VD.V
    X, Yn, Z = W.size
    for L, inf in VD.info.items():
        if not inf or not inf['side']:
            continue
        m = V == L
        if not m.any():
            continue
        xs, ys, zs = np.nonzero(m)
        x0, x1, y0, y1, z0, z1 = max(xs.min() - 1, 0), xs.max() + 2, max(ys.min() - 1, 0), ys.max() + 2, max(zs.min() - 1, 0), zs.max() + 2
        mm = m[x0:x1, y0:y1, z0:z1]
        hor = np.zeros_like(mm); ver = np.zeros_like(mm)
        hor[1:] |= mm[:-1]; hor[:-1] |= mm[1:]; hor[:, :, 1:] |= mm[:, :, :-1]; hor[:, :, :-1] |= mm[:, :, 1:]
        ver[:, 1:] |= mm[:, :-1]; ver[:, :-1] |= mm[:, 1:]
        sub = a[x0:x1, y0:y1, z0:z1]; vz = V[x0:x1, y0:y1, z0:z1]; zz = zone[x0:x1, y0:y1, z0:z1]
        ok = (sub != 0) & (vz == 0) & (zz != 2)
        for msk, key in ((ver & ok, inf['vert']), (hor & ok & ~ver, inf['side'])):
            n = int(msk.sum())
            if n:
                sub[msk] = M[key](n)
    a[V > 0] = 0
    for (x, y, z, b) in VD.post:
        if isinstance(b, tuple):
            kind, blk = b
            if kind == 'keep':
                if a[x, y, z] == 0 and V[x, y, z] == 0: a[x, y, z] = blk
            elif kind == 'ceil':
                if V[x, y, z] == 0: a[x, y, z] = blk
            elif kind == 'wall':
                if V[x, y, z] == 0: a[x, y, z] = blk
            else:
                a[x, y, z] = blk
        else:
            a[x, y, z] = b


def lights(W, M, C, VD):
    """現代參觀照明：空腔頂上每隔幾格嵌一顆赭黃蛙明燈。"""
    a = W.a; V = VD.V
    fl = W.B('ochre_froglight')
    n = 0
    xs, zs = np.nonzero((V > 0).any(axis=1))
    for x, z in zip(xs.tolist(), zs.tolist()):
        if not (x % 4 == 3 and z % 5 == 0):
            continue
        col = V[x, :, z]
        ys = np.nonzero(col)[0]
        for y in ys.tolist():
            L = int(col[y])
            if not VD.info[L]['light'] or not VD.info[L]['side']:
                continue
            if col[y + 1] == 0 and a[x, y + 1, z] != 0 and a[x, y, z] == 0:
                a[x, y + 1, z] = fl; n += 1
    return n


# ------------------------------------------------------------------ 周邊
def enclosure(W, M, C):
    a = W.a; B = W.B
    cap = W.slab('sandstone_slab')
    def wall_seg(x0, z0, x1, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if 256 <= x <= 295 and 112 <= z <= 168:
                    continue
                a[x, G + 1:G + 8, z] = M['mastaba'](7)
                a[x, G + 8, z] = cap
    wall_seg(14, 14, 266, 15); wall_seg(14, 265, 266, 266); wall_seg(14, 14, 15, 266); wall_seg(265, 14, 266, 266)
    # 北門、南門開口
    for (x0, x1, z0, z1) in ((PX - 2, PX + 2, 14, 15), (PX - 2, PX + 2, 265, 266), (14, 15, PZ - 2, PZ + 2)):
        a[x0:x1 + 1, G + 1:G + 9, z0:z1 + 1] = 0


def temple(W, M, C):
    a = W.a; B = W.B
    x0, x1, z0, z1 = 256, 295, 114, 166
    C.reserved[x0 - 2:x1 + 3, z0 - 2:z1 + 3] = True
    bas = B('smooth_basalt'); pb = B('polished_basalt')
    a[x0:x1 + 1, G, z0:z1 + 1] = bas
    a[x0:x1 + 1, G - 1, z0:z1 + 1] = M['rock']((x1 - x0 + 1, z1 - z0 + 1))
    for x in range(x0, x1 + 1, 3):
        a[x, G, z0:z1 + 1] = pb
    h = 8
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if edge:
                a[x, G + 1:G + h + 1, z] = M['mastaba'](h)
                a[x, G + h + 1, z] = W.slab('smooth_sandstone_slab')
    # 東門（接參道）
    a[x1, G + 1:G + 5, 137:144] = 0
    # 庭院四周柱廊：花崗岩柱＋屋頂
    cx0, cx1, cz0, cz1 = x0 + 4, x1 - 4, z0 + 4, z1 - 4
    gp = B('polished_granite'); roof = M['mastaba']
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            inner = cx0 <= x <= cx1 and cz0 <= z <= cz1
            if not inner:
                a[x, G + h, z] = roof()
    for x in range(cx0, cx1 + 1, 3):
        for z in (cz0, cz1):
            a[x, G + 1:G + h, z] = gp
    for z in range(cz0, cz1 + 1, 3):
        for x in (cx0, cx1):
            a[x, G + 1:G + h, z] = gp
    # 西側聖所：假門、祭台
    for z in range(PZ - 6, PZ + 7):
        a[x0 + 1, G + 1:G + 6, z] = B('chiseled_sandstone') if abs(z - PZ) <= 1 else B('smooth_sandstone')
    a[x0 + 1, G + 1:G + 5, PZ] = B('polished_blackstone')
    a[x0 + 3, G + 1, PZ - 1:PZ + 2] = W.slab('polished_granite_slab', True)
    for z in (PZ - 3, PZ + 3):
        a[x0 + 3, G + 1, z] = W.B('lantern')
    # 壁面浮雕
    for x in range(x0, x1 + 1, 4):
        for z in (z0, z1):
            a[x, G + 3:G + 6, z] = B('chiseled_sandstone')
    C.P['temple'] = (x0 + 10, 0, PZ)


def causeway(W, M, C):
    a = W.a; B = W.B
    x0, x1 = 296, W.size[0] - 1
    zc = PZ
    C.reserved[x0:x1 + 1, zc - 8:zc + 9] = True
    for x in range(x0, x1 + 1):
        for z in range(zc - 6, zc + 7):
            d = abs(z - zc)
            a[x, G, z] = M['pave']()
            if d >= 3:
                top = G + (5 if d <= 4 else 4 - (d - 5) * 2)
                a[x, G + 1:top + 1, z] = M['mastaba'](max(top - G, 0))
        for d in (3, -3):
            if x % 5 == 2:
                a[x, G + 2:G + 4, zc + d] = B('chiseled_sandstone')
        # 屋頂：中央留採光縫
        for z in (zc - 2, zc - 1, zc + 1, zc + 2):
            a[x, G + 5, z] = W.slab('smooth_sandstone_slab')
        a[x, G, zc - 1:zc + 2] = B('smooth_basalt')
    a[x0, G + 1:G + 5, zc - 2:zc + 3] = 0


def boat_pit(W, M, C, x0, z0, length, axis, width=5, depth=7):
    a = W.a
    for i in range(length):
        t = (i + 0.5) / length
        w = max(1, int(round(width * math.sin(math.pi * t) ** 0.6)))
        dep = max(2, int(round(depth * math.sin(math.pi * t) ** 0.5)))
        for j in range(-(w // 2), w - w // 2):
            x, z = (x0 + i, z0 + j) if axis == 'x' else (x0 + j, z0 + i)
            dj = abs(j + 0.5 - (w % 2) * 0.5) / max(w / 2, 1)
            dd = max(1, int(dep * (1 - 0.6 * dj * dj)))
            a[x, G - dd + 1:G + 1, z] = 0
            a[x, G - dd, z] = W.B('end_stone')
            C.reserved[x - 2:x + 3, z - 2:z + 3] = True


def south_pits(W, M, C):
    """南側兩個長方形船坑：蓋石封頂，坑內是拆解的雪松木船件。"""
    a = W.a; B = W.B
    cover = B('smooth_sandstone')
    for (x0, x1) in ((PX - 45, PX - 14), (PX + 6, PX + 37)):
        z0, z1 = 272, 274
        C.reserved[x0 - 3:x1 + 4, z0 - 3:z1 + 4] = True
        a[x0:x1 + 1, G - 4:G, z0:z1 + 1] = 0
        a[x0 - 1:x1 + 2, G - 5, z0 - 1:z1 + 2] = B('end_stone')
        a[x0 - 1:x1 + 2, G, z0 - 1:z1 + 2] = cover
        for x in range(x0 - 1, x1 + 2, 1):
            if x % 1 == 0 and (x - x0) % 2 == 0:
                a[x, G, z0 - 1:z1 + 2] = B('cut_sandstone')
        # 船件：龍骨、船殼板、槳
        for x in range(x0, x1 + 1):
            a[x, G - 4, z0 + 1] = W.log('stripped_spruce_log', 'x')
            if x % 3:
                a[x, G - 4, z0] = B('spruce_planks'); a[x, G - 4, z1] = B('dark_oak_planks')
            if x % 4 == 0:
                a[x, G - 3, z0:z1 + 1] = W.log('stripped_spruce_log', 'z')
            if x % 6 == 1:
                a[x, G - 3, z0 + 1] = W.slab('spruce_slab')
        a[x0 + 2, G - 3, z0 + 1] = W.B('lantern')
        a[x1 - 2, G - 3, z0 + 1] = W.B('lantern')
    C.P['boatpit'] = (PX + 20, -4, 273)


def mastaba(W, M, C, x0, z0, w, d, h=5):
    a = W.a; B = W.B
    C.reserved[x0 - 2:x0 + w + 2, z0 - 2:z0 + d + 2] = True
    a[x0 - 1:x0 + w + 1, G, z0 - 1:z0 + d + 1] = M['pave']((w + 2, d + 2))
    for k in range(h):
        ins = k // 2
        xa, xb, za, zb = x0 + ins, x0 + w - 1 - ins, z0 + ins, z0 + d - 1 - ins
        a[xa:xb + 1, G + 1 + k, za:zb + 1] = M['mastaba']((xb - xa + 1, zb - za + 1))
        if k % 2 == 1 and k < h - 1:
            for x in range(xa, xb + 1):
                a[x, G + 1 + k, za] = W.stairs('smooth_sandstone_stairs', 's')
                a[x, G + 1 + k, zb] = W.stairs('smooth_sandstone_stairs', 'n')
            for z in range(za + 1, zb):
                a[xa, G + 1 + k, z] = W.stairs('smooth_sandstone_stairs', 'e')
                a[xb, G + 1 + k, z] = W.stairs('smooth_sandstone_stairs', 'w')
    # 東側禮拜堂：假門＋供桌
    zc = z0 + d // 2
    xe = x0 + w - 1
    a[xe - 2:xe + 1, G + 1:G + 3, zc - 1:zc + 1] = 0
    a[xe - 3, G + 1:G + 4, zc - 1:zc + 1] = B('chiseled_sandstone')
    a[xe - 2, G + 1, zc - 1] = W.slab('smooth_sandstone_slab')
    a[xe - 3, G + 2, zc] = B('red_terracotta') if (x0 + z0) % 3 == 0 else B('chiseled_sandstone')
    # 墓井口
    a[x0 + w // 3, G + h, z0 + d // 3] = B('cut_sandstone')


def queens(W, M, C, VD, zone):
    specs = [('G1-a', 322, 196, 24, 30.4), ('G1-b', 322, 253, 24, 30.4), ('G1-c', 321, 308, 23, 29.5)]
    out = []
    for name, cx, cz, hw0, h in specs:
        C.reserved[cx - hw0 - 3:cx + hw0 + 4, cz - hw0 - 3:cz + hw0 + 4] = True
        W.a[cx - hw0 - 2:cx + hw0 + 3, G, cz - hw0 - 2:cz + hw0 + 3] = M['pave']((2 * hw0 + 5, 2 * hw0 + 5))
        pyramid(W, M, C, cx, cz, hw0, h, zone=zone)
        out.append((name, cx, cz, hw0, h))
        # 東側小禮拜堂
        x0 = cx + hw0 + 1
        a = W.a
        for x in range(x0, x0 + 9):
            for z in range(cz - 5, cz + 6):
                edge = x in (x0, x0 + 8) or z in (cz - 5, cz + 5)
                a[x, G, z] = W.B('smooth_basalt') if not edge else M['pave']()
                if edge:
                    a[x, G + 1:G + 5, z] = M['mastaba'](4)
                    a[x, G + 5, z] = W.slab('smooth_sandstone_slab')
        a[x0 + 8, G + 1:G + 4, cz - 1:cz + 2] = 0
        a[x0 + 1, G + 1:G + 4, cz] = W.B('chiseled_sandstone')
        a[x0 + 2, G + 1, cz] = W.slab('polished_granite_slab', True)
        C.reserved[x0:x0 + 10, cz - 6:cz + 7] = True
    return out


def queens_inside(W, M, C, VD, specs):
    """王后金字塔：北面入口下降通道→墓室（岩盤內）。"""
    fine = C.L['fine']; rock = C.L['rock']
    for name, cx, cz, hw0, h in specs:
        ze = cz - int(round(hw0 * (1 - 2 / h)))
        f = lambda z, ze=ze: 2 - (z - ze) // 2
        zend = ze + 2 * 9
        slope_z(VD, fine, cx, cx + 1, ze, zend, lambda z, f=f: max(f(z), -7), 3, 'smooth_sandstone_stairs')
        VD.box(rock, cx, -7, zend + 1, cx + 1, -5, cz)
        VD.box(rock, cx - 6, -7, cz - 2, cx + 1, -4, cz + 2)        # 墓室往西轉
        VD.put(cx - 5, -7, cz, ('solid', W.B('granite')))
        VD.put(cx - 5, -7, cz + 1, ('solid', W.B('granite')))
        C.P['queen_' + name] = (cx, 2, ze - 2)


def g1d(W, M, C, zone):
    cx, cz, hw0, h = 282, 282, 11, 13.8
    C.reserved[cx - 13:cx + 14, cz - 13:cz + 14] = True
    W.a[cx - 12:cx + 13, G, cz - 12:cz + 13] = M['pave']((25, 25))
    pyramid(W, M, C, cx, cz, hw0, h, zone=zone)


# ------------------------------------------------------------------ 主程式
def build():
    W = World()
    M = mats(W)
    C = Ctx(); C.P = {}
    zone = np.zeros(W.size, np.uint8)
    terrain(W, M, C)
    enclosure(W, M, C)
    temple(W, M, C)
    causeway(W, M, C)
    pyramid(W, M, C, PX, PZ, HW0, HGT, gold_top=True, zone=zone)
    VD = Voids(W)
    interior(W, M, C, VD)
    chevrons(W, M, C)
    specs = queens(W, M, C, VD, zone)
    queens_inside(W, M, C, VD, specs)
    g1d(W, M, C, zone)
    boat_pit(W, M, C, 278, 58, 46, 'z')
    boat_pit(W, M, C, 278, 176, 46, 'z')
    boat_pit(W, M, C, 300, 128, 46, 'x')
    south_pits(W, M, C)
    for i, z in enumerate(range(166, 372, 30)):
        mastaba(W, M, C, 358 + (i % 2), z, 11 + (i % 3), 22 + (i % 2) * 2, 5 + (i % 2))
        if z + 24 < 384:
            pass
    for row, z in enumerate((300, 328, 356)):
        for x in range(28, 250, 30):
            if x > 240: continue
            mastaba(W, M, C, x + (row % 2) * 6, z, 20 + (x // 30) % 3 * 2, 10 + row % 2 * 2, 5)
    apply_voids(W, M, C, VD, zone)
    C.nlights = lights(W, M, C, VD)
    dunes(W, M, C)
    C.VD = VD; C.zone = zone; C.specs = specs
    return W, C


if __name__ == '__main__':
    import time
    t = time.time()
    W, C = build()
    print('built', round(time.time() - t, 1), 's', W.stats(skip=('end_stone', 'sandstone', 'sand', 'cut_sandstone', 'smooth_sandstone')))
    print(C.P, C.nlights)
