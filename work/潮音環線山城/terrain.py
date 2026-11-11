"""地形：高度圖、台地、海灣、環線走廊。"""
import numpy as np
from core import *

# 環線（A＝內圈，B＝外圈），軌面 y=30，道床頂 y=29
RAIL_Y = 30
CH = 20
PEAK = (122, 76)
LOW = 22           # 下城地面
TSTEP = 6          # 台地階高


BZ1 = 199


def build_height():
    X, Z = np.meshgrid(np.arange(SX), np.arange(SZ), indexing='ij')
    px, pz = PEAK
    dx = X - px; dz = Z - pz
    ax = np.where(dx >= 0, 100.0, 92.0)
    az = np.where(dz >= 0, 116.0, 44.0)
    p = 2.6
    u = ((np.abs(dx) / ax) ** p + (np.abs(dz) / az) ** p) ** (1 / p)     # 0=山頂 1=環線內緣
    n1 = fbm((SX, SZ), 48, 11); n2 = fbm((SX, SZ), 14, 12, 3); n3 = fbm((SX, SZ), 90, 13, 2)
    ang = np.arctan2(dz, dx)                 # 0=東, +pi/2=南
    south = np.clip(np.sin(ang), 0, 1)       # 南側權重
    east = np.clip(np.cos(ang), 0, 1)
    north = np.clip(-np.sin(ang), 0, 1)
    west = np.clip(-np.cos(ang), 0, 1)
    base = (LOW * south ** 2 + 29 * east ** 2 + 34 * north ** 2 + 29 * west ** 2)
    uu = u + n2 * 0.035 + n1 * 0.03
    # 剖面：u>0.8 平地；0.8→0.34 台地爬升 42；0.34→0 山頂
    u_flat, u_top = 0.80, 0.283
    TOPTOWN = LOW + 6 * TSTEP          # 58
    t = np.clip((u_flat - uu) / (u_flat - u_top), 0, 1)
    mid = base + (TOPTOWN - base) * t
    s = np.clip((u_top - uu) / u_top, 0, 1)
    peak = TOPTOWN + (100 - TOPTOWN) * (s ** 0.8) + n2 * 5 * s + n1 * 3 * s
    h = np.where(uu < u_top, peak, mid)
    # 北嶺：從山頂往北延伸，讓環線穿隧道
    ridge = (20 + 44 * np.clip((Z - 28) / 40.0, 0, 1)) * np.clip((Z + 20) / 48.0, 0, 1) * np.exp(-((X - 138 - (pz - Z) * 0.25) / 24.0) ** 2) * np.clip((pz + 6 - Z) / 12.0, 0, 1)
    h = np.maximum(h, np.where(ridge > 2, 30 + ridge + n1 * 4, 0))
    # 環線外的丘陵
    out = np.clip(uu - 1.0, 0, 1)
    hills = 30 + n3 * 9 + n1 * 5 + 8 * north
    h = np.where(uu > 1.0, hills * np.clip(out * 8, 0, 1) + h * (1 - np.clip(out * 8, 0, 1)), h)
    town = (uu < u_flat + 0.02) & (uu > u_top - 0.03) & ((south > 0.25) | (east > 0.45))
    farm = (uu < u_flat) & (uu > u_top) & (west > 0.55) & ~town
    # 台地量化
    q = LOW + np.round((h - LOW) / TSTEP) * TSTEP
    h = np.where(town & (h > LOW + 1), q, h)
    q4 = 30 + np.round((h - 30) / 4) * 4
    h = np.where(farm & (h > 31), q4, h)
    # 教堂廣場：切進山體的平台
    plaza = (X >= 104) & (X <= 142) & (Z >= 90) & (Z <= 112)
    h = np.where(plaza, TOPTOWN, h); town = town | plaza
    # 下城整平
    lowz = (uu > u_flat) & (Z > 150) & (Z < 197) & (X > 44) & (X < 206)
    h = np.where(lowz, np.minimum(h, LOW), h); town = town | lowz
    # 東城整平、山後小站站場
    eastz = (uu > u_flat) & (X > 198) & (X < 228) & (Z > 52) & (Z < 174)
    h = np.where(eastz, 28, h); town = town | eastz
    # 後山：北側抬高成台地，讓北段鐵路成為地下段
    wb = np.clip((60 - Z) / 18.0, 0, 1); wb = wb * wb * (3 - 2 * wb)
    back = 51 + n3 * 6 + n1 * 4
    h = np.where(wb > 0, np.maximum(h, 30 + (back - 30) * wb), h)
    # ---- 海 ----
    sea_d = np.full((SX, SZ), 99.0)
    coast_s = 210 + 4 * np.sin(X / 23.0) + n2 * 4            # 南岸
    sea_d = np.minimum(sea_d, coast_s - Z)
    coast_e = 236 + 3 * np.sin(Z / 19.0) + n2 * 3            # 東岸
    cape = ((X - 244) / 11.0) ** 2 + ((Z - 188) / 16.0) ** 2  # 燈塔岬
    sea_d = np.minimum(sea_d, np.where(cape < 1.0, 99, coast_e - X))
    sea_d = np.where((cape < 1.0), np.maximum(sea_d, (1 - cape) * 9 + n2 * 2), sea_d)
    # 西側水道與溺谷
    coast_w = 17 + 4 * np.sin(Z / 17.0) + n2 * 3 - np.clip((66 - Z) / 3.0, 0, 30)
    sea_d = np.minimum(sea_d, X - coast_w)
    cove = ((X - 26) / 27.0) ** 2 + ((Z - 108) / 25.0) ** 2
    sea_d = np.minimum(sea_d, (cove - 1.0) * 14)
    sea = sea_d < 0
    # 海岸過渡：沙灘與海床
    shore = np.clip(sea_d, -40, 40)
    h = np.where(sea, np.clip(SEA - 1 + shore * 0.9 + n2 * 1.5, 7, SEA - 1), np.minimum(h, 21 + np.maximum(shore, 0) * 2.2 + 0.5))
    beach = ~sea & (Z > BZ1 + 1) & (X > 36) & (X < 222)
    h = np.where(beach, np.minimum(h, 21.4), h)
    h = np.round(h).astype(int)
    return dict(h=h, sea=sea, u=uu, town=town & ~sea, farm=farm & ~sea, south=south, east=east, north=north, west=west,
                shore=sea_d, n1=n1, n2=n2)


