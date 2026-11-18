"""生態系車站合集：5 種模組 × 16 生態系。座標：X 沿軌道（東），Z 0–12（南），Y 0–29。"""
import math, random, struct, zlib
import numpy as np
from core import World, DEFS, PROPS, BLOCK_VERSION, OPP
from biomes import BIOMES, BYID

H, WZ = 30, 13
G = 9                # 地表頂面方塊
YU, YE = 2, 17       # 地下 / 高架 軌面
ZR = (2, 10)         # 兩條軌道
KINDS = {'ug_station': 24, 'ug_track': 16, 'ramp': 32, 'el_track': 16, 'el_station': 24}
KIND_ZH = {'ug_station': '地下車站', 'ug_track': '隧道段', 'ramp': '升降坡道', 'el_track': '高架段', 'el_station': '高架車站'}
POSTS = (2, 8, 15, 21)

# 坡道高度：x0–4 y2，之後「升、升、平」直到 y17
RAMP_H = []
_h = YU
for _x in range(32):
    RAMP_H.append(_h)
    _i = _x - 5
    if _i >= 0 and _i % 3 in (0, 1) and _h < YE:
        _h += 1
assert RAMP_H[0] == YU and RAMP_H[-1] == YE and RAMP_H[26] == 16 and RAMP_H[27] == 17, RAMP_H

NONFULL = ('stairs', 'slab', 'fence', '_wall', 'pane', 'bars', 'rail', 'lever', 'lantern', 'carpet', 'snow_layer', 'leaves', 'glass',
           'grass', 'fern', 'flower', 'bush', 'poppy', 'dandelion', 'daisy', 'bluet', 'cornflower', 'orchid', 'allium', 'tulip', 'lily',
           'mushroom', 'fungus', 'roots', 'petals', 'eyeblossom', 'propagule', 'moss_carpet', 'cactus', 'bamboo', 'deadbush', 'seagrass',
           'kelp', 'pickle', 'vine', 'hanging', 'campfire', 'sapling', 'wildflowers', 'chain', 'trapdoor', 'water', 'air', 'coral_fan',
           'barrel', 'hay', 'melon', 'shroomlight', 'froglight', 'glowstone', 'sea_lantern', 'path')


def is_full(name):
    if name in ('red_mushroom_block', 'brown_mushroom_block', 'mushroom_stem', 'grass_path', 'hay_block', 'melon_block', 'barrel',
                'shroomlight', 'glowstone', 'sea_lantern', 'ochre_froglight', 'verdant_froglight', 'pearlescent_froglight', 'mud',
                'muddy_mangrove_roots', 'moss_block', 'pale_moss_block', 'crimson_nylium', 'grass_block', 'mycelium', 'podzol'):
        return True
    if name == 'glass':
        return True
    return not any(k in name for k in NONFULL)


class Piece:
    def __init__(self, bio, kind):
        self.P = bio
        self.kind = kind
        self.L = KINDS[kind]
        self.W = World(size=(self.L, H, WZ))
        self.W.rng = random.Random(zlib.crc32((bio['id'] + kind).encode()))
        self.rng = self.W.rng
        self.a = self.W.a
        self.top_ids = set()
        self.water0 = np.zeros(self.a.shape, bool)
        self.rails = {}          # (x,z) -> y
        self.walk = None

    # ---- 方塊 ----
    def b(self, name, **st):
        return self.W.B(name, **st)

    def pick(self, key_or_val):
        v = self.P.get(key_or_val, key_or_val) if isinstance(key_or_val, str) else key_or_val
        if isinstance(v, str):
            return self.blk(v)
        names = [n for n, _ in v]; ws = [w for _, w in v]
        return self.blk(self.rng.choices(names, ws)[0])

    def blk(self, name):
        full = 'minecraft:' + name
        props = [p['name'] for p in DEFS[full]['properties']] if full in DEFS else []
        if name in ('mushroom_stem',):
            return self.b(name, huge_mushroom_bits=15)
        if name in ('red_mushroom_block', 'brown_mushroom_block'):
            return self.b(name, huge_mushroom_bits=14)
        if 'pillar_axis' in props:
            return self.b(name, pillar_axis='y')
        return self.b(name)

    def log(self, name, axis='y'):
        full = 'minecraft:' + name
        props = [p['name'] for p in DEFS[full]['properties']]
        if 'pillar_axis' in props:
            return self.b(name, pillar_axis=axis)
        return self.blk(name)

    def put(self, x, y, z, b):
        self.W.put(x, y, z, b)

    def get(self, x, y, z):
        return self.W.names[self.W.get(x, y, z)]

    def box(self, x0, y0, z0, x1, y1, z1, b):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.put(x, y, z, b() if callable(b) else b)

    def stairs(self, mat, asc, upside=False):
        return self.W.stairs(mat, asc, upside)

    def slab(self, mat, top=False):
        return self.W.slab(mat, top)

    def lantern(self, hanging):
        return self.b(self.P['lantern'], hanging=hanging)

    def solid(self, x, y, z):
        return is_full(self.get(x, y, z))


# ------------------------------------------------------------------ 地層
STRATA = ['hardened_clay', 'orange_terracotta', 'yellow_terracotta', 'hardened_clay', 'white_terracotta', 'orange_terracotta',
          'red_terracotta', 'hardened_clay', 'brown_terracotta', 'orange_terracotta']


def ground(pc):
    P = pc.P; L = pc.L
    ocean = P.get('ocean')
    for x in range(L):
        for z in range(WZ):
            for y in range(G + 1):
                if ocean:
                    if y <= 3: b = pc.pick('deep')
                    elif y <= 5: b = pc.pick('sub')
                    elif y == 6: b = pc.pick('top')
                    elif z in (0, WZ - 1): b = pc.blk('sand') if y < G else pc.blk('sand')
                    else:
                        b = pc.b('water'); pc.water0[x, y, z] = True
                elif P.get('strata'):
                    b = pc.blk(STRATA[y % len(STRATA)]) if y < G else pc.pick('top')
                else:
                    if y <= 5: b = pc.pick('deep')
                    elif y < G: b = pc.pick('sub')
                    else: b = pc.pick('top')
                pc.put(x, y, z, b)
    tops = P['top'] if isinstance(P['top'], list) else [(P['top'], 1)]
    pc.top_ids = {pc.blk(n) for n, _ in tops}


