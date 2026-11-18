"""潮音環線山城：世界陣列、方塊調色盤、方向輔助、NBT 序列化。不依賴 amulet_nbt。"""
import json, struct, random
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
SX, SY, SZ = 256, 128, 256
SEA = 20
BLOCK_VERSION = (1 << 24) | (26 << 16) | (60 << 8)
NAMESPACE = 'chaoyin_loop_261111'

_meta = json.loads((HERE / 'mojang-blocks.json').read_text(encoding='utf8'))
DEFS = {v['name']: v for v in _meta['data_items']}
PROPS = {v['name']: v for v in _meta['block_properties']}
_DEFAULTS = {'pillar_axis': 'y', 'persistent_bit': True, 'update_bit': False, 'minecraft:vertical_half': 'bottom'}

DIRS = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}
ORDER = 'nesw'
OPP = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
LEFT = {'n': 'w', 'w': 's', 's': 'e', 'e': 'n'}   # 面向該方向時的左手
RIGHT = {v: k for k, v in LEFT.items()}
FULL = {'n': 'north', 'e': 'east', 's': 'south', 'w': 'west'}


class World:
    def __init__(self, size=(SX, SY, SZ)):
        self.size = size
        self.a = np.zeros(size, dtype=np.uint16)
        self.w2 = np.zeros(size, dtype=bool)        # 次層放水（含水方塊）
        self.pal = [('minecraft:air', {})]
        self.lookup = {('minecraft:air', ()): 0}
        self.names = ['air']
        self.rng = random.Random(261111)

    # ---------- 調色盤 ----------
    def B(self, name, **st):
        full = name if ':' in name else 'minecraft:' + name
        if full not in DEFS:
            raise ValueError('未知方塊 ' + name)
        allowed = [p['name'] for p in DEFS[full]['properties']]
        st = {('minecraft:' + k if ('minecraft:' + k) in allowed and k not in allowed else k): v for k, v in st.items()}
        bad = set(st) - set(allowed)
        if bad:
            raise ValueError(f'{name} 沒有 state {bad}；可用 {allowed}')
        vals = {k: PROPS[k]['values'][0]['value'] for k in allowed}
        for k, v in _DEFAULTS.items():
            if k in vals:
                vals[k] = v
        vals.update(st)
        for k, v in vals.items():
            ok = [a['value'] for a in PROPS[k]['values']]
            if v not in ok or type(v) is not type(ok[0]):
                raise ValueError(f'{name} {k}={v!r} 不合法；可用 {ok}')
        key = (full, tuple(sorted(vals.items())))
        if key not in self.lookup:
            self.lookup[key] = len(self.pal)
            self.pal.append((full, vals))
            self.names.append(full[10:])
        return self.lookup[key]

    def name(self, x, y, z):
        return self.names[self.a[x, y, z]]

    def inb(self, x, y, z):
        return 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]

    def put(self, x, y, z, b, keep=False):
        """越界靜默忽略；keep=True 只在空氣處放。"""
        if 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]:
            if keep and self.a[x, y, z] != 0:
                return
            self.a[x, y, z] = b

    def get(self, x, y, z):
        if 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]:
            return int(self.a[x, y, z])
        return 0

    def box(self, x0, y0, z0, x1, y1, z1, b):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        x0 = max(x0, 0); y0 = max(y0, 0); z0 = max(z0, 0)
        self.a[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = b

    def mix(self, *pairs):
        """mix((blk,weight),...) -> 取樣函式"""
        blks = [p[0] for p in pairs]; ws = [p[1] for p in pairs]
        return lambda: self.rng.choices(blks, ws)[0]

    def top(self, x, z, y_from=None):
        """該欄最高非空氣方塊的 y；沒有回 -1"""
        col = self.a[x, :, z]
        nz = np.nonzero(col)[0]
        return int(nz[-1]) if len(nz) else -1

    # ---------- 方向性方塊 ----------
    def stairs(self, mat, asc, upside=False):
        return self.B(mat, weirdo_direction={'e': 0, 'w': 1, 's': 2, 'n': 3}[asc], upside_down_bit=upside)

    def slab(self, mat, top=False):
        return self.B(mat, vertical_half='top' if top else 'bottom')

    def trapdoor(self, mat, d, open=True, top=False):
        return self.B(mat, direction={'e': 0, 'w': 1, 's': 2, 'n': 3}[d], open_bit=open, upside_down_bit=top)

    def log(self, mat, axis='y'):
        return self.B(mat, pillar_axis=axis)

    def door(self, x, y, z, mat, out, hinge=False):
        cd = {'s': 'east', 'w': 'south', 'n': 'west', 'e': 'north'}[out]
        self.put(x, y, z, self.B(mat, cardinal_direction=cd, upper_block_bit=False, door_hinge_bit=hinge))
        self.put(x, y + 1, z, self.B(mat, cardinal_direction=cd, upper_block_bit=True, door_hinge_bit=hinge))

    def bed(self, x, y, z, head, color='red'):
        """(x,y,z) 是床頭格，床尾在 head 的反方向。"""
        d = {'s': 0, 'w': 1, 'n': 2, 'e': 3}[head]
        dx, dz = DIRS[OPP[head]]
        self.put(x, y, z, self.B('bed', direction=d, head_piece_bit=True))
        self.put(x + dx, y, z + dz, self.B('bed', direction=d, head_piece_bit=False))

    def ladder(self, facing):
        return self.B('ladder', facing_direction={'n': 2, 's': 3, 'w': 4, 'e': 5}[facing])

    def facing(self, mat, d):
        return self.B(mat, cardinal_direction=FULL[d])

    def lantern(self, hanging=False, soul=False):
        return self.B('soul_lantern' if soul else 'lantern', hanging=hanging)

    # ---------- 連接狀態 ----------
    def auto_connect(self):
        X, Y, Z = self.size
        npal = len(self.pal)
        NONSOLID = ('air', '_pane', '_bars', '_wall', 'fence', 'carpet', 'torch', 'lantern', 'candle', 'flower', 'sapling',
                    'grass', 'fern', 'water', 'lava', 'rail', 'vine', 'button', 'pressure_plate', 'snow_layer', 'waterlily',
                    'pot', 'petals', 'lichen', 'slab', 'stairs', 'trapdoor', 'door', 'ladder', 'leaves', 'chain', 'bed',
                    'sign', 'banner', 'poppy', 'dandelion', 'tulip', 'orchid', 'allium', 'daisy', 'cornflower', 'bush',
                    'kelp', 'seagrass', 'wheat', 'carrots', 'potatoes', 'beetroot', 'campfire', 'bell', 'lever', 'rod',
                    'azalea', 'lilac', 'rose', 'peony', 'sunflower', 'scaffolding', 'cauldron', 'anvil', 'grindstone',
                    'lectern', 'chest', 'hopper', 'coral', 'pickle', 'dripleaf', 'roots', 'head', 'skull', 'cake', 'sugar_cane',
                    'bamboo', 'cactus', 'deadbush', 'web', 'azure', 'lily', 'composter')
        names = self.names
        solid = np.array([not any(s in n for s in NONSOLID) or n in ('grass_block', 'dirt_with_roots', 'azalea_leaves_x') for n in names] + [False] * 4096)
        solid[0] = False
        linkable = np.array([any(s in n for s in ('_pane', '_bars')) or n.endswith('_wall') for n in names] + [False] * 4096)
        fence = np.array([n.endswith('_fence') or n.endswith('_fence_gate') for n in names] + [False] * 4096)
        isconn = np.array([any(k.startswith('minecraft:connection_') or k.startswith('wall_connection_type_') for k in st) for _, st in self.pal])
        isfence = np.array([n.endswith('_fence') for n in names])
        iswall = np.array([n.endswith('_wall') for n in names])
        xs, ys, zs = np.nonzero(isconn[self.a])
        changed = 0
        a = self.a
        for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
            k = int(a[x, y, z]); name, st = self.pal[k]
            new = dict(st)
            fz = isfence[k]; wl = iswall[k]
            links = 0
            for d, (dx, dz) in (('east', (1, 0)), ('west', (-1, 0)), ('south', (0, 1)), ('north', (0, -1))):
                nx, nz = x + dx, z + dz
                nk = int(a[nx, y, nz]) if 0 <= nx < X and 0 <= nz < Z else 0
                if fz:
                    link = bool(solid[nk] or fence[nk])
                elif wl:
                    link = bool(solid[nk] or linkable[nk] or fence[nk] and names[nk].endswith('gate'))
                else:
                    link = bool(solid[nk] or linkable[nk])
                if 'minecraft:connection_' + d in st:
                    new['minecraft:connection_' + d] = link
                else:
                    ab = int(a[x, y + 1, z]) if y + 1 < Y else 0
                    new['wall_connection_type_' + d] = ('tall' if (solid[ab] or linkable[ab]) else 'short') if link else 'none'
                links += link
            if 'wall_post_bit' in st:
                ew = new['wall_connection_type_east'] != 'none' and new['wall_connection_type_west'] != 'none'
                ns = new['wall_connection_type_north'] != 'none' and new['wall_connection_type_south'] != 'none'
                ab = int(a[x, y + 1, z]) if y + 1 < Y else 0
                new['wall_post_bit'] = not ((ew and links == 2) or (ns and links == 2)) or bool(solid[ab]) or (ab != 0 and not linkable[ab])
            if new != st:
                a[x, y, z] = self.B(name, **new); changed += 1
        return changed

    # ---------- 統計 ----------
    def stats(self, skip=()):
        cnt = np.bincount(self.a.ravel(), minlength=len(self.pal))
        by = {}
        for i, c in enumerate(cnt):
            if i and c:
                by[self.names[i]] = by.get(self.names[i], 0) + int(c)
        tot = sum(v for k, v in by.items() if k not in skip)
        top = sorted(((k, v) for k, v in by.items() if k not in skip), key=lambda kv: -kv[1])[:8]
        return {'distinct': len(by), 'variants': len(self.pal) - 1, 'placed': sum(by.values()),
                'top': [(k, v, round(v / tot, 3)) for k, v in top]}

    # ---------- NBT ----------
    def part_bytes(self, x0, z0, w=64, d=64, origin=(0, 0, 0)):
        sub = self.a[x0:x0 + w, :, z0:z0 + d]
        sw = self.w2[x0:x0 + w, :, z0:z0 + d]
        used = np.unique(sub)
        water = self.B('water')
        remap = np.zeros(len(self.pal), dtype=np.int32)
        local = []
        for g in used.tolist():
            remap[g] = len(local); local.append(g)
        if sw.any() and water not in local:
            remap[water] = len(local); local.append(water)
        prim = remap[sub].astype('<i4')
        sec = np.where(sw & (sub != water), remap[water], -1).astype('<i4')
        size = (sub.shape[0], sub.shape[1], sub.shape[2])
        out = bytearray()
        def s(v):
            b = v.encode('utf8'); return struct.pack('<H', len(b)) + b
        def tag(t, name):
            return bytes([t]) + s(name)
        def ilist(name, arr):
            return tag(9, name) + bytes([3]) + struct.pack('<i', len(arr)) + (arr.tobytes() if isinstance(arr, np.ndarray) else struct.pack('<%di' % len(arr), *arr))
        out += tag(10, '')
        out += tag(3, 'format_version') + struct.pack('<i', 1)
        out += ilist('size', list(size))
        out += tag(10, 'structure')
        out += tag(9, 'block_indices') + bytes([9]) + struct.pack('<i', 2)
        for arr in (prim, sec):
            flat = np.ascontiguousarray(arr).ravel()      # x*(Y*Z)+y*Z+z
            out += bytes([3]) + struct.pack('<i', flat.size) + flat.tobytes()
        out += tag(9, 'entities') + bytes([10]) + struct.pack('<i', 0)
        out += tag(10, 'palette') + tag(10, 'default')
        out += tag(9, 'block_palette') + bytes([10]) + struct.pack('<i', len(local))
        for g in local:
            name, st = self.pal[g]
            out += tag(8, 'name') + s(name)
            out += tag(10, 'states')
            for k, v in st.items():
                if isinstance(v, bool):
                    out += tag(1, k) + bytes([int(v)])
                elif isinstance(v, int):
                    out += tag(3, k) + struct.pack('<i', v)
                else:
                    out += tag(8, k) + s(v)
            out += b'\x00'
            out += tag(3, 'version') + struct.pack('<i', BLOCK_VERSION)
            out += b'\x00'
        out += tag(10, 'block_position_data') + b'\x00'
        out += b'\x00'      # default
        out += b'\x00'      # palette
        out += b'\x00'      # structure
        out += ilist('structure_world_origin', list(origin))
        out += b'\x00'
        return bytes(out), size, len(local)


def parse_nbt(raw):
    """極簡 little-endian NBT 解析（驗證用）。回傳 dict/list/純量；int list 回 numpy。"""
    pos = 0
    def rd(fmt):
        nonlocal pos
        v = struct.unpack_from('<' + fmt, raw, pos); pos += struct.calcsize('<' + fmt); return v[0]
    def rs():
        nonlocal pos
        n = rd('H'); v = raw[pos:pos + n].decode('utf8'); pos += n; return v
    def payload(t):
        nonlocal pos
        if t == 1: return ('b', rd('b'))
        if t == 2: return rd('h')
        if t == 3: return rd('i')
        if t == 4: return rd('q')
        if t == 5: return rd('f')
        if t == 6: return rd('d')
        if t == 8: return rs()
        if t == 9:
            et = rd('B'); n = rd('i')
            if et == 3:
                v = np.frombuffer(raw, dtype='<i4', count=n, offset=pos); pos += 4 * n; return v
            return [payload(et) for _ in range(n)]
        if t == 10:
            d = {}
            while True:
                tt = rd('B')
                if tt == 0: return d
                k = rs(); d[k] = payload(tt)
        raise ValueError('tag %d' % t)
    t = rd('B'); assert t == 10; rs()
    root = payload(10)
    assert pos == len(raw), '尾端有多餘位元組'
    return root


def fbm(shape, scale, seed, octaves=4):
    """值雜訊 fBm，回傳約 [-1,1]。"""
    rs = np.random.RandomState(seed)
    out = np.zeros(shape); amp = 1.0; tot = 0
    X, Z = shape
    for o in range(octaves):
        sc = scale / (2 ** o)
        gx, gz = int(X / sc) + 3, int(Z / sc) + 3
        g = rs.rand(gx, gz) * 2 - 1
        xs = np.arange(X) / sc; zs = np.arange(Z) / sc
        xi = xs.astype(int); zi = zs.astype(int)
        xf = xs - xi; zf = zs - zi
        xf = xf * xf * (3 - 2 * xf); zf = zf * zf * (3 - 2 * zf)
        a = g[np.ix_(xi, zi)]; b = g[np.ix_(xi + 1, zi)]; c = g[np.ix_(xi, zi + 1)]; d = g[np.ix_(xi + 1, zi + 1)]
        v = (a * (1 - xf)[:, None] + b * xf[:, None]) * (1 - zf)[None, :] + (c * (1 - xf)[:, None] + d * xf[:, None]) * zf[None, :]
        out += v * amp; tot += amp; amp *= 0.5
    return out / tot


class Frame:
    """局部座標→世界座標（含 90° 旋轉）。局部正面＝南（+z）。rot=0..3 代表正面朝 s/w/n/e。"""
    def __init__(self, W, ox, oy, oz, w, d, front='s'):
        self.W, self.ox, self.oy, self.oz, self.w, self.d = W, ox, oy, oz, w, d
        self.front = front
        self.r = {'s': 0, 'w': 1, 'n': 2, 'e': 3}[front]

    def footprint(self):
        return (self.w, self.d) if self.r % 2 == 0 else (self.d, self.w)

    def xz(self, lx, lz):
        w, d, r = self.w, self.d, self.r
        if r == 0: x, z = lx, lz
        elif r == 1: x, z = d - 1 - lz, lx
        elif r == 2: x, z = w - 1 - lx, d - 1 - lz
        else: x, z = lz, w - 1 - lx
        return self.ox + x, self.oz + z

    def D(self, d):
        """局部方向字母→世界方向字母"""
        return ORDER[(ORDER.index(d) + self.r) % 4]

    def axis(self, ax):
        if ax == 'y' or self.r % 2 == 0: return ax
        return 'z' if ax == 'x' else 'x'

    def put(self, lx, ly, lz, b, keep=False):
        x, z = self.xz(lx, lz); self.W.put(x, self.oy + ly, z, b, keep)

    def get(self, lx, ly, lz):
        x, z = self.xz(lx, lz); return self.W.get(x, self.oy + ly, z)

    def box(self, x0, y0, z0, x1, y1, z1, b):
        fn = b if callable(b) else (lambda: b)
        for lx in range(min(x0, x1), max(x0, x1) + 1):
            for lz in range(min(z0, z1), max(z0, z1) + 1):
                x, z = self.xz(lx, lz)
                for ly in range(min(y0, y1), max(y0, y1) + 1):
                    self.W.put(x, self.oy + ly, z, fn())

    def stairs(self, lx, ly, lz, mat, asc, upside=False):
        self.put(lx, ly, lz, self.W.stairs(mat, self.D(asc), upside))

    def trapdoor(self, lx, ly, lz, mat, d, open=True, top=False):
        self.put(lx, ly, lz, self.W.trapdoor(mat, self.D(d), open, top))

    def door(self, lx, ly, lz, mat, out, hinge=False):
        x, z = self.xz(lx, lz); self.W.door(x, self.oy + ly, z, mat, self.D(out), hinge)

    def bed(self, lx, ly, lz, head, color='red'):
        x, z = self.xz(lx, lz); self.W.bed(x, self.oy + ly, z, self.D(head), color)

    def ladder(self, lx, ly, lz, facing):
        self.put(lx, ly, lz, self.W.ladder(self.D(facing)))

    def facing(self, lx, ly, lz, mat, d):
        self.put(lx, ly, lz, self.W.facing(mat, self.D(d)))

    def log(self, lx, ly, lz, mat, axis='y'):
        self.put(lx, ly, lz, self.W.log(mat, self.axis(axis)))
