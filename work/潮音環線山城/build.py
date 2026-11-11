import sys, time, random
from core import *
from terrain import *
import rail, town, landmarks as LM, nature as NA, mine as MN, render as R


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
    T['reserved'][146:159, 182:195] = True         # 金市
    LM.gold_wharf(W, T)
    LM.summit(W, T)
    px, pg, pz = T['summit']
    # 曲折石階：每上一層台地就在平台上橫移再往上
    S = T['stairs'] = {}
    S['main'] = town.stair_path(W, T, town.bent_cells(T, 119, 176, 'n', shift=6, first='l'), None, 3)
    S['funi'] = town.stair_path(W, T, town.until_top(T, 125, 176, 'n'), None, 1, rail=True)
    S['w'] = town.stair_path(W, T, town.bent_cells(T, 84, 174, 'n', shift=5, first='r'), None, 2)
    S['e'] = town.stair_path(W, T, town.bent_cells(T, 158, 174, 'n', shift=5, first='r'), None, 2)
    S['e1'] = town.stair_path(W, T, town.bent_cells(T, 200, 80, 'w', shift=4, first='l'), None, 2)
    S['e2'] = town.stair_path(W, T, town.bent_cells(T, 204, 126, 'w', shift=5, first='r'), None, 2)
    S['sw'] = town.stair_path(W, T, town.bent_cells(T, 60, 150, 'e', top=46, shift=4, first='l'), None, 2)
    # 登頂之字步道：從東梯頂往西，每 9 格南北折一次，最後接上山頂平台
    (x, z), _ = S['e1'][-1]
    cells = [(x, z)]; k = 0
    while x > px + 8:
        for _ in range(6):
            if x <= px + 8: break
            x -= 1; cells.append((x, z))
        tz = pz + 10 if (k % 2 == 0) else pz + 1
        while z != tz:
            z += 1 if tz > z else -1; cells.append((x, z))
        k += 1
    while z != pz + 1: z += 1 if pz + 1 > z else -1; cells.append((x, z))
    while x > px + 3: x -= 1; cells.append((x, z))
    S['top'] = town.stair_path(W, T, cells, None, 2)
    MN.prepare(W, T)
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
    LM.main_station(W, T); LM.church_plaza(W, T); LM.funicular(W, T); LM.market(W, T)      # 纜索鐵道要在廣場鋪面之後，否則紅石塊會被蓋掉
    LM.harbor(W, T); LM.lighthouse(W, T); LM.depot(W, T); LM.underground_station(W, T); LM.gold_market(W, T)
    print('windmill', LM.windmill(W, T))
    print('mine', MN.build(W, T))
    LM.gold_wharf_fit(W, T)
    houses = []
    lowq = ['gold', 'bakery', 'inn', 'smith', 'store', 'bank', 'clinic', 'fish', 'tailor', 'school', 'butcher', 'grocer', 'post', 'carpenter', 'gold', 'inn', 'store', 'bakery']
    upq = ['bakery', 'store', 'inn', 'tailor', 'grocer', 'clinic', 'school', 'gold', 'carpenter', 'butcher', 'post', 'smith']
    ui = 0
    for L in town.LEVELS:
        lots = town.find_lots(T, L, rng, tol=0, gap_p=0.2)
        lots.sort(key=lambda l: -l[2] * l[3])
        for j, (x0, z0, fw, fd, d) in enumerate(lots):
            if x0 < 70 and z0 < 124: continue          # 西北角孤立台地不蓋屋
            low = L == 22
            floors = rng.choice([3, 3, 4]) if low else rng.choice([2, 2, 3, 3]) if L < 52 else rng.choice([2, 2, 3])
            if x0 > 196: floors = 2
            kind = None
            if low and lowq and fw >= 6: kind = lowq.pop(0)
            elif not low and x0 > 160 and z0 < 78 and fw >= 6 and L >= 34: kind = 'gold'       # 礦場旁的金飾街
            elif not low and fw >= 7 and j % 3 == 0:
                kind = upq[ui % len(upq)]; ui += 1
            houses.append(town.house(W, T, x0, z0, fw, fd, d, L, floors, rng, shop=low and rng.random() < 0.6, kind=kind))
    for L in town.LEVELS:           # 第二輪：補小屋
        for (x0, z0, fw, fd, d) in town.find_lots(T, L, rng, wide=(5, 6), deep=(5,), gap_p=0.2, need=0.5):
            if x0 < 70 and z0 < 124: continue
            houses.append(town.house(W, T, x0, z0, fw, fd, d, L, rng.choice([2, 2, 3]) if L > 22 else 3, rng))
    for L in town.LEVELS:           # 第三輪：臨街面較窄的畸零地
        for (x0, z0, fw, fd, d) in town.find_lots(T, L, rng, wide=(7, 6, 5), deep=(6, 5), gap_p=0.1, need=0.34):
            if x0 < 70 and z0 < 124: continue
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
    out['mine_track'] = MN.verify(W, T)
    px, pg, pz = T['summit']
    targets = dict(下城主街=(150, 23, 179), 總站月台=(125, 31, 194), 面海月台=(120, 31, 201), 碼頭=(120, 23, 208), 教堂廣場=(127, 59, 108), 山頂=(px + 3, pg + 1, pz + 1),
                   東城=(206, 29, 120), 地下車站=T['ug_station'], 後山出口=T['ug_exit'], 燈塔=(245, 30, 186), 礦場坑口=(168, 47, 61), 金礦坑室=(140, 47, 61), 礦坑豎井頂=T['mine_shaft'], 市場=(92, 23, 189), 金市=T['gold_market'], 黃金碼頭=T['gold_wharf'],
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
            kw = dict(cut_y=c[4], floor_y=c[5]) if len(c) > 4 else {}
            print(R.render(W.a, W.names, f'dbg_{v}_crop{len(c)}.png', view=v, scale=5, crop=c[:4], **kw))
        else:
            print(R.render(W.a, W.names, f'dbg_{v}.png', view=v, scale=2))
