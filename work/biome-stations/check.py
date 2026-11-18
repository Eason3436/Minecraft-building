"""逐件檢查：鐵軌、支承、淨空、重力方塊、吊燈、步行可達、動力軌分段。"""
from collections import deque
from gen import *

PASS_KEYS = ('rail', 'lever', 'lantern', 'carpet', 'snow_layer', 'petals', 'grass', 'fern', 'poppy', 'dandelion', 'daisy', 'bluet',
             'cornflower', 'orchid', 'allium', 'tulip', 'lily_of', 'mushroom', 'fungus', 'roots', 'eyeblossom', 'propagule', 'deadbush',
             'wildflowers', 'sapling', 'vine', 'hanging_moss', 'weeping', 'hanging_roots')
GRAVITY = ('sand', 'gravel', 'concrete_powder')


def passable(n):
    if n == 'air': return True
    if n == 'sea_lantern': return False
    if n.endswith('_block') or n.endswith('_stairs') or n.endswith('_slab'): return False
    if n in ('red_sand', 'sand', 'mushroom_stem', 'moss_block', 'pale_moss_block', 'mangrove_roots', 'muddy_mangrove_roots') or n.endswith('_path'): return False
    return any(k in n for k in PASS_KEYS)


def tall(n):
    return n.endswith('_wall') or 'fence' in n or n.endswith('_bars') or n.endswith('_pane')


def check_piece(pc):
    W = pc.W; a = W.a; N = W.names
    X, Y, Z = a.shape
    err = []
    nm = lambda x, y, z: N[a[x, y, z]] if 0 <= x < X and 0 <= y < Y and 0 <= z < Z else 'air'
    # 鐵軌
    for (x, z), h in pc.rails.items():
        n = nm(x, h, z)
        if n not in ('rail', 'golden_rail'): err.append(f'軌道被覆蓋 {(x, h, z)} {n}')
        b = nm(x, h - 1, z)
        if not (is_full(b) or b == 'redstone_block'): err.append(f'軌道下方不實 {(x, h - 1, z)} {b}')
        for yy in (h + 1, h + 2):
            if nm(x, yy, z) != 'air': err.append(f'軌道上方不空 {(x, yy, z)} {nm(x, yy, z)}')
        if x + 1 < X:
            h2 = pc.rails[(x + 1, z)]
            st = W.pal[a[x, h, z]][1]
            if h2 - h not in (0, 1): err.append(f'高差 {x} {h}->{h2}')
            if (h2 == h + 1) != (st.get('rail_direction') == 2): err.append(f'坡向錯 {(x, h, z)}')
    # 動力軌分段：拉桿段不可接到紅石塊段
    for z in ZR:
        run = []
        for x in range(X + 1):
            h = pc.rails.get((x, z))
            if h is not None and nm(x, h, z) == 'golden_rail':
                run.append(x); continue
            if run:
                lev = any(nm(rx, pc.rails[(rx, z)], zz) == 'lever' for rx in run for zz in (z - 1, z + 1))
                red = any(nm(rx, pc.rails[(rx, z)] - 1, z) == 'redstone_block' for rx in run)
                if lev and red: err.append(f'拉桿段接到常時供電 z{z} x{run}')
                run = []
    # 支撐
    for x in range(X):
        for y in range(1, Y):
            for z in range(Z):
                n = N[a[x, y, z]]
                if n == 'air' or n == 'water': continue
                below = nm(x, y - 1, z); above = nm(x, y + 1, z)
                if n in GRAVITY or n.endswith('_sand'):
                    if below in ('air', 'water'): err.append(f'重力方塊懸空 {(x, y, z)} {n}')
                if n in ('lantern', 'soul_lantern'):
                    hang = W.pal[a[x, y, z]][1]['hanging']
                    if hang and above == 'air': err.append(f'吊燈上方空 {(x, y, z)}')
                    if not hang and below == 'air': err.append(f'燈下方空 {(x, y, z)}')
                if passable(n) and not n.endswith('rail') and n not in ('lever',) and not any(k in n for k in ('vine', 'hanging', 'weeping', 'propagule', 'lantern')):
                    if below in ('air',): err.append(f'植物懸空 {(x, y, z)} {n}')
    # 步行
    if pc.walk:
        s, t = pc.walk
        ok = bfs(pc, s, t)
        if not ok: err.append(f'步行不可達 {s}->{t}')
    return err


def bfs(pc, s, t):
    W = pc.W; a = W.a; N = W.names
    X, Y, Z = a.shape
    nm = lambda x, y, z: N[a[x, y, z]] if 0 <= x < X and 0 <= y < Y and 0 <= z < Z else 'void'
    def stand(x, y, z):
        if not (0 <= x < X and 0 <= z < Z and 1 <= y < Y - 1): return False
        f, hd, b = nm(x, y, z), nm(x, y + 1, z), nm(x, y - 1, z)
        if 'rail' in f: return False
        return passable(f) and passable(hd) and not passable(b) and not tall(b) and b != 'water'
    if not stand(*s): return False
    seen = {s}; q = deque([s])
    while q:
        x, y, z = q.popleft()
        if abs(x - t[0]) + abs(z - t[2]) <= 1 and abs(y - t[1]) <= 1: return True
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (0, 1, -1):
                n = (x + dx, y + dy, z + dz)
                if n in seen: continue
                if dy == 1 and not passable(nm(x, y + 2, z)): continue
                if dy == -1 and not passable(nm(x + dx, y + 1, z + dz)): continue
                if stand(*n):
                    seen.add(n); q.append(n)
    return False


if __name__ == '__main__':
    import sys
    tot = 0
    for b in BIOMES:
        for k in KINDS:
            pc = build_piece(b, k)
            e = check_piece(pc)
            tot += len(e)
            if e: print(b['id'], k, len(e), e[:6])
    print('errors', tot)
