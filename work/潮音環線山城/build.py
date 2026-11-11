import sys, time, random
from core import *
from terrain import *
import rail, town, landmarks as LM, nature as NA, render as R


def layout(W, T):
    rng = random.Random(77)
    for k in ('reserved', 'street', 'parapet'):
        T[k] = np.zeros((SX, SZ), bool)
    h = T['h']
    # 地標預留
    T['reserved'][104:143, 90:113] = True          # 教堂廣場
    T['reserved'][100:146, 186:196] = True         # 總站
    T['reserved'][86:104, 183:195] = True          # 市場
    T['reserved'][210:221, 105:150] = True         # 機務段
    # 石階
    S = T['stairs'] = {}
    S['main'] = town.stair_path(W, T, town.until_top(T, 119, 176, 'n'), 'n', 3)
    S['funi'] = town.stair_path(W, T, town.until_top(T, 125, 176, 'n'), 'n', 1, rail=True)
    S['w'] = town.stair_path(W, T, town.until_top(T, 84, 174, 'n'), 'n', 2)
    S['e'] = town.stair_path(W, T, town.until_top(T, 158, 174, 'n'), 'n', 2)
    S['e1'] = town.stair_path(W, T, town.until_top(T, 200, 80, 'w', top=96), 'w', 2)
    S['e2'] = town.stair_path(W, T, town.until_top(T, 204, 126, 'w'), 'w', 2)
    S['sw'] = town.stair_path(W, T, town.until_top(T, 60, 150, 'e', top=46), 'e', 2)
    town.terrace_streets(W, T)
    # 下城街道
    town.pave_rect(W, T, 62, 178, 196, 180, level=22)
    for x in (84, 158, 180):
        town.pave_rect(W, T, x, 172, x + 1, 203, level=22)
    town.pave_rect(W, T, 116, 170, 127, 187, level=22)       # 站前廣場軸線
    town.pave_rect(W, T, 100, 181, 145, 187, level=22)
    town.pave_rect(W, T, 86, 181, 104, 195, level=22)        # 市場廣場
    # 東城街道（南北向）＋ 接往下城的斜坡
    town.pave_rect(W, T, 206, 84, 207, 172, level=28)
    LM.main_station(W, T); LM.funicular(W, T); LM.church_plaza(W, T); LM.market(W, T)
    LM.harbor(W, T); LM.lighthouse(W, T); LM.summit(W, T); LM.depot(W, T); LM.underground_station(W, T)
    print('windmill', LM.windmill(W, T))
    houses = []
    for L in town.LEVELS:
        for (x0, z0, fw, fd, d) in town.find_lots(T, L, rng, tol=0, gap_p=0.2):
            if x0 < 70 and z0 < 112: continue          # 西北角孤立台地不蓋屋
            low = L == 22
            floors = rng.choice([3, 3, 4]) if low else rng.choice([2, 2, 3, 3]) if L < 52 else rng.choice([2, 2, 3])
            if x0 > 196: floors = 2
            houses.append(town.house(W, T, x0, z0, fw, fd, d, L, floors, rng, shop=low and rng.random() < 0.6))
    for L in town.LEVELS:           # 第二輪：補小屋
        for (x0, z0, fw, fd, d) in town.find_lots(T, L, rng, wide=(5, 6), deep=(5,), gap_p=0.2, need=0.5):
            if x0 < 70 and z0 < 112: continue
            houses.append(town.house(W, T, x0, z0, fw, fd, d, L, rng.choice([2, 2, 3]) if L > 22 else 3, rng))
    for L in town.LEVELS:           # 第三輪：臨街面較窄的畸零地
        for (x0, z0, fw, fd, d) in town.find_lots(T, L, rng, wide=(7, 6, 5), deep=(6, 5), gap_p=0.1, need=0.34):
            if x0 < 70 and z0 < 112: continue
            houses.append(town.house(W, T, x0, z0, fw, fd, d, L, rng.choice([2, 3]), rng))
    T['houses'] = houses
    print('houses', len(houses))
    print('waterfall', NA.waterfall(W, T))
    NA.street_dressing(W, T)
    NA.plant_all(W, T)
    print('cleared', NA.clear_ways(W, T))


def checks(W, T):
    out = {}
    trA = rail.verify(W, T['cellsA'][0], int(T['ry'][T['cellsA'][0]]), len(T['cellsA']))
    trB = rail.verify(W, T['cellsB'][0], int(T['ry'][T['cellsB'][0]]), len(T['cellsB']))
    out['railA'] = len(trA); out['railB'] = len(trB)
    for nm, tr in (('A', trA), ('B', trB)):
        gap = 0; mg = 0
        for c in tr + tr:
            gap = 0 if c[3] else gap + 1; mg = max(mg, gap)
        out['maxgap' + nm] = mg
        out['sim' + nm] = (rail.simulate(tr), rail.simulate(tr, reverse=True))
        out['sim_slow' + nm] = (rail.simulate(tr, v0=0.1), rail.simulate(tr, reverse=True, v0=0.1))
    out['funi'] = LM.verify_funicular(W, T)
    px, pg, pz = T['summit']
    targets = dict(下城主街=(150, 23, 179), 總站月台=(125, 31, 194), 面海月台=(120, 31, 201), 碼頭=(120, 23, 208), 教堂廣場=(127, 59, 108), 山頂=(px, pg + 1, pz + 4),
                   東城=(206, 29, 120), 地下車站=T['ug_station'], 後山出口=T['ug_exit'], 燈塔=(245, 30, 186), 市場=(92, 23, 189),
                   西梯頂=(T['stairs']['w'][-1][0][0], T['stairs']['w'][-1][1] + 1, T['stairs']['w'][-1][0][1]))
    for i, h_ in enumerate(T['houses']):
        dx, dz = DIRS[h_['front']]
        fx = h_['x0'] + ((h_['w'] if h_['front'] in 'ns' else h_['d']) // 2) + dx * ((h_['d'] if h_['front'] in 'ns' else h_['d']) // 2 + 2)
        fz = h_['z0'] + ((h_['d'] if h_['front'] in 'ns' else h_['w']) // 2) + dz * ((h_['d'] if h_['front'] in 'ns' else h_['d']) // 2 + 2)
        targets['H%d' % i] = (fx, h_['base'] + 1, fz)
    res, seen = NA.walkable_check(W, T, (120, 23, 179), targets)
    out['walk'] = {k: v for k, v in res.items() if not k.startswith('H')}
    hs = [k for k, v in res.items() if k.startswith('H') and not v]
    out['houses_unreachable'] = (len(hs), len(T['houses']), [(T['houses'][int(k[1:])]['x0'], T['houses'][int(k[1:])]['z0'], T['houses'][int(k[1:])]['base']) for k in hs][:30])
    T['seen'] = seen
    return out


def main():
    t0 = time.time()
    W = World(); T = build_height()
    rail.prepare(T)
    fill_terrain(W, T)
    info = rail.build(W, T)
    print('rail', info)
    layout(W, T)
    c = checks(W, T)
    for k, v in c.items(): print(' ', k, v)
    T['checks'] = c; T['railinfo'] = info
    print('built', round(time.time() - t0, 1))
    return W, T


if __name__ == '__main__':
    W, T = main()
    for v in sys.argv[1:] or ['sw']:
        if ':' in v:
            v, c = v.split(':'); c = tuple(int(q) for q in c.split(','))
            print(R.render(W.a, W.names, f'dbg_{v}_crop.png', view=v, scale=4, crop=c))
        else:
            print(R.render(W.a, W.names, f'dbg_{v}.png', view=v, scale=2))