def is_ground_top(pc, x, z):
    if pc.P.get('ocean'):
        return pc.W.get(x, 6, z) in pc.top_ids and pc.water0[x, 7, z] and pc.get(x, 7, z) == 'water'
    return pc.W.get(x, G, z) in pc.top_ids and pc.get(x, G + 1, z) == 'air'


# ------------------------------------------------------------------ 植物、樹
def plant(pc, x, z, spec=None):
    P = pc.P
    if spec is None:
        names = [n for n, _ in P['plants']]; ws = [w for _, w in P['plants']]
        spec = pc.rng.choices(names, ws)[0]
    if P.get('ocean'):
        if not is_ground_top(pc, x, z): return
        if spec == 'seagrass':
            pc.put(x, 7, z, pc.b('seagrass'))
        elif spec == 'sea_pickle':
            pc.put(x, 7, z, pc.b('sea_pickle', cluster_count=pc.rng.randint(0, 3)))
        elif spec == 'coral':
            pc.put(x, 6, z, pc.blk(pc.rng.choice(['tube_coral_block', 'brain_coral_block', 'horn_coral_block', 'fire_coral_block', 'bubble_coral_block'])))
        return
    y = G + 1
    if pc.get(x, y, z) != 'air' or pc.get(x, y + 1, z) != 'air':
        return
    below = pc.get(x, y - 1, z)
    if spec in ('tall_grass', 'large_fern', 'rose_bush', 'tall_dry_grass_x'):
        pc.put(x, y, z, pc.b(spec, upper_block_bit=False)); pc.put(x, y + 1, z, pc.b(spec, upper_block_bit=True))
    elif spec == 'cactus':
        if 'sand' not in below: return
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if pc.get(x + dx, y, z + dz) != 'air' or pc.get(x + dx, y + 1, z + dz) != 'air': return
        for k in range(pc.rng.randint(1, 3)):
            pc.put(x, y + k, z, pc.b('cactus'))
    elif spec == 'bamboo':
        n = pc.rng.randint(3, 6)
        for k in range(n):
            pc.put(x, y + k, z, pc.b('bamboo', bamboo_leaf_size='large_leaves' if k >= n - 2 else 'no_leaves', bamboo_stalk_thickness='thin'))
    elif spec == 'melon_block':
        pc.put(x, y, z, pc.b('melon_block'))
    elif spec == 'snow_layer':
        if is_full(below): pc.put(x, y, z, pc.b('snow_layer', height=pc.rng.choice([0, 0, 1])))
    elif spec == 'sweet_berry_bush':
        pc.put(x, y, z, pc.b('sweet_berry_bush', growth=3))
    elif spec in ('pink_petals', 'wildflowers'):
        pc.put(x, y, z, pc.b(spec, growth=pc.rng.randint(1, 3), cardinal_direction=pc.rng.choice(['north', 'south', 'east', 'west'])))
    elif spec == 'mangrove_propagule':
        pc.put(x, y, z, pc.b('mangrove_propagule', propagule_stage=pc.rng.randint(1, 3)))
    elif spec == 'pale_moss_carpet':
        pc.put(x, y, z, pc.b('pale_moss_carpet'))
    else:
        pc.put(x, y, z, pc.blk(spec))


def scatter(pc, xs, zs, dens=None):
    dens = pc.P['density'] if dens is None else dens
    for x in xs:
        for z in zs:
            if pc.rng.random() < dens and is_ground_top(pc, x, z):
                plant(pc, x, z)


def puddles(pc, n):
    for _ in range(n * 6):
        x = pc.rng.randrange(1, pc.L - 1); z = pc.rng.randrange(1, WZ - 1)
        if not is_ground_top(pc, x, z): continue
        if all(pc.W.get(x + dx, G, z + dz) in pc.top_ids and pc.get(x + dx, G + 1, z + dz) == 'air' for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            pc.put(x, G, z, pc.b('water'))
            if pc.rng.random() < 0.5: pc.put(x, G + 1, z, pc.b('waterlily'))
            n -= 1
            if n <= 0: return


def leaf_blob(pc, cx, cy, cz, r, leaf, ry=None, keep_core=True):
    ry = r if ry is None else ry
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - ry, cy + ry + 1):
            for z in range(cz - r, cz + r + 1):
                d = ((x - cx) / (r + .5)) ** 2 + ((y - cy) / (ry + .5)) ** 2 + ((z - cz) / (r + .5)) ** 2
                if d <= 1 and pc.get(x, y, z) == 'air' and pc.rng.random() > 0.08 * (d > .6):
                    pc.put(x, y, z, leaf)


