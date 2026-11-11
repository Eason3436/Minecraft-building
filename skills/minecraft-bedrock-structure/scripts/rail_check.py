"""可搭乘鐵路的走查工具。與建模方式無關：只需要一個 get(x, y, z) -> (name, states) 的存取函式，
name 不含 minecraft: 前綴，states 是 dict；越界回 ('air', {})。

    from rail_check import walk_loop, walk_path, spacing_report, simulate
    track = walk_loop(get, start=(78, 30, 197))
    print(spacing_report(track, max_gap=10))

說明見 references/railway.md。"""

DIRS = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}
OPP = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
CON = {0: 'ns', 1: 'ew', 2: 'ew', 3: 'ew', 4: 'ns', 5: 'ns', 6: 'se', 7: 'sw', 8: 'nw', 9: 'ne'}
ASC = {2: 'e', 3: 'w', 4: 'n', 5: 's'}          # 傾斜軌往哪一側上升
RAILS = ('rail', 'golden_rail', 'detector_rail', 'activator_rail')
NO_SUPPORT = ('air', 'water', 'flowing_water', 'lava')


def _rail(get, x, y, z):
    name, st = get(x, y, z)
    return (st['rail_direction'], name, st) if name in RAILS else None


def _powered(get, x, y, z, st, reach=3):
    """動力軌的電源：正下方紅石塊、或 reach 格內相連的動力軌下方有紅石塊、或緊鄰拉桿／紅石火把。"""
    if get(x, y - 1, z)[0] == 'redstone_block':
        return True
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in (0, 1):
                if get(x + dx, y + dy, z + dz)[0] in ('lever', 'redstone_torch', 'redstone_block'):
                    return True
    for d in CON[st['rail_direction']]:
        cx, cy, cz = x, y, z
        for _ in range(reach):
            dx, dz = DIRS[d]
            nxt = None
            for dy in (0, 1, -1):
                r = _rail(get, cx + dx, cy + dy, cz + dz)
                if r and r[1] == 'golden_rail':
                    nxt = (cx + dx, cy + dy, cz + dz)
                    break
            if not nxt:
                break
            cx, cy, cz = nxt
            if get(cx, cy - 1, cz)[0] == 'redstone_block':
                return True
    return False


def _neighbours(get, x, y, z, r):
    out = []
    for d in CON[r[0]]:
        dx, dz = DIRS[d]
        q = None
        for dy in ((1, 0) if ASC.get(r[0]) == d else (0, -1)):
            rr = _rail(get, x + dx, y + dy, z + dz)
            if not rr:
                continue
            if dy == -1 and ASC.get(rr[0]) != OPP[d]:
                continue
            if OPP[d] in CON[rr[0]]:
                q = (x + dx, y + dy, z + dz)
                break
        out.append((d, q))
    return out


def _check_cell(get, x, y, z, r, clearance):
    for dy in range(1, clearance + 1):
        nm = get(x, y + dy, z)[0]
        assert nm == 'air', f'({x},{y + dy},{z}) 淨空被 {nm} 佔用'
    below = get(x, y - 1, z)[0]
    assert below not in NO_SUPPORT, f'({x},{y},{z}) 鐵軌下方是 {below}'
    if below in ('gravel', 'sand', 'red_sand'):
        assert get(x, y - 2, z)[0] not in NO_SUPPORT, f'({x},{y - 1},{z}) 道砟下方懸空，載入後會掉落'
    pw = False
    if r[1] == 'golden_rail':
        assert r[2].get('rail_data_bit') is True, f'({x},{y},{z}) 動力軌 rail_data_bit 不是 True'
        assert _powered(get, x, y, z, r[2]), f'({x},{y},{z}) 動力軌附近沒有電源'
        pw = True
    return dict(pos=(x, y, z), powered=pw, slope=r[0] in ASC, curve=r[0] >= 6)


