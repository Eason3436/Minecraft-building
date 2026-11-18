"""最終輸出：連接狀態、檢查、切 9 分件、重新解析驗證、渲染、打包 mcpack。"""
import json, zipfile, shutil, time
from PIL import Image, ImageDraw, ImageFont
from core import *
import gen, render as R, check as C

NAME = '巴比倫空中花園'
FN = 'babylon'
ROOT = HERE.parents[1]
OUT = ROOT / 'structures' / NAME
PARTS = HERE / 'parts'
HEADER_UUID = '7b2e4c91-3f6a-4d85-b0c2-9e1a5d7f3b48'
MODULE_UUID = 'c5d9a1e3-8b47-4f26-a3e5-2f6c8d0b4a97'
VERSION = [1, 0, 0]
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
NOTES = '依方塊資料繪製，非遊戲截圖；樓梯、半磚、藤蔓等以簡化方塊表示；瀑布在遊戲內是流動水，圖中以水柱示意。'


def show_falls(W, srcs):
    a = W.a.copy(); water = W.B('water')
    for x, y, z in srcs:
        for dx, dz in DIRS.values():
            if a[x + dx, y, z + dz] == 0:
                yy = y
                while yy > 0 and a[x + dx, yy, z + dz] == 0:
                    a[x + dx, yy, z + dz] = water; yy -= 1
    return a


def panel(a, names, title, **kw):
    p = HERE / ('_p_%d.png' % (abs(hash(title)) % 10**8))
    R.render(a, names, p, **kw)
    return Image.open(p).convert('RGB'), title


def montage(panels, path, title, notes, cols=2, cell=(1500, 1000), bg=(236, 240, 244)):
    f1 = ImageFont.truetype(FONT, 40); f2 = ImageFont.truetype(FONT, 26); f3 = ImageFont.truetype(FONT, 22)
    rows = (len(panels) + cols - 1) // cols
    Wd, Ht = cols * cell[0], rows * (cell[1] + 50) + 150
    im = Image.new('RGB', (Wd, Ht), bg); dr = ImageDraw.Draw(im)
    dr.text((30, 16), title, fill=(30, 40, 60), font=f1)
    for i, (p, cap) in enumerate(panels):
        r, c = divmod(i, cols)
        p = p.copy(); p.thumbnail((cell[0] - 40, cell[1] - 20), Image.LANCZOS)
        x = c * cell[0] + (cell[0] - p.width) // 2; y = 80 + r * (cell[1] + 50) + 44 + (cell[1] - 20 - p.height) // 2
        dr.text((c * cell[0] + 30, 80 + r * (cell[1] + 50) + 6), cap, fill=(40, 60, 90), font=f2)
        im.paste(p, (x, y))
    dr.text((30, Ht - 54), notes, fill=(70, 80, 90), font=f3)
    im.save(path)
    return im.size