def tree(pc, x, z, kind):
    """在 (x,z) 地表長一棵小樹；回傳是否成功。"""
    y = G + 1
    if not is_ground_top(pc, x, z) and kind != 'deadbush':
        return False
    for yy in range(y, y + 7):
        if pc.get(x, yy, z) != 'air': return False
    rng = pc.rng
    if kind in ('oak', 'swamp_oak'):
        h = rng.randint(4, 5); lg = pc.log('oak_log'); lf = pc.b('oak_leaves')
        leaf_blob(pc, x, y + h - 1, z, 2, lf, 1)
        pc.box(x, y, z, x, y + h - 1, z, lg)
        if kind == 'swamp_oak':
            for _ in range(10):
                vx, vz = x + rng.randint(-2, 2), z + rng.randint(-2, 2)
                vy = y + h - 2
                if pc.get(vx, vy, vz) == 'oak_leaves' and pc.get(vx, vy - 1, vz) == 'air':
                    for d, bit in (((0, 1), 1), ((-1, 0), 2), ((0, -1), 4), ((1, 0), 8)):
                        if pc.get(vx - d[0], vy - 1, vz - d[1]) == 'air' and False: pass
    elif kind == 'birch':
        h = rng.randint(5, 6); lg = pc.log('birch_log'); lf = pc.b('birch_leaves')
        leaf_blob(pc, x, y + h - 1, z, 1, lf, 2)
        pc.box(x, y, z, x, y + h - 1, z, lg)
    elif kind in ('spruce', 'spruce_snow'):
        h = rng.randint(6, 7); lg = pc.log('spruce_log'); lf = pc.b('spruce_leaves')
        for k, r in enumerate([1, 2, 1, 2, 1, 0, 0][:h]):
            yy = y + h - 1 - k + 1
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if abs(dx) + abs(dz) <= r + (r == 2) - 0 and not (abs(dx) == 2 and abs(dz) == 2):
                        if pc.get(x + dx, yy, z + dz) == 'air': pc.put(x + dx, yy, z + dz, lf)
        pc.box(x, y, z, x, y + h - 1, z, lg)
        if kind == 'spruce_snow':
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    for yy in range(y + h + 2, y, -1):
                        if pc.get(x + dx, yy, z + dz) == 'spruce_leaves':
                            if pc.get(x + dx, yy + 1, z + dz) == 'air': pc.put(x + dx, yy + 1, z + dz, pc.b('snow_layer', height=0))
                            break
    elif kind == 'jungle':
        h = rng.randint(5, 6); lg = pc.log('jungle_log'); lf = pc.b('jungle_leaves')
        leaf_blob(pc, x, y + h - 1, z, 2, lf, 1)
        pc.box(x, y, z, x, y + h - 1, z, lg)
        for dz, d in ((1, 2), (-1, 0)):
            if pc.get(x, y + 2, z + dz) == 'air':
                pc.put(x, y + 2, z + dz, pc.b('cocoa', age=2, direction=d))
    elif kind == 'darkoak':
        h = 4; lg = pc.log('dark_oak_log'); lf = pc.b('dark_oak_leaves')
        for dx in (0, 1):
            for dz in (0, 1):
                if not is_ground_top(pc, x + dx, z + dz): return False
        leaf_blob(pc, x, y + h, z, 3, lf, 1)
        pc.box(x, y, z, x + 1, y + h, z + 1, lg)
    elif kind == 'acacia':
        lg = pc.log('acacia_log'); lf = pc.b('acacia_leaves')
        pc.box(x, y, z, x, y + 2, z, lg)
        dx = rng.choice([-1, 1])
        pc.put(x + dx, y + 3, z, lg); pc.put(x + 2 * dx, y + 4, z, lg)
        for ddx in range(-2, 3):
            for ddz in range(-2, 3):
                if abs(ddx) + abs(ddz) <= 3:
                    pc.put(x + 2 * dx + ddx, y + 5, z + ddz, lf)
                if abs(ddx) + abs(ddz) <= 1:
                    pc.put(x + 2 * dx + ddx, y + 6, z + ddz, lf)
    elif kind == 'cherry':
        lg = pc.log('cherry_log'); lf = pc.b('cherry_leaves')
        pc.box(x, y, z, x, y + 3, z, lg)
        leaf_blob(pc, x, y + 5, z, 3, lf, 1)
        pc.put(x, y + 4, z, lg)
        for ddx in range(-2, 3):
            for ddz in range(-2, 3):
                if rng.random() < .3 and pc.get(x + ddx, y, z + ddz) == 'air' and pc.solid(x + ddx, y - 1, z + ddz):
                    pc.put(x + ddx, y, z + ddz, pc.b('pink_petals', growth=rng.randint(1, 3), cardinal_direction='north'))
    elif kind == 'mangrove':
        lg = pc.log('mangrove_log'); lf = pc.b('mangrove_leaves'); rt = pc.b('mangrove_roots')
        for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pc.put(x + ddx, y, z + ddz, rt)
        pc.put(x, y, z, rt)
        pc.box(x, y + 1, z, x, y + 5, z, lg)
        leaf_blob(pc, x, y + 5, z, 2, lf, 1)
        for ddx, ddz in ((2, 0), (-2, 0), (0, 2)):
            if pc.get(x + ddx, y + 3, z + ddz) == 'mangrove_leaves' and pc.get(x + ddx, y + 2, z + ddz) == 'air':
                pc.put(x + ddx, y + 2, z + ddz, pc.b('mangrove_propagule', hanging=True, propagule_stage=4))
    elif kind == 'pale':
        lg = pc.log('pale_oak_log'); lf = pc.b('pale_oak_leaves')
        pc.box(x, y, z, x, y + 4, z, lg)
        leaf_blob(pc, x, y + 4, z, 2, lf, 1)
        for ddx in range(-2, 3):
            for ddz in range(-2, 3):
                yy = y + 2
                if pc.get(x + ddx, yy + 1, z + ddz) == 'pale_oak_leaves' and pc.get(x + ddx, yy, z + ddz) == 'air' and rng.random() < .5:
                    pc.put(x + ddx, yy, z + ddz, pc.b('pale_hanging_moss', tip=True))
    elif kind in ('mushroom_red', 'mushroom_brown'):
        st = pc.blk('mushroom_stem')
        h = 4 if kind == 'mushroom_red' else 5
        pc.box(x, y, z, x, y + h - 1, z, st)
        if kind == 'mushroom_red':
            cap = pc.blk('red_mushroom_block')
            for ddx in range(-2, 3):
                for ddz in range(-2, 3):
                    if abs(ddx) == 2 and abs(ddz) == 2: continue
                    edge = abs(ddx) == 2 or abs(ddz) == 2
                    if edge:
                        pc.box(x + ddx, y + h - 2, z + ddz, x + ddx, y + h - 1, z + ddz, cap)
                    elif abs(ddx) <= 1 and abs(ddz) <= 1:
                        pc.put(x + ddx, y + h, z + ddz, cap)
            pc.put(x, y + h - 1, z, st)
        else:
            cap = pc.blk('brown_mushroom_block')
            for ddx in range(-3, 4):
                for ddz in range(-3, 4):
                    if abs(ddx) == 3 and abs(ddz) == 3: continue
                    pc.put(x + ddx, y + h, z + ddz, cap)
    elif kind == 'crimson':
        st = pc.log('crimson_stem'); wt = pc.blk('nether_wart_block')
        pc.box(x, y, z, x, y + 4, z, st)
        leaf_blob(pc, x, y + 5, z, 2, wt, 1)
        pc.put(x + 1, y + 5, z, pc.blk('shroomlight'))
        for ddx in range(-2, 3):
            for ddz in range(-2, 3):
                if pc.get(x + ddx, y + 4, z + ddz) == 'nether_wart_block' and pc.get(x + ddx, y + 3, z + ddz) == 'air' and rng.random() < .4:
                    pc.put(x + ddx, y + 3, z + ddz, pc.b('weeping_vines', weeping_vines_age=3))
    elif kind == 'cactus':
        plant(pc, x, z, 'cactus')
    elif kind == 'deadbush':
        plant(pc, x, z, 'deadbush')
    return True