def fill_terrain(W, T):
    """把高度圖填成方塊：岩層、表土、沙灘、海水、擋土牆。"""
    h = T['h']; sea = T['sea']
    B = W.B
    stone, andesite, tuff, cobble, mossy, deep, calcite = B('stone'), B('andesite'), B('tuff'), B('cobblestone'), B('mossy_cobblestone'), B('deepslate'), B('calcite')
    grass, dirt, coarse, sand, sandstone, gravel, clay, water = B('grass_block'), B('dirt'), B('coarse_dirt'), B('sand'), B('sandstone'), B('gravel'), B('clay'), B('water')
    sb, msb, csb = B('stone_bricks'), B('mossy_stone_bricks'), B('cracked_stone_bricks')
    rs = np.random.RandomState(5)
    Y = np.arange(SY)[None, :, None]
    H = h[:, None, :]
    a = W.a
    solid = Y <= H
    # 岩層：依 y＋雜訊分帶
    band = (Y + (T['n1'] * 6 + T['n2'] * 3)[:, None, :] + rs.rand(SX, SY, SZ) * 2.2)
    bi = (band // 3).astype(int) % 7
    lut = np.array([stone, stone, andesite, stone, tuff, cobble, andesite])
    rock = lut[bi]
    rock = np.where(Y < 10 + (T['n2'] * 3)[:, None, :], deep, rock)
    # 海崖淺色層理
    rock = np.where(((Y == 26) | (Y == 27) | (Y == 41)) & (rs.rand(SX, SY, SZ) < 0.7), calcite, rock)
    rock = np.where((rs.rand(SX, SY, SZ) < 0.06) & (Y < 40), mossy, rock)
    a[:] = np.where(solid, rock, 0)
    # 坡度
    pad = np.pad(h, 1, mode='edge')
    nb = np.stack([pad[2:, 1:-1], pad[:-2, 1:-1], pad[1:-1, 2:], pad[1:-1, :-2]])
    drop = h - nb.min(0)             # 往下最大落差
    T['drop'] = drop
    gentle = (drop <= 2) & ~sea
    highrock = (h > 62) & ~T['town'] & ((drop >= 2) | (rs.rand(SX, SZ) < 0.55)) & (T['u'] < 0.30)
    xs, zs = np.nonzero(gentle & ~highrock)
    for x, z in zip(xs.tolist(), zs.tolist()):
        hh = h[x, z]
        if hh <= 21 or (T['shore'][x, z] < 5 and hh <= 23):
            a[x, hh - 2:hh + 1, z] = sand; a[x, hh - 3, z] = sandstone
        else:
            a[x, hh, z] = grass; a[x, hh - 2:hh, z] = dirt
    # 陡坡上零星草與碎石
    xs, zs = np.nonzero((drop > 2) & (drop <= 4) & ~sea & (rs.rand(SX, SZ) < 0.35) & ~T['town'])
    a[xs, h[xs, zs], zs] = np.where(rs.rand(len(xs)) < 0.5, grass, coarse)
    # 海床
    xs, zs = np.nonzero(sea)
    r = rs.rand(len(xs))
    topb = np.where(h[xs, zs] >= SEA - 3, sand, np.where(r < 0.55, sand, np.where(r < 0.85, gravel, clay)))
    a[xs, h[xs, zs], zs] = topb
    a[xs, h[xs, zs] - 1, zs] = sand
    wat = (Y > H) & (Y <= SEA) & sea[:, None, :]
    a[wat] = water
    # 擋土牆：城鎮台地與梯田的垂直面
    wallmask = (T['town'] | T['farm']) & (drop >= 3)
    xs, zs = np.nonzero(wallmask)
    for x, z in zip(xs.tolist(), zs.tolist()):
        hh = h[x, z]; lo = hh - drop[x, z] + 1
        if T['town'][x, z]:
            for y in range(lo, hh + 1):
                r = rs.rand()
                a[x, y, z] = sb if r < 0.68 else msb if r < 0.82 else csb if r < 0.92 else cobble
        else:
            for y in range(lo, hh + 1):
                r = rs.rand()
                a[x, y, z] = cobble if r < 0.6 else mossy if r < 0.85 else andesite
