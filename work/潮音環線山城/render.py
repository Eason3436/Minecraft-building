"""等角渲染：只畫外露方塊，依深度排序後一次寫入。"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

COL = [  # (關鍵字, RGB) 先比對先贏
 ('water', (58, 120, 190)), ('grass_block', (104, 160, 72)), ('moss', (92, 130, 52)), ('podzol', (106, 80, 44)),
 ('coarse_dirt', (120, 90, 62)), ('farmland', (86, 58, 36)), ('dirt', (134, 96, 67)), ('red_sandstone', (196, 108, 40)), ('sandstone', (222, 210, 164)),
 ('sand', (226, 216, 172)), ('gravel', (136, 130, 128)), ('clay', (160, 166, 178)), ('calcite', (226, 228, 224)),
 ('raw_gold', (222, 170, 50)), ('deepslate_gold_ore', (150, 130, 70)), ('gold_ore', (200, 170, 90)), ('gold_block', (246, 208, 62)),
 ('deepslate', (74, 74, 80)), ('tuff', (110, 112, 104)), ('polished_andesite', (140, 144, 142)), ('andesite', (134, 136, 136)), ('mossy', (112, 126, 100)),
 ('cobblestone', (126, 126, 126)), ('cracked_stone', (118, 118, 118)), ('stone_brick', (124, 124, 124)), ('smooth_stone', (160, 160, 160)), ('mud_brick', (140, 104, 80)),
 ('nether_brick', (70, 30, 34)), ('brick', (154, 88, 70)), ('granite', (160, 110, 92)), ('diorite', (196, 196, 198)), ('quartz', (236, 232, 224)),
 ('white_terracotta', (212, 180, 162)), ('yellow_terracotta', (190, 136, 40)), ('orange_terracotta', (166, 86, 40)), ('pink_terracotta', (166, 80, 80)),
 ('red_terracotta', (146, 62, 48)), ('light_blue_terracotta', (116, 110, 140)), ('lime_terracotta', (106, 120, 54)), ('green_terracotta', (78, 84, 44)),
 ('brown_terracotta', (80, 52, 38)), ('cyan_terracotta', (88, 92, 92)), ('light_gray_terracotta', (136, 108, 98)), ('magenta_terracotta', (150, 90, 110)),
 ('hardened_clay', (154, 96, 70)),
 ('white_concrete', (210, 214, 216)), ('yellow_concrete', (240, 176, 22)), ('pink_concrete', (214, 102, 144)), ('light_blue_concrete', (38, 138, 200)),
 ('orange_concrete', (226, 98, 2)), ('red_concrete', (144, 34, 34)), ('black_concrete', (12, 14, 18)), ('gray_concrete', (56, 58, 62)), ('lime_concrete', (96, 170, 26)),
 ('white_wool', (236, 238, 238)), ('red_wool', (164, 40, 36)), ('yellow_wool', (250, 200, 40)), ('blue_wool', (54, 58, 160)), ('light_blue_wool', (60, 176, 220)),
 ('orange_wool', (242, 120, 22)), ('green_wool', (86, 112, 28)), ('lime_wool', (114, 186, 26)), ('pink_wool', (238, 144, 174)), ('wool', (200, 200, 200)),
 ('azalea_leaves_flowered', (150, 120, 130)), ('azalea', (94, 124, 44)), ('spruce_leaves', (48, 84, 48)), ('birch_leaves', (104, 140, 70)), ('leaves', (62, 118, 44)),
 ('red_carpet', (190, 60, 50)), ('yellow_carpet', (240, 200, 50)), ('light_blue_carpet', (90, 180, 220)), ('lime_carpet', (120, 190, 40)), ('orange_carpet', (240, 130, 30)), ('pink_carpet', (240, 150, 180)), ('white_carpet', (236, 238, 238)), ('green_carpet', (86, 112, 28)), ('brown_carpet', (110, 72, 44)), ('carpet', (190, 60, 50)), ('stripped_spruce', (116, 90, 52)), ('stripped_dark_oak', (74, 58, 36)), ('stripped_oak', (178, 144, 86)), ('stripped_birch', (198, 176, 118)),
 ('dark_oak', (68, 44, 22)), ('spruce', (116, 86, 50)), ('birch', (196, 180, 124)), ('acacia', (170, 92, 50)), ('mangrove', (118, 54, 48)),
 ('warped', (44, 106, 100)), ('crimson', (102, 48, 70)), ('cherry', (228, 180, 172)), ('jungle', (160, 116, 80)), ('bamboo', (196, 176, 80)),
 ('azalea_leaves_flowered', (124, 130, 92)), ('azalea', (94, 124, 44)), ('leaves', (62, 118, 44)),
 ('oak', (164, 132, 78)), ('planks', (164, 132, 78)), ('trapdoor', (130, 100, 60)), ('wooden_door', (140, 110, 60)), ('bookshelf', (120, 96, 60)),
 ('glowstone', (250, 220, 130)), ('sea_lantern', (200, 236, 226)), ('lantern', (252, 210, 110)), ('redstone_block', (176, 24, 10)), ('golden_rail', (220, 180, 60)),
 ('rail', (150, 138, 120)), ('iron', (200, 200, 200)), ('glass', (180, 214, 230)), ('hay', (200, 170, 40)), ('pumpkin', (220, 130, 30)), ('melon', (120, 160, 40)),
 ('wheat', (210, 190, 80)), ('carrots', (70, 150, 40)), ('potatoes', (60, 150, 60)), ('beetroot', (80, 140, 50)), ('vine', (60, 110, 36)),
 ('poppy', (220, 40, 30)), ('dandelion', (250, 220, 40)), ('tulip', (240, 120, 140)), ('cornflower', (80, 110, 230)), ('allium', (180, 110, 230)), ('daisy', (240, 240, 230)),
 ('lilac', (200, 150, 210)), ('rose', (200, 40, 50)), ('peony', (236, 170, 220)), ('sunflower', (250, 210, 40)), ('azure', (220, 230, 240)), ('orchid', (60, 170, 240)),
 ('short_grass', (110, 170, 76)), ('tall_grass', (110, 170, 76)), ('fern', (90, 150, 70)), ('bush', (70, 130, 50)), ('seagrass', (60, 140, 90)), ('kelp', (70, 130, 60)),
 ('barrel', (130, 96, 56)), ('chest', (160, 110, 40)), ('composter', (120, 80, 40)), ('crafting', (150, 110, 70)), ('furnace', (110, 110, 110)), ('smoker', (100, 96, 90)),
 ('campfire', (230, 150, 50)), ('bell', (240, 200, 60)), ('copper', (190, 108, 80)), ('prismarine', (90, 160, 150)), ('obsidian', (20, 16, 30)), ('coal', (30, 30, 30)),
 ('basalt', (80, 80, 86)), ('blackstone', (40, 36, 42)), ('stone', (128, 128, 128)), ('bed', (170, 50, 50)), ('lectern', (160, 120, 70)), ('loom', (150, 120, 90)),
 ('cauldron', (70, 70, 74)), ('anvil', (70, 70, 70)), ('scaffolding', (200, 170, 90)), ('ladder', (150, 120, 70)), ('pot', (130, 76, 56)), ('candle', (240, 220, 160)),
 ('end_rod', (240, 240, 230)), ('chain', (70, 76, 90)), ('lightning_rod', (200, 120, 90)), ('snow', (245, 250, 250)), ('ice', (150, 190, 250)), ('coral', (220, 90, 130)),
]
FLAT = ('rail', 'carpet', 'pressure_plate', 'petals', 'waterlily', 'snow_layer', 'vine', 'lichen', 'ladder')
SMALL = ('lantern', 'poppy', 'dandelion', 'tulip', 'cornflower', 'allium', 'daisy', 'orchid', 'azure', 'short_grass', 'fern', 'seagrass', 'kelp',
         'fence', '_wall', 'chain', 'pot', 'candle', 'end_rod', 'torch', 'bars', 'lightning_rod', 'bell', 'button', 'lever', 'wheat', 'carrots', 'potatoes',
         'beetroot', 'sapling', 'bush', 'tall_grass', 'lilac', 'rose', 'peony', 'sunflower', 'pane', 'sign', 'banner', 'trapdoor', '_door', 'lever', 'campfire', 'coral_fan', 'deadbush', 'sugar_cane', 'bamboo')
TRANSP = FLAT + SMALL + ('air', 'glass', 'trapdoor', 'door', 'slab', 'stairs', 'leaves', 'water', 'campfire', 'bed', 'anvil', 'cauldron', 'lectern', 'scaffolding', 'chest', 'composter')


def classify(names):
    n = len(names)
    col = np.zeros((n, 3), np.float32); kind = np.zeros(n, np.uint8); opaque = np.zeros(n, bool)
    for i, nm in enumerate(names):
        if nm == 'air':
            continue
        c = (150, 150, 150)
        for k, v in COL:
            if k in nm:
                c = v; break
        col[i] = c
        s = nm
        if any(k in s for k in SMALL) and not s.endswith('_block') and 'grass_block' not in s and 'leaves' not in s and 'rail' not in s:
            kind[i] = 2
        elif any(k in s for k in FLAT):
            kind[i] = 1
        else:
            kind[i] = 3
        opaque[i] = not any(k in s for k in TRANSP) or s in ('grass_block', 'glass_dummy')
    return col, kind, opaque


def render(a, names, path, view='se', floor_y=0, cut_y=None, cut_mask=None, title='', notes='', scale=2, bg=(236, 240, 244), crop=None):
    """a: [x,y,z] 調色盤索引。view: 相機所在方位 se/sw/ne/nw。cut_y: 只畫 y<=cut_y（cut_mask 為 True 的欄）。"""
    a = a.copy()
    if floor_y: a[:, :floor_y, :] = 0
    if cut_y is not None:
        if cut_mask is None:
            a[:, cut_y + 1:, :] = 0
        else:
            sub = a[:, cut_y + 1:, :]; sub[np.broadcast_to(cut_mask[:, None, :], sub.shape)] = 0
    if crop:
        x0, x1, z0, z1 = crop; a = a[x0:x1, :, z0:z1]
    # 轉成相機在 +x,+z（東南）的標準朝向
    if view == 'sw': a = a[::-1]
    elif view == 'ne': a = a[:, :, ::-1]
    elif view == 'nw': a = a[::-1, :, ::-1]
    X, Y, Z = a.shape
    col, kind, opaque = classify(names)
    op = opaque[a]
    nz = a != 0
    pad = np.zeros((X + 1, Y + 1, Z + 1), bool); pad[:X, :Y, :Z] = op
    vt = nz & ~pad[:X, 1:, :Z]          # 上方不遮
    vx = nz & ~pad[1:, :Y, :Z]          # +x 面
    vz = nz & ~pad[:X, :Y, 1:]          # +z 面
    water = np.array([n == 'water' for n in names])[a]
    vx &= ~water; vz &= ~water
    # 水面只畫頂（上方不是水）
    wa = np.zeros((X, Y + 1, Z), bool); wa[:, :Y, :] = water
    vt &= ~(water & wa[:, 1:, :])
    u = 2 * scale; hh = scale
    W_ = (X + Z) * u + 8; H_ = (X + Z) * hh + Y * u + 8
    img = np.zeros((H_, W_, 3), np.float32); img[:] = bg
    px_all = []; py_all = []; c_all = []; d_all = []
    def emit(mask, face):
        xs, ys, zs = np.nonzero(mask)
        if len(xs) == 0: return
        k = a[xs, ys, zs]; kd = kind[k]; c = col[k]
        sx = (xs - zs + Z) * u + 2
        sy = (xs + zs) * hh + (Y - 1 - ys) * u + 2
        depth = (xs + zs + ys).astype(np.int64) * 4
        # 高度陰影
        shade_y = (0.80 + 0.20 * np.clip(ys / 110.0, 0, 1))[:, None]
        if face == 't':
            offs = [(dx, dy) for dy in range(2 * hh) for dx in range(2 * u) if abs((dx + .5) - u) / u + abs((dy + .5) - hh) / hh <= 1.0]
            sh = 1.0
            full = kd == 3
            for dx, dy in offs:
                m = full
                px_all.append(sx[m] - u + dx); py_all.append(sy[m] + dy); c_all.append(c[m] * sh * shade_y[m]); d_all.append(depth[m] + 3)
            # 扁平：畫在格底
            m = kd == 1
            for dx, dy in offs:
                px_all.append(sx[m] - u + dx); py_all.append(sy[m] + dy + u); c_all.append(c[m] * shade_y[m]); d_all.append(depth[m] + 1)
            # 小物：中央小塊
            m = kd == 2
            for dx in range(-scale // 1, scale):
                for dy in range(hh, hh + u + scale):
                    px_all.append(sx[m] + dx); py_all.append(sy[m] + dy); c_all.append(c[m] * (1.0 if dy < hh + scale else 0.8) * shade_y[m]); d_all.append(depth[m] + 2)
        else:
            m = kd == 3
            sh = 0.78 if face == 'z' else 0.62
            for dx in range(u):
                for dy in range(u):
                    if face == 'z':   # 左面（+z）
                        X_ = sx[m] - u + dx; Y_ = sy[m] + hh + dy + (dx * hh) // u
                    else:             # 右面（+x）
                        X_ = sx[m] + dx; Y_ = sy[m] + 2 * hh + dy - ((dx + 1) * hh) // u
                    px_all.append(X_); py_all.append(Y_); c_all.append(c[m] * sh * shade_y[m]); d_all.append(depth[m] + (1 if face == 'z' else 2))
    emit(vz, 'z'); emit(vx, 'x'); emit(vt, 't')
    px = np.concatenate(px_all); py = np.concatenate(py_all); c = np.concatenate(c_all); d = np.concatenate(d_all)
    o = np.argsort(d, kind='stable')
    px, py, c = px[o], py[o], c[o]
    ok = (px >= 0) & (px < W_) & (py >= 0) & (py < H_)
    img[py[ok], px[ok]] = c[ok]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # 裁掉空白
    arr = np.asarray(im); m = np.any(np.abs(arr.astype(int) - np.array(bg)) > 2, axis=2)
    ys_, xs_ = np.nonzero(m)
    if len(xs_):
        im = im.crop((max(xs_.min() - 20, 0), max(ys_.min() - 20, 0), min(xs_.max() + 20, W_), min(ys_.max() + 20, H_)))
    if title or notes:
        font = None
        for f in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                  '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', '/usr/share/fonts/truetype/arphic/uming.ttc'):
            try:
                font = ImageFont.truetype(f, 34); small = ImageFont.truetype(f, 20); break
            except OSError:
                pass
        if font is None:
            font = small = ImageFont.load_default()
        w, h = im.size
        canvas = Image.new('RGB', (w, h + 110), bg); canvas.paste(im, (0, 80))
        dr = ImageDraw.Draw(canvas)
        dr.text((24, 14), title, fill=(30, 40, 60), font=font)
        dr.text((24, h + 80), notes, fill=(70, 80, 90), font=small)
        im = canvas
    im.save(path)
    return im.size