def plant_trees(pc, spots):
    kinds = pc.P['tree']
    if not kinds: return
    for i, (x, z) in enumerate(spots):
        tree(pc, x, z, kinds[i % len(kinds)])


# ------------------------------------------------------------------ 屋頂
def roof_y(style, z, za, zb, base, x=None, xa=None, xb=None):
    mid = (za + zb) / 2
    d = int(min(z - za, zb - z))
    if style in ('gable', 'leafy', 'stepgable'):
        return base + d
    if style == 'low':
        return base + d // 2
    if style == 'pagoda':
        return base + max(0, d - 1)
    if style == 'flat':
        return base
    if style in ('mushroom', 'vault'):
        half = (zb - za) / 2 + 0.7
        hh = 4 if style == 'mushroom' else 3
        dz = (z - mid) / half
        f = math.sqrt(max(0.0, 1 - dz * dz))
        if style == 'mushroom' and x is not None:
            ex = min(x - xa, xb - x)
            fx = math.sqrt(max(0.0, 1 - (max(0, 3 - ex) / 3.5) ** 2))
            f *= fx
        return base + int(round(hh * f))
    raise ValueError(style)


def roof(pc, style, xa, xb, za, zb, base, ends=(), lamp_center=True):
    """沿 X 延伸的屋頂。ends：要補山牆的 x。"""
    P = pc.P
    mid = (za + zb) / 2
    rs, rsl, rf = P['roof_stairs'], P['roof_slab'], pc.blk(P['roof_full'])
    for x in range(xa, xb + 1):
        prev = None
        for z in range(za, zb + 1):
            y = roof_y(style, z, za, zb, base, x, xa, xb)
            d = int(min(z - za, zb - z))
            side = 's' if z < mid else ('n' if z > mid else 'c')
            if style in ('gable', 'leafy'):
                if side == 'c':
                    pc.put(x, y, z, rf); pc.put(x, y + 1, z, pc.slab(rsl))
                else:
                    pc.put(x, y, z, pc.stairs(rs, side))
                    if d > 0: pc.put(x, y - 1, z, pc.stairs(rs, OPP[side], True))
                    if style == 'leafy' and pc.rng.random() < .55:
                        pc.put(x, y + 1, z, pc.b(P['roof_leaves']))
            elif style == 'stepgable':
                pc.put(x, y, z, rf)
                if d > 0: pc.put(x, y - 1, z, rf)
                pc.put(x, y + 1, z, pc.b('snow_layer', height=1 if side == 'c' else 0))
            elif style == 'low':
                if side == 'c':
                    pc.put(x, y, z, rf); pc.put(x, y + 1, z, pc.slab(rsl))
                else:
                    pc.put(x, y, z, pc.slab(rsl, top=(d % 2 == 1)))
            elif style == 'pagoda':
                if d == 0:
                    pc.put(x, y, z, pc.slab(rsl))
                    if x in (xa, xb): pc.put(x, y + 1, z, pc.stairs(rs, 'n' if z == za else 's'))
                elif side == 'c':
                    pc.put(x, y, z, rf); pc.put(x, y + 1, z, pc.stairs(rs, 'n')); pc.put(x, y + 1, z, pc.slab(rsl))
                else:
                    pc.put(x, y, z, pc.stairs(rs, side))
                    if d > 1: pc.put(x, y - 1, z, pc.stairs(rs, OPP[side], True))
            elif style == 'flat':
                pc.put(x, y, z, rf)
                if z in (za, zb) or x in (xa, xb):
                    pc.put(x, y + 1, z, pc.blk(P['mas_trim']) if (x + z) % 2 == 0 else pc.slab(P['mas_slab']))
                elif abs(z - mid) <= 2 and xa + 2 <= x <= xb - 2:
                    if abs(z - mid) == 2: pc.put(x, y + 1, z, pc.blk(P['planks']) if x % 3 else pc.b(P['pane']))
                    else: pc.put(x, y + 1, z, pc.b(P['pane']))
                    pc.put(x, y + 2, z, pc.slab(rsl))
            elif style in ('mushroom', 'vault'):
                rib = style == 'vault' and (x in (xa, xb) or x in POSTS or (x - xa) % 7 == 0)
                blk = pc.blk(P['planks']) if rib else (pc.blk('glass') if style == 'vault' else rf)
                ys = [y]
                if prev is not None and abs(prev - y) > 1:
                    ys = range(min(prev, y) + 1, max(prev, y) + 1) if y > prev else range(y, prev)
                for yy in set(list(ys) + [y]):
                    pc.put(x, yy, z, blk)
                if style == 'mushroom' and z not in (za, zb):
                    pc.put(x, y - 1, z, blk)
            prev = y
    # 山牆
    if style in ('gable', 'leafy', 'stepgable', 'low', 'pagoda'):
        for x in ends:
            for z in range(za + 1, zb):
                ytop = roof_y(style, z, za, zb, base)
                for y in range(base, ytop if style != 'stepgable' else ytop - 1):
                    if pc.get(x, y, z) == 'air':
                        pc.put(x, y, z, pc.blk(P['planks']))
            if lamp_center:
                zc = (za + zb) // 2
                if pc.get(x, base + 1, zc) == P['planks']:
                    pc.put(x, base + 1, zc, pc.blk(P['lampblock']))


# ------------------------------------------------------------------ 鐵軌
def lay_rails(pc, hfun, powered=(), redstone=(), levers=()):
    P = pc.P; L = pc.L
    for x in range(L):
        h = hfun(x)
        hn = hfun(x + 1) if x + 1 < L else h
        for z in ZR:
            pw = x in powered
            asc = hn == h + 1
            if pw:
                b = pc.b('golden_rail', rail_direction=2 if asc else 1, rail_data_bit=True)
            else:
                b = pc.b('rail', rail_direction=2 if asc else 1)
            pc.put(x, h, z, b)
            pc.put(x, h - 1, z, pc.blk('redstone_block') if x in redstone else pc.blk(P['bed']))
            pc.rails[(x, z)] = h
            for yy in (h + 1, h + 2):
                pc.put(x, yy, z, 0)
    for (x, z) in levers:
        h = hfun(x)
        pc.put(x, h, z, pc.b('lever', lever_direction='up_east_west', open_bit=True))


