"""環狀雙軌鐵路 v2：順地形彎折的不規則環線，含爬坡、高架、路塹與地下段。
走廊整地、拱橋、隧道、沿線裝飾、鋪軌、閉合驗證與礦車動能模擬。"""
import numpy as np
from collections import deque
from core import *
from terrain import *

N8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

# A 圈（內軌）折點：逆時針（南段往東→東段往北→北段往西→西段往南）。相鄰折點只差 45°。
WP = [(78, 197), (180, 197), (224, 153), (224, 96), (204, 76), (204, 50), (184, 30), (70, 30), (40, 60), (40, 159)]
SEG_NAME = ['南・海堤高架', '東南斜線', '東・爬坡高架', '東城跨線', '東北直線', '東北斜線', '北・地下段', '西北斜線', '西・溺谷高橋', '西南斜線']


def level_at(seg, x, z):
    """軌面高度：南 30 → 東段爬到 38 → 北地下段降到 34 → 西段降回 30。坡道只放在直線上，每 3 格升 1。"""
    if seg in (0, 1, 9): return 30
    if seg == 2: return 30 + int(np.clip((148 - z + 2) // 3, 0, 8))
    if seg in (3, 4, 5): return 38
    if seg == 6: return 38 - int(np.clip((182 - x + 2) // 3, 0, 4))
    if seg == 7: return 34
    return 34 - int(np.clip((z - 132 + 2) // 3, 0, 4))


def _dil(m):
    n = m.copy()
    n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
    n[1:, 1:] |= m[:-1, :-1]; n[:-1, :-1] |= m[1:, 1:]; n[1:, :-1] |= m[:-1, 1:]; n[:-1, 1:] |= m[1:, :-1]
    return n


def route(jog_every=11, jog=3):
    """折點之間：直線照走；斜線用之字線，每隔 jog_every 步插入一小段 3 格直線（放動力軌補速），
    x 向與 z 向輪流插，整體仍維持 45°。"""
    cells = []; seg = []
    n = len(WP)
    for i in range(n):
        (x, z), (x1, z1) = WP[i], WP[(i + 1) % n]
        sx, sz = int(np.sign(x1 - x)), int(np.sign(z1 - z))
        assert sx == 0 or sz == 0 or abs(x1 - x) == abs(z1 - z), (WP[i], WP[(i + 1) % n])
        if not (sx and sz):
            while (x, z) != (x1, z1):
                cells.append((x, z)); seg.append(i); x += sx; z += sz
            continue
        run = 0; turn = 0
        while (x, z) != (x1, z1):
            rx, rz = abs(x1 - x), abs(z1 - z)
            if rx == 0 or rz == 0:               # 只剩單軸：直走到底
                cells.append((x, z)); seg.append(i); x += sx if rx else 0; z += sz if rz else 0
                continue
            if run >= jog_every and min(rx, rz) > jog + 4 + (jog if turn % 2 == 0 else 0):
                for _ in range(jog):
                    cells.append((x, z)); seg.append(i)
                    if turn % 2 == 0: x += sx
                    else: z += sz
                turn += 1; run = 0
                continue
            cells.append((x, z)); seg.append(i); x += sx
            cells.append((x, z)); seg.append(i); z += sz
            run += 1
    assert len(set(cells)) == len(cells)
    return cells, seg


def order_ring(mask, start):
    path = [start]; prev = None; cur = start
    while True:
        nb = [(cur[0] + dx, cur[1] + dz) for dx, dz in DIRS.values() if mask[cur[0] + dx, cur[1] + dz]]
        assert len(nb) == 2, (cur, nb)
        nxt = nb[0] if nb[1] == prev else nb[1] if nb[0] == prev else nb[0]
        if nxt == start: break
        path.append(nxt); prev, cur = cur, nxt
        assert len(path) < 5000
    return path


def prepare(T):
    cellsA, segA = route()
    A = np.zeros((SX, SZ), bool)
    for x, z in cellsA: A[x, z] = True
    # 內部區域（洪水填充外部）
    out = np.zeros((SX, SZ), bool); dq = deque([(0, 0)]); out[0, 0] = True
    while dq:
        x, z = dq.popleft()
        for dx, dz in DIRS.values():
            nx, nz = x + dx, z + dz
            if 0 <= nx < SX and 0 <= nz < SZ and not out[nx, nz] and not A[nx, nz]:
                out[nx, nz] = True; dq.append((nx, nz))
    R = ~out
    D1 = _dil(R); D2 = _dil(D1); D3 = _dil(D2)
    Bm = D2 & ~D1
    mid = D1 & ~R
    edge = (D3 & ~D2) | (R & ~A & _dil(A))
    rail = A | Bm
    cor = rail | mid | edge
    cor2 = _dil(cor)
    # B 圈排序：方向與 A 相同
    bx, bz = np.nonzero(Bm)
    start = (int(bx[0]), int(bz[0]))
    cellsB = order_ring(Bm, start)
    # 沿線標號：最近的 A 格（直線段上就是正側方那一格）
    an = np.array(cellsA)
    lab = np.full((SX, SZ), -1, int); ldist = np.full((SX, SZ), 99.0)
    reach = cor2.copy()
    for _ in range(6): reach = _dil(reach)
    xs, zs = np.nonzero(reach)
    for k in range(0, len(xs), 4000):
        px = xs[k:k + 4000]; pz = zs[k:k + 4000]
        d2 = (px[:, None] - an[None, :, 0]) ** 2 + (pz[:, None] - an[None, :, 1]) ** 2
        j = d2.argmin(1)
        lab[px, pz] = j; ldist[px, pz] = np.sqrt(d2[np.arange(len(px)), j])
    n = len(cellsA)
    yA = np.array([level_at(segA[i], *cellsA[i]) for i in range(n)])
    straight = np.zeros(n, bool); axis = [''] * n
    for i in range(n):
        xs_ = {cellsA[(i + k) % n][0] for k in range(-3, 4)}; zs_ = {cellsA[(i + k) % n][1] for k in range(-3, 4)}
        if len(xs_) == 1: straight[i] = True; axis[i] = 'z'
        elif len(zs_) == 1: straight[i] = True; axis[i] = 'x'
    # B 圈方向對齊 A（比較第一段的標號走向）
    la = [lab[c] for c in cellsB[:40]]
    fwd = sum(1 for a_, b_ in zip(la, la[1:]) if (b_ - a_) % n < n // 2 and b_ != a_)
    bwd = sum(1 for a_, b_ in zip(la, la[1:]) if (a_ - b_) % n < n // 2 and b_ != a_)
    if bwd > fwd: cellsB = cellsB[::-1]
    ry = np.zeros((SX, SZ), int)
    m = lab >= 0
    ry[m] = yA[lab[m]]
    h = T['h']; ho = h.copy()
    tun_i = np.array([ho[x, z] >= yA[i] + 7 for i, (x, z) in enumerate(cellsA)])
    for _ in range(4):                      # 去掉太短的片段
        for i in range(n):
            if tun_i[i - 1] == tun_i[(i + 1) % n] != tun_i[i]: tun_i[i] = tun_i[i - 1]
    for i in range(n):                      # 連續不足 10 格的隧道改成路塹
        if tun_i[i] and not tun_i[i - 1]:
            j = i
            while tun_i[j % n]: j += 1
            if j - i < 10:
                for k in range(i, j): tun_i[k % n] = False
    tunnel = np.zeros((SX, SZ), bool); tunnel[cor] = tun_i[lab[cor]]
    tunnel2 = np.zeros((SX, SZ), bool); tunnel2[cor2] = tun_i[lab[cor2]]
    sel = cor & ~tunnel
    h[sel] = ry[sel] - 1
    sel = cor & tunnel
    h[sel] = np.maximum(h[sel], ry[sel] + 8)
    sel = cor2 & tunnel2 & ~cor
    h[sel] = np.maximum(h[sel], ry[sel] + 7)
    sel = cor2 & ~cor & ~tunnel2 & (h > ry + 5)   # 路塹邊坡不超過 6 高，再往外自然接坡
    h[sel] = ry[sel] + 5
    inside = R & ~cor2
    T.update(A=A, Bm=Bm, rail=rail, mid=mid, edge=edge, cor=cor, cor2=cor2, lab=lab, ldist=ldist, straight=straight, axis=axis,
             ho=ho, tunnel=tunnel, tunnel2=tunnel2, tun_i=tun_i, ry=ry, yA=yA, cellsA=cellsA, cellsB=cellsB, segA=segA, inside=inside)
    T['town'] = T['town'] & inside
    T['farm'] = T['farm'] & inside


def rail_dir(p, c, n_):
    con = set()
    for q in (p, n_):
        d = (q[0] - c[0], q[1] - c[1])
        con.add({(0, -1): 'n', (0, 1): 's', (1, 0): 'e', (-1, 0): 'w'}[d])
    return {frozenset('ns'): 0, frozenset('ew'): 1, frozenset('se'): 6, frozenset('sw'): 7, frozenset('nw'): 8, frozenset('ne'): 9}[frozenset(con)]


ASC = {'e': 2, 'w': 3, 'n': 4, 's': 5}


def build(W, T):
    B = W.B; a = W.a
    ho = T['ho']; cor = T['cor']; lab = T['lab']; straight = T['straight']; axis = T['axis']; ry = T['ry']; h = T['h']
    sb, msb, csb, cob, andes, pand = B('stone_bricks'), B('mossy_stone_bricks'), B('cracked_stone_bricks'), B('cobblestone'), B('andesite'), B('polished_andesite')
    gravel, water, air = B('gravel'), B('water'), 0
    masonry = W.mix((sb, 66), (msb, 12), (csb, 10), (cob, 7), (andes, 5))
    ballast = W.mix((gravel, 60), (cob, 22), (andes, 18))
    wall = B('stone_brick_wall'); fence = B('spruce_fence')
    sea = T['sea']
    n = len(T['cellsA'])
    viaduct = np.zeros((SX, SZ), bool)
    xs, zs = np.nonzero(cor & ~T['tunnel'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        i = lab[x, z]; BY = int(ry[x, z]) - 1
        g = int(ho[x, z])
        if g < BY:
            for y in range(max(g - 1, 1), BY - 1): a[x, y, z] = masonry()
            a[x, BY - 2, z] = sb; a[x, BY - 1, z] = pand if T['edge'][x, z] else sb
            if BY - g >= 6:                      # 拱洞（8 格一跨：2 格橋墩＋6 格拱）
                c = i % 8
                if c >= 2:
                    k = c - 2
                    top = BY - (5, 4, 3, 3, 4, 5)[k]
                    for y in range(g + 1, top + 1):
                        a[x, y, z] = water if (sea[x, z] and y <= SEA) else air
                    viaduct[x, z] = True
                    if straight[i] and k in (0, 1, 4, 5):
                        # 標號沿 A 圈遞增的方向
                        p0, p1 = T['cellsA'][i], T['cellsA'][(i + 1) % n]
                        fd = {(1, 0): 'e', (-1, 0): 'w', (0, 1): 's', (0, -1): 'n'}[(p1[0] - p0[0], p1[1] - p0[1])]
                        d = OPP[fd] if k < 3 else fd
                        a[x, top + 1, z] = W.stairs('stone_brick_stairs', d, True)
        a[x, BY, z] = ballast()
        if a[x, BY - 1, z] == 0 or W.names[a[x, BY - 1, z]] in ('water', 'sand', 'gravel'): a[x, BY - 1, z] = sb
        a[x, BY + 1:BY + 8, z] = 0
    T['viaduct'] = viaduct
    # 路塹邊坡砌石
    xs, zs = np.nonzero(T['cor2'] & ~cor & ~T['tunnel2'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        BY = int(ry[x, z]) - 1
        if h[x, z] > BY:
            for y in range(BY, int(h[x, z]) + 1): a[x, y, z] = masonry()
    # ---- 沿線裝飾：護欄、燈柱、樹籬、圍籬 ----
    hedge = [B('azalea_leaves'), B('azalea_leaves_flowered'), B('oak_leaves')]
    xs, zs = np.nonzero(T['edge'] & ~T['tunnel'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        i = lab[x, z]; BY = int(ry[x, z]) - 1
        nb = [(x + dx, z + dz) for dx, dz in N8 if 0 <= x + dx < SX and 0 <= z + dz < SZ and not cor[x + dx, z + dz]]
        if not nb: continue
        lo = min(int(h[p]) for p in nb)
        if lo < BY - 1:                           # 高架／路堤：石護欄＋燈柱
            a[x, BY, z] = pand; a[x, BY + 1, z] = wall
            if i % 12 == 6: a[x, BY + 1, z] = sb; a[x, BY + 2, z] = wall; a[x, BY + 3, z] = W.lantern()
        elif lo <= BY:                            # 平地：樹籬與圍籬交錯
            a[x, BY, z] = B('grass_block') if (i // 4) % 2 == 0 else a[x, BY, z]
            a[x, BY + 1, z] = hedge[i % 3] if (i // 4) % 2 == 0 else fence
    # ---- 門型架（雙軌上方橫樑＋吊燈），每 12 格一座，只放在直線、非坡道、非隧道 ----
    cellsA = T['cellsA']; yA = T['yA']
    gantries = 0
    for i in range(n):
        if not straight[i] or T['tun_i'][i] or i % 9 != 0: continue
        if len({yA[(i + k) % n] for k in (-2, -1, 0, 1, 2)}) != 1: continue
        x, z = cellsA[i]
        if T['segA'][i] == 0 and 98 <= x <= 148: continue     # 總站範圍另有雨棚
        px, pz = (0, 1) if axis[i] == 'x' else (1, 0)
        # 找出往外的方向（mid 在外側）
        s = 1 if T['mid'][x + px, z + pz] else -1
        px *= s; pz *= s
        y = int(yA[i])
        post = B('dark_oak_fence')
        for k in (-1, 3):
            cx, cz = x + px * k, z + pz * k
            if not T['edge'][cx, cz]: break
            for yy in range(y, y + 4): a[cx, yy, cz] = post
            if W.names[a[cx, y - 1, cz]] in ('air', 'gravel', 'grass_block'): a[cx, y - 1, cz] = sb
        else:
            for k in range(-1, 4): a[x + px * k, y + 4, z + pz * k] = W.slab('dark_oak_slab') if k not in (-1, 3) else B('dark_oak_planks')
            a[x + px, y + 3, z + pz] = W.lantern(True)
            gantries += 1
    # ---- 隧道：襯砌、木框、吊燈 ----
    lamp = W.lantern(True)
    dlog = lambda ax: W.log('dark_oak_log', ax)
    xs, zs = np.nonzero(T['cor2'] & T['tunnel2'])
    for x, z in zip(xs.tolist(), zs.tolist()):
        i = lab[x, z]; BY = int(ry[x, z]) - 1
        if cor[x, z]:
            a[x, BY, z] = ballast()
            a[x, BY + 1:BY + 6, z] = 0
            a[x, BY + 6, z] = masonry()
            rib = i % 6 == 0
            if T['edge'][x, z]:
                a[x, BY + 5, z] = masonry()
                if rib:
                    for y in range(BY + 1, BY + 5): a[x, y, z] = dlog('y')
                elif i % 6 == 3 and straight[i]:
                    a[x, BY + 3, z] = W.lantern() if False else a[x, BY + 3, z]
            elif rib and straight[i]:
                a[x, BY + 5, z] = dlog('z' if axis[i] == 'x' else 'x')
            elif T['mid'][x, z] and i % 6 == 3:
                a[x, BY + 5, z] = lamp
        else:
            for y in range(BY, BY + 7):
                if a[x, y, z] != 0: a[x, y, z] = masonry()
    # 洞門
    tun = T['tun_i']
    T['portals'] = []
    for i in range(n):
        if tun[i] and (not tun[i - 1] or not tun[(i + 1) % n]):
            T['portals'].append(cellsA[i])
            xs, zs = np.nonzero((lab == i) & (T['ldist'] <= 6.5))
            for x, z in zip(xs.tolist(), zs.tolist()):
                BY = int(ry[x, z]) - 1
                if cor[x, z]:
                    for y in range(BY + 6, BY + 10): a[x, y, z] = masonry()
                    a[x, BY + 10, z] = W.slab('stone_brick_slab')
                    if T['edge'][x, z]: a[x, BY + 5, z] = masonry()
                else:
                    top = BY + 9 if T['cor2'][x, z] else BY + 7
                    for y in range(BY, top + 1): a[x, y, z] = masonry()
                    a[x, top + 1, z] = W.slab('stone_brick_slab')
    # ---- 鋪軌 ----
    red = B('redstone_block')
    info = {'gantries': gantries}
    for name, loop in (('A', T['cellsA']), ('B', T['cellsB'])):
        m = len(loop)
        ys = [int(ry[c]) for c in loop]
        dirs = [rail_dir(loop[i - 1], loop[i], loop[(i + 1) % m]) for i in range(m)]
        powered = 0; run = 0; slopes = 0
        for i, (x, z) in enumerate(loop):
            y = ys[i]; d = dirs[i]
            up_next = ys[(i + 1) % m] > y; up_prev = ys[i - 1] > y
            assert abs(ys[(i + 1) % m] - y) <= 1 and not (up_next and up_prev), (name, i, x, z)
            if up_next or up_prev:
                assert d in (0, 1), ('坡道必須在直線上', name, x, z)
                q = loop[(i + 1) % m] if up_next else loop[i - 1]
                dd = {(1, 0): 'e', (-1, 0): 'w', (0, 1): 's', (0, -1): 'n'}[(q[0] - x, q[1] - z)]
                a[x, y, z] = B('golden_rail', rail_direction=ASC[dd], rail_data_bit=True)
                a[x, y - 1, z] = red; powered += 1; slopes += 1; run = 0
                continue
            st = d in (0, 1)
            near_ramp = any(ys[(i + k) % m] != y for k in range(-4, 5))
            edge_of_diag = st and (dirs[(i + 1) % m] not in (0, 1) or dirs[i - 1] not in (0, 1) or dirs[(i + 2) % m] not in (0, 1) or dirs[i - 2] not in (0, 1))
            run = run + 1 if st else 0
            if st and (near_ramp or edge_of_diag or run % 10 in (4, 5)):
                a[x, y, z] = B('golden_rail', rail_direction=d, rail_data_bit=True)
                a[x, y - 1, z] = red; powered += 1
            else:
                a[x, y, z] = B('rail', rail_direction=d)
            if a[x, y - 2, z] == 0: a[x, y - 2, z] = sb
        info[name] = dict(length=m, powered=powered, slopes=slopes, levels=(min(ys), max(ys)))
    return info


CON = {0: 'ns', 1: 'ew', 2: 'ew', 3: 'ew', 4: 'ns', 5: 'ns', 6: 'se', 7: 'sw', 8: 'nw', 9: 'ne'}
ASCDIR = {2: 'e', 3: 'w', 4: 'n', 5: 's'}


def _rail(W, x, y, z):
    k = W.get(x, y, z); nm = W.names[k]
    if nm not in ('rail', 'golden_rail'): return None
    return W.pal[k][1]['rail_direction'], nm, W.pal[k][1].get('rail_data_bit', False)


def verify(W, start, y0, expect_len=None):
    """沿鐵軌 3D 走一圈：相接、淨空、支承、供電。回傳依行進順序的 [(x,y,z,powered,slope)]。"""
    x, z = start; y = y0
    prev = None; out = []
    while True:
        r = _rail(W, x, y, z); assert r, f'({x},{y},{z}) 沒有鐵軌'
        for dy in (1, 2):
            assert W.get(x, y + dy, z) == 0, f'({x},{y + dy},{z}) 淨空被 {W.names[W.get(x, y + dy, z)]} 佔用'
        below = W.names[W.get(x, y - 1, z)]
        assert below not in ('air', 'water'), f'({x},{y},{z}) 鐵軌下方是 {below}'
        assert W.names[W.get(x, y - 2, z)] not in ('air', 'water'), f'({x},{y - 2},{z}) 道床懸空'
        pw = False
        if r[1] == 'golden_rail':
            if below != 'redstone_block':
                near = [W.names[W.get(x + dx, y + 1, z + dz)] for dx in (-1, 0, 1) for dz in (-1, 1)]
                assert 'lever' in near, f'({x},{y},{z}) 動力軌沒有紅石塊也沒有拉桿'
            assert r[2] is True
            pw = True
        nxt = []
        for d in CON[r[0]]:
            dx, dz = DIRS[d]; q = None
            for dy in ((1, 0) if ASCDIR.get(r[0]) == d else (0, -1)):
                rr = _rail(W, x + dx, y + dy, z + dz)
                if not rr: continue
                if dy == -1 and ASCDIR.get(rr[0]) != OPP[d]: continue
                if OPP[d] in CON[rr[0]]: q = (x + dx, y + dy, z + dz); break
            assert q, f'({x},{y},{z}) 往 {d} 斷軌'
            nxt.append(q)
        out.append((x, y, z, pw, r[0] in ASCDIR))
        q = nxt[0] if nxt[1] == prev else nxt[1] if nxt[0] == prev else nxt[0]
        prev = (x, y, z); x, y, z = q
        if (x, z) == start: break
        assert len(out) < 5000
    if expect_len: assert len(out) == expect_len, (len(out), expect_len)
    return out


def simulate(track, reverse=False, v0=0.4, laps=3, start=0):
    """載人礦車動能近似模擬（每 tick）：動力軌 +0.06（上限 0.4 格/tick＝8 m/s）、
    一般軌 ×0.997、坡道每 tick ±0.0078。回傳 (最低速度, 發生位置, 一圈秒數)。"""
    tr = track[::-1] if reverse else track
    n = len(tr)
    v = v0; pos = float(start); vmin = (9, None); ticks = 0; lap_ticks = None
    while pos < n * laps:
        i = int(pos) % n
        x, y, z, pw, sl = tr[i]
        ynext = tr[(i + 1) % n][1]; yprev = tr[i - 1][1]
        if pw: v = min(0.4, v + 0.06)
        else: v *= 0.997
        if ynext > y or (sl and yprev < y and ynext >= y): v -= 0.0078125
        elif ynext < y or (sl and yprev > y): v = min(0.4, v + 0.0078125)
        if v <= 0.005: return (0.0, (x, y, z), None)
        pos += v; ticks += 1
        if pos >= n and lap_ticks is None: lap_ticks = ticks
        if pos >= n and v < vmin[0]: vmin = (v, (x, y, z))
    return (round(vmin[0], 3), vmin[1], round(lap_ticks / 20.0, 1))