def walk_loop(get, start, clearance=2, limit=20000):
    """閉合環線。start=(x,y,z) 是任一格鐵軌。回傳依行進順序的格子清單。"""
    x, y, z = start
    prev = None
    out = []
    while True:
        r = _rail(get, x, y, z)
        assert r, f'({x},{y},{z}) 沒有鐵軌'
        out.append(_check_cell(get, x, y, z, r, clearance))
        nb = _neighbours(get, x, y, z, r)
        for d, q in nb:
            assert q, f'({x},{y},{z}) 往 {d} 斷軌'
        qs = [q for _, q in nb]
        q = qs[0] if qs[1] == prev else qs[1] if qs[0] == prev else qs[0]
        prev = (x, y, z)
        x, y, z = q
        if (x, y, z) == tuple(start):
            return out
        assert len(out) < limit, '走不回起點'


def walk_path(get, start, clearance=2, limit=20000):
    """兩端有擋塊的往返線。start 是其中一個端點（只接一個方向的那格）。"""
    x, y, z = start
    prev = None
    out = []
    while True:
        r = _rail(get, x, y, z)
        assert r, f'({x},{y},{z}) 沒有鐵軌'
        out.append(_check_cell(get, x, y, z, r, clearance))
        qs = [q for _, q in _neighbours(get, x, y, z, r) if q and q != prev]
        if prev is None:
            assert len(qs) == 1, f'({x},{y},{z}) 不是端點（接了 {len(qs)} 個方向）'
        if not qs:
            break
        prev = (x, y, z)
        x, y, z = qs[0]
        assert len(out) < limit
    for end in (out[0], out[-1]):                    # 端點要頂著實心方塊才會自動折返
        ex, ey, ez = end['pos']
        end['buffer'] = any(get(ex + dx, ey, ez + dz)[0] not in ('air',) + RAILS for dx, dz in DIRS.values())
    return out


def spacing_report(track, max_gap=10, closed=True):
    """最長連續無動力格數等指標。客運線 max_gap 建議 10 以內（含之字斜線），貨運線 4 以內。"""
    seq = track + track if closed else track
    gap = worst = 0
    where = None
    for c in seq:
        if c['powered']:
            gap = 0
        else:
            gap += 1
            if gap > worst:
                worst, where = gap, c['pos']
    slopes = [c for c in track if c['slope']]
    rep = dict(length=len(track), powered=sum(c['powered'] for c in track),
               powered_ratio=round(sum(c['powered'] for c in track) / len(track), 3),
               max_unpowered_run=worst, worst_at=where,
               slopes=len(slopes), unpowered_slopes=[c['pos'] for c in slopes if not c['powered']],
               ok=worst <= max_gap and all(c['powered'] for c in slopes))
    return rep


def simulate(track, reverse=False, v0=0.1, laps=2, friction=0.985, boost=0.04, vmax=0.4, closed=True):
    """粗略速度模擬，只用來抓「會不會停在半路」。常數刻意保守（比載人礦車的實際阻力大），
    通過不代表能高速行駛；高速與否看 spacing_report 與遊戲實測。回傳 (最低速度, 位置)。"""
    tr = track[::-1] if reverse else track
    n = len(tr)
    v, pos, vmin = v0, 0.0, (9.0, None)
    total = n * laps if closed else n - 1
    while pos < total:
        i = int(pos) % n
        c = tr[i]
        y = c['pos'][1]
        ynext = tr[(i + 1) % n]['pos'][1] if (closed or i + 1 < n) else y
        if c['powered']:
            v = min(vmax, v + boost)
        else:
            v *= friction
        if ynext > y:
            v -= 0.02
        elif ynext < y:
            v = min(vmax, v + 0.02)
        if v <= 0.01:
            return (0.0, c['pos'])
        if pos >= min(n, total) / 4 and v < vmin[0]:
            vmin = (v, c['pos'])
        pos += v
    return (round(vmin[0], 3), vmin[1])