def deck_row(pc, x, y, mid_key='mid'):
    """一列甲板（z0–12）在 y：邊緣、走道、道床由 lay_rails 覆蓋、軌間。"""
    P = pc.P
    for z in range(WZ):
        if z in (0, WZ - 1): b = pc.blk(P['mas_trim'])
        elif z in (1, WZ - 2): b = pc.pick('mas')
        elif z in ZR: b = pc.blk(P['bed'])
        else: b = pc.pick(mid_key)
        pc.put(x, y, z, b)


def platform_row(pc, x, y):
    P = pc.P
    for z in range(3, 10):
        pc.put(x, y, z, pc.blk(P['edge']) if z in (3, 9) else pc.pick('floor'))


# ------------------------------------------------------------------ 高架共用
def piers(pc, xs, top=15, foot=4):
    P = pc.P
    for px in xs:
        for z in (0, 1, WZ - 2, WZ - 1):
            for y in range(foot, top + 1):
                pc.put(px, y, z, pc.pick('mas'))
        for z in range(WZ):
            pc.put(px, top, z, pc.blk(P['mas_trim']))
        # 拱腋
        for dx in (-1, 1):
            if (px + dx) in xs: continue
            for z in (0, 1, WZ - 2, WZ - 1):
                pc.put(px + dx, top, z, pc.stairs(P['mas_stairs'], 'w' if dx > 0 else 'e', True))
                pc.put(px + dx, top - 1, z, 0) if pc.get(px + dx, top - 1, z) == 'air' else None


def girders(pc, y, x0, x1):
    P = pc.P
    for x in range(x0, x1 + 1):
        for z in (0, WZ - 1):
            if pc.get(x, y, z) == 'air':
                pc.put(x, y, z, pc.blk(P['mas_trim']))


def parapet(pc, x, y):
    P = pc.P
    for z in (0, WZ - 1):
        pc.put(x, y, z, pc.b(P['mas_wall']) if 'wall' in P['mas_wall'] else pc.blk(P['mas_wall']))


def hang_under(pc, x, y, z, n=2):
    P = pc.P
    hb = P.get('hang')
    if not hb or pc.get(x, y, z) != 'air' or not pc.solid(x, y + 1, z): return
    for k in range(n):
        if pc.get(x, y - k, z) != 'air': break
        last = k == n - 1 or pc.get(x, y - k - 1, z) != 'air'
        if hb == 'pale_hanging_moss': pc.put(x, y - k, z, pc.b(hb, tip=last))
        elif hb == 'weeping_vines': pc.put(x, y - k, z, pc.b(hb, weeping_vines_age=3))
        else:
            pc.put(x, y, z, pc.b(hb)); break


def vines_on(pc, x, y0, y1, z, side):
    """在 (x,z) 的空氣格放藤蔓，貼著 side 方向的方塊。bits: 1 南 2 西 4 北 8 東。"""
    bit = {'s': 1, 'w': 2, 'n': 4, 'e': 8}[side]
    for y in range(y0, y1 + 1):
        if pc.get(x, y, z) == 'air' and pc.rng.random() < .7:
            pc.put(x, y, z, pc.b('vine', vine_direction_bits=bit))


def ground_deco(pc, avoid):
    """地表散布植物（避開 avoid(x,z) 為真的格）。"""
    xs = range(pc.L); zs = range(WZ)
    for x in xs:
        for z in zs:
            if avoid(x, z): continue
            if pc.rng.random() < pc.P['density'] and is_ground_top(pc, x, z):
                plant(pc, x, z)
    if pc.P.get('puddles'):
        puddles(pc, 3)


def lamp_post(pc, x, y, z):
    P = pc.P
    f = pc.b(P['fence']) if 'fence' in P['fence'] or 'bars' in P['fence'] else pc.blk(P['fence'])
    pc.put(x, y, z, f); pc.put(x, y + 1, z, f); pc.put(x, y + 2, z, pc.lantern(False))


def bench_planter(pc, x0, x1, y):
    """島式月台中央：長椅（z4 面北、z8 面南）＋花台（z5–7）。y 為站立高度。"""
    P = pc.P
    for x in range(x0, x1 + 1):
        pc.put(x, y, 4, pc.stairs(P['wstairs'], 's'))
        pc.put(x, y, 8, pc.stairs(P['wstairs'], 'n'))
        pc.put(x, y, 5, pc.slab(P['wslab'], True)); pc.put(x, y, 7, pc.slab(P['wslab'], True))
        pc.put(x, y, 6, pc.blk(P['soil']))
        spec = P['pot'][0] if x in (x0, x1) else P['pot'][1]
        if P.get('ocean'):
            pc.put(x, y, 6, pc.blk('sand')); pc.put(x, y + 1, 6, pc.b('sea_pickle', cluster_count=3) if (x - x0) % 2 == 0 else pc.blk('sea_lantern'))
            continue
        if spec == 'cactus':
            pc.put(x, y + 1, 6, pc.b('cactus')); pc.put(x, y + 2, 6, pc.b('cactus'))
        elif spec == 'bamboo':
            for k in range(3): pc.put(x, y + 1 + k, 6, pc.b('bamboo', bamboo_leaf_size='small_leaves' if k == 2 else 'no_leaves'))
        elif spec in ('pink_petals',):
            pc.put(x, y + 1, 6, pc.b('pink_petals', growth=3, cardinal_direction='north'))
        elif spec == 'sweet_berry_bush':
            pc.put(x, y + 1, 6, pc.b('sweet_berry_bush', growth=3))
        elif spec == 'mangrove_propagule':
            pc.put(x, y + 1, 6, pc.b('mangrove_propagule', propagule_stage=2))
        elif spec == 'tall_dry_grass':
            pc.put(x, y + 1, 6, pc.blk('tall_dry_grass'))
        else:
            pc.put(x, y + 1, 6, pc.blk(spec))
    # 花台兩端擋板
    for x in (x0 - 1, x1 + 1):
        pc.put(x, y, 6, pc.slab(P['wslab'], True))