def main():
    t0 = time.time()
    W, srcs = gen.main()
    print('auto_connect', W.auto_connect())
    leaks = C.water_leaks(W, srcs); assert not leaks, leaks[:10]
    seen = C.walk(W, (95, 9, 189))
    targets = {'城門外橋頭': (95, 9, 189), '頂層廣場': (95, 54, 80), '頂層涼亭': (100, 54, 78), 'L0 步道': (60, 18, 120), 'L1 步道': (60, 27, 110),
               'L2 步道': (70, 36, 100), 'L3 步道': (80, 45, 92), 'L4 步道': (95, 54, 73), '拱頂地庫': (75, 9, 85), '王宮中庭': (172, 9, 60), '王座廳': (172, 9, 95),
               '提水塔底': (32, 9, 84), '提水塔頂': (30, 60, 84)}
    walk = {k: bool(seen[v]) for k, v in targets.items()}
    print(walk); assert all(walk.values())
    st = W.stats(skip=('dirt', 'grass_block', 'sandstone', 'sand', 'water', 'packed_mud'))
    print('stats', st)
    assert st['distinct'] >= 40 and st['top'][0][2] <= 0.6
    if PARTS.exists(): shutil.rmtree(PARTS)
    PARTS.mkdir()
    ids = []
    for ix in range(3):
        for iz in range(3):
            raw, size, npal = W.part_bytes(ix * 64, iz * 64)
            pid = f'p_{ix}_{iz}'
            (PARTS / (pid + '.mcstructure')).write_bytes(raw)
            root = parse_nbt(raw)
            assert root['format_version'] == 1 and list(root['size']) == [64, SY, 64]
            bi = root['structure']['block_indices']
            assert len(bi) == 2 and all(len(l) == 64 * SY * 64 for l in bi)
            pal = root['structure']['palette']['default']['block_palette']
            assert len(pal) == npal and int(bi[0].max()) < npal and int(bi[0].min()) >= 0 and int(bi[1].min()) >= -1 and int(bi[1].max()) < npal
            for b in pal:
                assert b['name'] in DEFS and b['version'] == BLOCK_VERSION
            back = np.asarray(bi[0]).reshape(64, SY, 64)
            names_local = np.array([b['name'][10:] for b in pal])
            src = np.array(W.names)[W.a[ix * 64:ix * 64 + 64, :, iz * 64:iz * 64 + 64]]
            assert (names_local[back] == src).all()
            ids.append((pid, ix * 64, iz * 64, len(raw), npal))
    print('parts ok', len(ids), 'bytes', sum(i[3] for i in ids))
    # ---- 渲染 ----
    A = show_falls(W, srcs)
    R.render(A, W.names, HERE / 'overall.png', view='se', scale=3,
             title=f'{NAME}　192 x 192 x 80（9 分件）　東南上空俯視', notes=NOTES)
    P = []
    a2 = A.copy(); a2[77:, :, :] = 0
    P.append(panel(a2, W.names, '梯台縱剖（x=76）：拱頂迴廊、植床土層、地庫拱室', view='se', scale=5, crop=(44, 77, 28, 136), floor_y=5))
    P.append(panel(A, W.names, '拱頂地庫：14 間拱室、三孔井、南北走廊（剖切 y=11）', view='se', scale=7, crop=(56, 95, 66, 125), cut_y=11, floor_y=6))
    P.append(panel(A, W.names, '頂層：蓄水池、渡槽進水口、涼亭與王座（剖切 y=58）', view='se', scale=8, crop=(78, 114, 66, 94), cut_y=58, floor_y=50))
    a3 = A.copy(); a3[:, :, 81:] = 0
    P.append(panel(a3, W.names, '鏈斗提水塔縱剖（z=80）：上下木輪、鐵鏈與水斗、集水井', view='se', scale=6, crop=(18, 50, 70, 81), floor_y=0))
    P.append(panel(A, W.names, '王宮：中庭、房間與王座廳（剖切 y=14，藍釉立面、雪松柱、王座）', view='se', scale=5, crop=(150, 192, 26, 128), cut_y=14, floor_y=6))
    P.append(panel(A, W.names, '伊什塔爾門與遊行大道：藍釉磚、公牛與龍浮雕、獅子牆', view='se', scale=5, crop=(76, 116, 126, 192), floor_y=2))
    montage(P, HERE / 'interior.png', f'{NAME}　內部剖視與結構細節', NOTES, cols=3, cell=(1200, 950))
    # ---- 打包 ----
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir(): f.unlink()
    tick = [f'tickingarea add ~{i * 64} ~ ~0 ~{i * 64 + 63} ~{SY - 1} ~191 {FN}{i} true' for i in range(3)]
    fun = {
        'prepare': tick,
        'build': [f'structure load {NAMESPACE}:{pid} ~{ox} ~ ~{oz}' for pid, ox, oz, _, _ in ids],
        'cleanup': [f'tickingarea remove {FN}{i}' for i in range(3)],
        'life': ['summon cow ~40 ~9 ~95', 'summon villager ~95 ~9 ~140', 'summon villager ~60 ~18 ~122', 'summon villager ~120 ~27 ~113', 'summon villager ~172 ~9 ~55',
                 'summon villager ~100 ~54 ~79', 'summon parrot ~95 ~60 ~78', 'summon parrot ~70 ~30 ~60', 'summon parrot ~120 ~40 ~100', 'summon camel ~95 ~9 ~180',
                 'summon camel ~50 ~9 ~140', 'summon boat ~15 ~8 ~60', 'summon boat ~12 ~8 ~110', 'summon tropicalfish ~15 ~5 ~90', 'summon cat ~172 ~9 ~60'],
        'view': ['tp @s ~210 ~95 ~215 facing ~95 ~30 ~85'],
        'gate': ['tp @s ~95 ~9 ~190 facing ~95 ~25 ~170'],
        'way': ['tp @s ~95 ~9 ~148 facing ~95 ~30 ~110'],
        'garden': ['tp @s ~95 ~18 ~124 facing ~95 ~40 ~90'],
        'top': ['tp @s ~95 ~54 ~84 facing ~100 ~56 ~76'],
        'gallery': ['tp @s ~70 ~18 ~115 facing ~80 ~19 ~115'],
        'crypt': ['tp @s ~75 ~9 ~85 facing ~65 ~10 ~85'],
        'tower': ['tp @s ~42 ~9 ~92 facing ~32 ~40 ~80'],
        'aqueduct': ['tp @s ~60 ~60 ~84 facing ~40 ~56 ~80'],
        'palace': ['tp @s ~172 ~9 ~45 facing ~172 ~14 ~80'],
        'throne': ['tp @s ~172 ~9 ~84 facing ~172 ~11 ~102'],
        'screw': ['tp @s ~38 ~11 ~15 facing ~26 ~7 ~10'],
    }
    desc = '依史料與常見復原圖還原的巴比倫空中花園：五層拱廊梯台、層層植栽與垂藤、鏈斗提水塔與渡槽、阿基米德螺旋、拱頂地庫，周邊伊什塔爾門、遊行大道、城牆護城河、南宮王座廳與民宅。192×192×80，9 分件。'
    manifest = {'format_version': 2, 'header': {'name': NAME, 'description': desc, 'uuid': HEADER_UUID, 'version': VERSION, 'min_engine_version': [1, 26, 60]},
                'modules': [{'type': 'data', 'uuid': MODULE_UUID, 'version': VERSION}]}
    mc = OUT / (NAME + '.mcpack')
    with zipfile.ZipFile(mc, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        for k, lines in fun.items(): z.writestr(f'functions/{FN}/{k}.mcfunction', '\n'.join(lines) + '\n')
        for pid, *_ in ids: z.write(PARTS / (pid + '.mcstructure'), f'structures/{NAMESPACE}/{pid}.mcstructure')
    with zipfile.ZipFile(mc) as z:
        assert z.testzip() is None
        for pid, *_ in ids:
            assert z.read(f'structures/{NAMESPACE}/{pid}.mcstructure') == (PARTS / (pid + '.mcstructure')).read_bytes()
    shutil.copyfile(HERE / 'overall.png', OUT / (NAME + '_整體渲染.png'))
    shutil.copyfile(HERE / 'interior.png', OUT / (NAME + '_內部剖視.png'))
    json.dump(dict(walk=walk, stats=st, parts=ids, funcs=list(fun), cascades=len(srcs), trunks=len(gen.TRUNKS)), open(HERE / 'report.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('mcpack', mc.stat().st_size, 'done', round(time.time() - t0, 1), 'cascades', len(srcs), 'trees', len(gen.TRUNKS))


if __name__ == '__main__':
    main()