# ------------------------------------------------------------------ 高架車站
def el_station(pc):
    P = pc.P; L = pc.L
    ground(pc)
    piers(pc, (2, 11, 21))
    girders(pc, 15, 0, L - 1)
    for x in range(L):
        deck_row(pc, x, 16)
        platform_row(pc, x, 16)
        parapet(pc, x, 17)
    # 樓梯（島中央 z5–7，由 x16 往西下到地面）
    for x in range(12, 16):
        for z in (5, 6, 7): pc.put(x, 16, z, 0)
    for x in range(10, 16):
        ys = x
        for z in (5, 6, 7):
            pc.put(x, ys, z, pc.stairs(P['mas_stairs'], 'e'))
            for y in range(G + 1, ys): pc.put(x, y, z, pc.pick('mas'))
        for z in (4, 8):
            if pc.get(x, ys + 1, z) == 'air':
                pc.put(x, ys + 1, z, pc.b(P['mas_wall']))
            for y in range(G + 1, ys + 1):
                if pc.get(x, y, z) == 'air': pc.put(x, y, z, pc.pick('mas'))
    for x in range(11, 16):
        for z in (4, 8): pc.put(x, 17, z, pc.b(P['fence']))
    for z in (5, 6, 7): pc.put(11, 17, z, pc.b(P['fence']))
    # 地面廣場
    for x in range(2, 10):
        for z in range(3, 10):
            if pc.get(x, G + 1, z) == 'air' or x == 9:
                pc.put(x, G, z, pc.pick('path'))
    for x in range(0, 2):
        for z in (5, 6, 7): pc.put(x, G, z, pc.pick('path'))
    lamp_post(pc, 4, G + 1, 3); lamp_post(pc, 4, G + 1, 9)
    pc.put(6, 15, 6, pc.lantern(True))
    pc.put(3, G + 1, 8, pc.b('barrel', facing_direction=1))
    # 柱、側牆、窗
    for x in range(L):
        for z in (0, WZ - 1):
            if x in POSTS:
                for y in range(17, 21): pc.put(x, y, z, pc.log(P['log']))
            else:
                pc.put(x, 20, z, pc.log(P['log'], 'x'))
                if 9 <= x <= 14:
                    pc.put(x, 17, z, pc.pick('mas'))
                    pc.put(x, 18, z, pc.b(P['pane'])); pc.put(x, 19, z, pc.b(P['pane']))
    for x in POSTS:
        for z in range(1, WZ - 1):
            pc.put(x, 20, z, pc.log(P['log'], 'z'))
        for z in (4, 8):
            pc.put(x, 19, z, pc.lantern(True))
    roof(pc, P['roof'], 0, L - 1, 0, WZ - 1, 21, ends=(0, L - 1))
    bench_planter(pc, 3, 5, 17)
    bench_planter(pc, 18, 20, 17)
    lay_rails(pc, lambda x: YE, powered={2, 21, 10, 11, 12, 13}, redstone={2, 21}, levers=[(12, 3), (12, 9)])
    # 地面裝飾
    def avoid(x, z):
        return 2 <= x <= 9 and 3 <= z <= 9
    ground_deco(pc, avoid)
    under_deck_hang(pc)
    pc.walk = ((4, YE, 3), (3, G + 1, 6))


def under_deck_hang(pc):
    P = pc.P
    if P.get('hang'):
        for x in range(pc.L):
            for z in (0, WZ - 1):
                if pc.rng.random() < .35: hang_under(pc, x, 14, z, 2)
    if P.get('vines'):
        for px in range(pc.L):
            for z in (0, 1, WZ - 2, WZ - 1):
                if pc.get(px, 12, z) != 'air' and 'brick' in pc.get(px, 12, z) or 'cobble' in pc.get(px, 12, z):
                    for dx, side in ((1, 'w'), (-1, 'e')):
                        if pc.get(px + dx, 12, z) == 'air': vines_on(pc, px + dx, 10, 14, z, side)


# ------------------------------------------------------------------ 高架段
def el_track(pc):
    P = pc.P; L = pc.L
    ground(pc)
    piers(pc, (7, 8))
    girders(pc, 15, 0, L - 1)
    for x in range(L):
        deck_row(pc, x, 16)
        parapet(pc, x, 17)
    # 門型架
    for z in (0, WZ - 1):
        for y in range(17, 22): pc.put(8, y, z, pc.log(P['log']))
    for z in range(1, WZ - 1): pc.put(8, 21, z, pc.log(P['log'], 'z'))
    pc.put(8, 22, 6, pc.slab(P['wslab']))
    for z in (3, 9): pc.put(8, 20, z, pc.lantern(True))
    lay_rails(pc, lambda x: YE, powered={4, 12}, redstone={4, 12})
    ground_deco(pc, lambda x, z: False)
    under_deck_hang(pc)


# ------------------------------------------------------------------ 地下車站
def ug_station(pc):
    P = pc.P; L = pc.L
    ocean = P.get('ocean')
    ground(pc)
    for x in range(L):
        for z in range(WZ):
            pc.put(x, 0, z, pc.pick('deep'))
            for y in range(1, 8):
                if z in (0, WZ - 1):
                    if y == 2: b = pc.blk(P['mas_trim'])
                    elif y == 4: b = pc.blk(P.get('band2', P['band'])) if (x % 4 == 0 and 'band2' in P) else pc.blk(P['band'])
                    else: b = pc.pick('mas')
                    pc.put(x, y, z, b)
                elif y == 1:
                    pc.put(x, y, z, pc.pick('mas'))
                elif y == 7:
                    pc.put(x, y, z, pc.blk('glass') if (ocean and 3 <= z <= 9) else pc.pick('mas'))
                else:
                    pc.put(x, y, z, 0)
            if not ocean:
                pc.put(x, 8, z, pc.pick('sub'))
        platform_row(pc, x, 1)
        for z, asc in ((1, 'n'), (WZ - 2, 's')):
            pc.put(x, 6, z, pc.stairs(P['mas_stairs'], asc, True))
    for x in POSTS:
        for z in (0, WZ - 1):
            for y in range(2, 7): pc.put(x, y, z, pc.log(P['log']))
        for z in range(1, WZ - 1):
            pc.put(x, 6, z, pc.log(P['log'], 'z'))
    for x in (5, 12, 18):
        pc.put(x, 4, 0, pc.blk(P['lampblock'])); pc.put(x, 4, WZ - 1, pc.blk(P['lampblock']))
    # 樓梯：x15(y2) → x8(y9)，往西上升
    sy = lambda x: 17 - x
    for x in range(7, 14):
        for z in range(4, 9):
            for y in (7, 8, 9):
                pc.put(x, y, z, pc.pick('mas'))
    for x in range(8, 16):
        for z in (5, 6, 7):
            pc.put(x, sy(x), z, pc.stairs(P['mas_stairs'], 'w'))
            for y in range(2, sy(x)): pc.put(x, y, z, pc.pick('mas'))
            for y in range(sy(x) + 1, 10): pc.put(x, y, z, 0)
        for z in (4, 8):
            for y in range(2, min(sy(x) + 2, 10)): pc.put(x, y, z, pc.pick('mas'))
    # 出入口亭
    if ocean:
        for x in range(4, 17):
            for z in range(2, 11):
                if pc.get(x, G, z) == 'water': pc.put(x, G, z, pc.pick('floor'))
    for x in range(6, 15):
        for z in range(3, 10):
            if not (8 <= x <= 12 and 5 <= z <= 7):
                pc.put(x, G, z, pc.pick('floor'))
    for x in range(6, 15):
        for z in range(3, 10):
            if x in (6, 14) or z in (3, 9):
                corner = x in (6, 14) and z in (3, 9) or (z in (3, 9) and x == 10)
                for y in range(G + 1, G + 4):
                    pc.put(x, y, z, pc.log(P['log']) if corner else pc.blk(P['planks']))
    for z in (5, 6, 7):
        pc.put(6, G + 1, z, 0); pc.put(6, G + 2, z, 0)
    pc.put(6, G + 3, 6, pc.blk(P['lampblock']))
    for x in (8, 9, 11, 12):
        for z in (3, 9): pc.put(x, G + 2, z, pc.b(P['pane']))
    for z in (5, 7): pc.put(14, G + 2, z, pc.b(P['pane']))
    for x in range(9, 14):
        for z in (4, 8): pc.put(x, G + 1, z, pc.b(P['fence']))
    for z in (5, 6, 7): pc.put(13, G + 1, z, pc.b(P['fence']))
    for z in range(3, 10): pc.put(10, G + 4, z, pc.log(P['log'], 'z'))
    pc.put(10, G + 3, 6, pc.lantern(True))
    roof(pc, P['roof'], 5, 15, 2, 10, G + 4, ends=(6, 14), lamp_center=False)
    for x in range(0, 6):
        for z in (5, 6, 7):
            if ocean: pc.put(x, G, z, pc.pick('floor'))
            else: pc.put(x, G, z, pc.pick('path'))
            pc.put(x, G + 1, z, 0)
    # 月台
    bench_planter(pc, 3, 5, 2)
    bench_planter(pc, 18, 20, 2)
    for x in (3, 19):
        for z in (4, 8): pc.put(x, 6, z, pc.lantern(True))
    lay_rails(pc, lambda x: YU, powered={2, 21, 10, 11, 12, 13}, redstone={2, 21}, levers=[(12, 3), (12, 9)])
    def avoid(x, z):
        return 4 <= x <= 16 and 2 <= z <= 10 or (x <= 5 and 5 <= z <= 7)
    ground_deco(pc, avoid)
    plant_trees(pc, [(19, 3), (2, 10), (21, 9)])
    pc.walk = ((4, YU, 3), (1, G + 1, 6))


# ------------------------------------------------------------------ 隧道段
def tunnel_column(pc, x, h, roof_y, ring=False, glass=False):
    P = pc.P
    for z in range(WZ):
        for y in range(0, h - 1): pc.put(x, y, z, pc.pick('deep') if y < h - 2 else pc.pick('mas'))
        if z in (0, WZ - 1):
            for y in range(h - 1, roof_y): pc.put(x, y, z, pc.blk(P['mas_trim']) if ring else pc.pick('mas'))
        else:
            pc.put(x, h - 1, z, pc.pick('mas') if z in (1, WZ - 2) else pc.pick('mid'))
            for y in range(h, roof_y): pc.put(x, y, z, 0)
        pc.put(x, roof_y, z, pc.blk('glass') if (glass and 3 <= z <= 9 and not ring) else (pc.blk(P['mas_trim']) if ring else pc.pick('mas')))
    for z, asc in ((1, 'n'), (WZ - 2, 's')):
        pc.put(x, roof_y - 1, z, pc.stairs(P['mas_stairs'], asc, True))


def ug_track(pc):
    P = pc.P; L = pc.L
    ground(pc)
    for x in range(L):
        tunnel_column(pc, x, YU, 6, ring=(x % 8 == 0), glass=P.get('ocean'))
        if not P.get('ocean'):
            pc.put(x, 7, 0, pc.pick('sub'))
    for x in (4, 12):
        z = 0 if x == 4 else WZ - 1
        pc.put(x, 3, z, pc.blk(P['lampblock']))
    for y in range(2, 6): pc.put(8, y, 6, pc.log(P['log']))
    for z in (5, 7): pc.put(8, 5, z, pc.stairs(P['mas_stairs'], 's' if z == 5 else 'n', True))
    pc.put(8, 4, 5, pc.lantern(True)) if False else None
    lay_rails(pc, lambda x: YU, powered={4, 12}, redstone={4, 12})
    ground_deco(pc, lambda x, z: False)
    plant_trees(pc, [(4, 3), (12, 9)])


# ------------------------------------------------------------------ 坡道
def ramp(pc):
    P = pc.P; L = pc.L
    ocean = P.get('ocean')
    ground(pc)
    h = RAMP_H
    hm = lambda x: max(h[max(0, x - 1)], h[x], h[min(L - 1, x + 1)])
    for x in range(L):
        hx = h[x]
        if hm(x) + 4 <= 8:                          # 隧道
            roof_y = hm(x) + 4
            tunnel_column(pc, x, hx, roof_y, ring=(x % 8 == 0 or x == 7), glass=ocean)
            if x == 7:                               # 洞口立面
                for z in range(WZ):
                    for y in range(roof_y, G + 2):
                        pc.put(x, y, z, pc.blk(P['mas_trim']) if y == G + 1 or z in (0, WZ - 1) else pc.pick('mas'))
                    pc.put(x, G + 2, z, pc.slab(P['mas_slab']))
                for y in range(roof_y, G + 2):
                    pc.put(x, y, 6, pc.blk(P['lampblock'])) if y == roof_y + 1 else None
        elif hx - 1 < G:                             # 路塹
            for z in range(WZ):
                for y in range(0, hx - 1): pc.put(x, y, z, pc.pick('deep') if y < hx - 2 else pc.pick('mas'))
                if z in (0, WZ - 1):
                    for y in range(hx - 1, G + 2): pc.put(x, y, z, pc.pick('mas'))
                    pc.put(x, G + 2, z, pc.b(P['mas_wall']))
                else:
                    pc.put(x, hx - 1, z, pc.pick('mas') if z in (1, WZ - 2) else pc.pick('mid'))
                    for y in range(hx, G + 3): pc.put(x, y, z, 0)
        else:                                        # 路堤 / 高架
            deck = hx - 1
            emb = deck <= 12
            for z in range(WZ):
                if emb:
                    for y in range(5, deck):
                        pc.put(x, y, z, pc.pick('mas') if z in (0, WZ - 1) or y < 7 else pc.pick('sub'))
                else:
                    if ocean:
                        pass
            deck_row(pc, x, deck)
            parapet(pc, x, deck + 1)
            if not emb:
                girders(pc, deck - 1, x, x)
            for z in range(1, WZ - 1):
                for y in range(deck + 1, deck + 4):
                    if (x, z) not in pc.rails and pc.get(x, y, z) != 'air' and z not in (0, WZ - 1): pc.put(x, y, z, 0)
    piers(pc, (27,), top=15)
    for x in range(22, 27):
        pass
    # 坡道高架段的拱腋要在甲板下
    lay_rails(pc, lambda x: h[x] if x < L else h[-1], powered=set(range(4, 29)), redstone=set(range(4, 29)))
    # 路塹／路堤上的燈
    for x in (12, 20):
        pc.put(x, h[x], 6, pc.b(P['fence']) if 'fence' in P['fence'] or 'bars' in P['fence'] else pc.blk(P['fence']))
        pc.put(x, h[x] + 1, 6, pc.b(P['fence']) if 'fence' in P['fence'] or 'bars' in P['fence'] else pc.blk(P['fence']))
        pc.put(x, h[x] + 2, 6, pc.lantern(False))
    for x in (3,):
        pc.put(x, 4, 0, pc.blk(P['lampblock']))
    ground_deco(pc, lambda x, z: 8 <= x <= 21)
    plant_trees(pc, [(2, 10), (5, 2)])
    under_deck_hang(pc)


BUILDERS = {'ug_station': ug_station, 'ug_track': ug_track, 'ramp': ramp, 'el_track': el_track, 'el_station': el_station}


def build_piece(bio, kind):
    pc = Piece(bio, kind)
    BUILDERS[kind](pc)
    finish(pc)
    return pc


def finish(pc):
    W = pc.W
    W.auto_connect()
    # 含水：海洋水帶內的非整塊方塊
    if pc.P.get('ocean'):
        names = W.names
        part = np.array([any(k in n for k in ('seagrass', 'kelp', 'pickle', 'stairs', 'slab', 'fence', '_wall', 'bars', 'pane')) for n in names])
        W.w2 |= part[W.a] & pc.water0
    # 雪原：頂面積雪
    if pc.P.get('snow'):
        X, Y, Z = W.a.shape
        for x in range(X):
            for z in range(Z):
                col = W.a[x, :, z]; nz = np.nonzero(col)[0]
                if not len(nz): continue
                t = int(nz[-1]); n = W.names[col[t]]
                if t >= G + 1 and t + 1 < Y and is_full(n) and 'glass' not in n and 'lantern' not in n and pc.rng.random() < .9:
                    if (x, 2) in pc.rails and t < 18 and z in range(0, WZ): pass
                    W.put(x, t + 1, z, W.B('snow_layer', height=0))


# ------------------------------------------------------------------ 存檔
def void_mask(pc):
    a = pc.W.a
    X, Y, Z = a.shape
    m = np.zeros(a.shape, bool)
    for x in range(X):
        for z in range(Z):
            nz = np.nonzero(a[x, :, z])[0]
            top = max(int(nz[-1]) if len(nz) else 0, G)
            m[x, top + 4:, z] = True
    return m & (a == 0)


def piece_bytes(pc):
    W = pc.W
    void = void_mask(pc)
    a = W.a
    used = np.unique(a)
    water = W.B('water')
    remap = np.zeros(len(W.pal), dtype=np.int32)
    local = []
    for g in used.tolist():
        remap[g] = len(local); local.append(g)
    if W.w2.any() and water not in local:
        remap[water] = len(local); local.append(water)
    prim = remap[a].astype('<i4')
    prim[void] = -1
    sec = np.where(W.w2 & (a != water), remap[water], -1).astype('<i4')
    size = a.shape
    out = bytearray()
    def s(v):
        b = v.encode('utf8'); return struct.pack('<H', len(b)) + b
    def tag(t, name):
        return bytes([t]) + s(name)
    def ilist(name, arr):
        return tag(9, name) + bytes([3]) + struct.pack('<i', len(arr)) + struct.pack('<%di' % len(arr), *arr)
    out += tag(10, '')
    out += tag(3, 'format_version') + struct.pack('<i', 1)
    out += ilist('size', list(size))
    out += tag(10, 'structure')
    out += tag(9, 'block_indices') + bytes([9]) + struct.pack('<i', 2)
    for arr in (prim, sec):
        flat = np.ascontiguousarray(arr).ravel()
        out += bytes([3]) + struct.pack('<i', flat.size) + flat.tobytes()
    out += tag(9, 'entities') + bytes([10]) + struct.pack('<i', 0)
    out += tag(10, 'palette') + tag(10, 'default')
    out += tag(9, 'block_palette') + bytes([10]) + struct.pack('<i', len(local))
    for g in local:
        name, st = W.pal[g]
        out += tag(8, 'name') + s(name)
        out += tag(10, 'states')
        for k, v in st.items():
            if isinstance(v, bool): out += tag(1, k) + bytes([int(v)])
            elif isinstance(v, int): out += tag(3, k) + struct.pack('<i', v)
            else: out += tag(8, k) + s(v)
        out += b'\x00'
        out += tag(3, 'version') + struct.pack('<i', BLOCK_VERSION)
        out += b'\x00'
    out += tag(10, 'block_position_data') + b'\x00'
    out += b'\x00' + b'\x00' + b'\x00'
    out += ilist('structure_world_origin', [0, 0, 0])
    out += b'\x00'
    return bytes(out), void, local
