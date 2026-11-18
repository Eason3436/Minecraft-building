"""產出 80 件、檢查、渲染、打包。"""
import json, zipfile, shutil, time, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gen import *
from core import parse_nbt
from check import check_piece
import render as R

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
NAME = '生態系車站合集'
NS = 'biomesta_261118'
FN = 'bst'
OUT = ROOT / 'structures' / NAME
PARTS = HERE / 'parts'
HEADER_UUID = '6c1f2a3e-8b47-4d1a-9f60-2e7b5c4d8a13'
MODULE_UUID = 'b2d94e71-3a5c-4f08-8e26-71c0a9f3d5b4'
VERSION = [1, 0, 0]
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
ORDER = ['ug_station', 'ug_track', 'ramp', 'el_track', 'el_station']
OFFS = {}
_x = 0
for k in ORDER:
    OFFS[k] = _x; _x += KINDS[k]
LINE_L = _x       # 112
ROW = 16
NOTE = '依方塊資料繪製，非遊戲截圖；樓梯、半磚、柵欄、植物等以簡化方塊表示。'


def combine(pcs, gap=ROW):
    idx = {}
    A = np.zeros((LINE_L, H, WZ), np.int32)
    for k in ORDER:
        p = pcs[k]
        m = np.array([idx.setdefault(n, len(idx)) for n in p.W.names])
        A[OFFS[k]:OFFS[k] + p.L] = m[p.W.a]
    names = [None] * len(idx)
    for n, i in idx.items(): names[i] = n
    return A, names


def montage(panels, path, title, cols, cell):
    f1 = ImageFont.truetype(FONT, 46); f2 = ImageFont.truetype(FONT, 30); f3 = ImageFont.truetype(FONT, 24)
    rows = (len(panels) + cols - 1) // cols
    Wd, Ht = cols * cell[0], rows * (cell[1] + 50) + 170
    im = Image.new('RGB', (Wd, Ht), (236, 240, 244)); dr = ImageDraw.Draw(im)
    dr.text((30, 18), title, fill=(30, 40, 60), font=f1)
    for i, (p, cap) in enumerate(panels):
        r, c = divmod(i, cols)
        p = p.copy(); p.thumbnail((cell[0] - 30, cell[1] - 10), Image.LANCZOS)
        y0 = 96 + r * (cell[1] + 50)
        dr.text((c * cell[0] + 24, y0), cap, fill=(40, 60, 90), font=f2)
        im.paste(p, (c * cell[0] + (cell[0] - p.width) // 2, y0 + 44 + (cell[1] - 10 - p.height) // 2))
    dr.text((30, Ht - 56), NOTE, fill=(70, 80, 90), font=f3)
    im.save(path, optimize=True)
    return im.size


def rimg(a, names, **kw):
    p = HERE / '_r.png'
    R.render(a, names, p, **kw)
    return Image.open(p).convert('RGB')


def main():
    t0 = time.time()
    if PARTS.exists(): shutil.rmtree(PARTS)
    PARTS.mkdir()
    allp = {}
    report = {}
    for b in BIOMES:
        pcs = {}
        for k in ORDER:
            pc = build_piece(b, k)
            e = check_piece(pc)
            assert not e, (b['id'], k, e[:5])
            st = pc.W.stats(skip=('stone', 'dirt', 'sandstone', 'netherrack', 'water', 'mud', 'hardened_clay', 'orange_terracotta',
                                  'yellow_terracotta', 'white_terracotta', 'red_terracotta', 'brown_terracotta', 'sand'))
            raw, void, local = piece_bytes(pc)
            sid = f"{b['id']}_{k}"
            (PARTS / (sid + '.mcstructure')).write_bytes(raw)
            root = parse_nbt(raw)
            X = pc.L
            assert root['format_version'] == 1 and list(root['size']) == [X, H, WZ]
            bi = root['structure']['block_indices']
            pal = root['structure']['palette']['default']['block_palette']
            assert len(bi) == 2 and all(len(l) == X * H * WZ for l in bi)
            assert int(bi[0].max()) < len(pal) and int(bi[0].min()) >= -1 and int(bi[1].max()) < len(pal)
            for p in pal: assert p['name'] in DEFS and p['version'] == BLOCK_VERSION
            back = np.asarray(bi[0]).reshape(X, H, WZ)
            nl = np.array([p['name'][10:] for p in pal] + ['air'])
            src = np.array(pc.W.names)[pc.W.a]
            assert (nl[back] == src).all()
            assert ((back == -1) == void).all()
            pcs[k] = pc
            report[sid] = dict(bytes=len(raw), palette=len(pal), distinct=st['distinct'], top=st['top'][:3])
        allp[b['id']] = pcs
        print(b['id'], 'ok', round(time.time() - t0, 1))
    # ---- 渲染 ----
    panels = []
    for b in BIOMES:
        A, names = combine(allp[b['id']])
        panels.append((rimg(A, names, view='sw', scale=4), f"{b['zh']}　示範線（地下站→隧道→坡道→高架→高架站）"))
    montage(panels, HERE / 'overall.png', f'{NAME}　16 生態系 × 5 模組（每件寬 13、高 30；全線 112 格）　西南上空', cols=4, cell=(1150, 640))
    ip = []
    for b in BIOMES:
        pcs = allp[b['id']]
        ip.append((rimg(pcs['ug_station'].W.a, pcs['ug_station'].W.names, view='se', scale=9, cut_y=5),
                   f"{b['zh']}　地下車站（剖去天花板）"))
        ip.append((rimg(pcs['el_station'].W.a, pcs['el_station'].W.names, view='se', scale=9, cut_y=19),
                   f"{b['zh']}　高架車站（剖去屋頂）"))
    montage(ip, HERE / 'interior.png', f'{NAME}　車站內部剖視（島式月台、長椅花台、樓梯、拉桿停車段）', cols=4, cell=(1000, 640))
    # ---- function ----
    fun = {}
    def line_cmds(bid, dy, row_z=0):
        L = [f'structure load {NS}:{bid}_{k} ~{OFFS[k]} ~{dy} ~{row_z}' for k in ORDER]
        stop = 'stone_bricks'
        for z in ZR:
            L.append(f'setblock ~-1 ~{dy + YU} ~{row_z + z} {stop}')
            L.append(f'setblock ~{LINE_L} ~{dy + YE} ~{row_z + z} {stop}')
        if BYID[bid].get('ocean'):
            L.append(f'fill ~-1 ~{dy + 7} ~{row_z + 1} ~-1 ~{dy + 9} ~{row_z + 11} sand')
            L.append(f'fill ~{LINE_L} ~{dy + 7} ~{row_z + 1} ~{LINE_L} ~{dy + 9} ~{row_z + 11} sand')
        return L
    for b in BIOMES:
        bid = b['id']
        fun[bid] = line_cmds(bid, 0)
        fun[bid + '_embed'] = line_cmds(bid, -10)
        for k in ORDER:
            fun[f'{bid}/{k}'] = [f'structure load {NS}:{bid}_{k} ~ ~ ~']
    gal = []
    for i, b in enumerate(BIOMES):
        gal += line_cmds(b['id'], 0, i * ROW)
    fun['gallery'] = gal
    fun['gallery_prepare'] = [f'tickingarea add ~-1 ~ ~ ~{LINE_L} ~{H} ~{8 * ROW - 1} {FN}a true',
                              f'tickingarea add ~-1 ~ ~{8 * ROW} ~{LINE_L} ~{H} ~{16 * ROW - 1} {FN}b true']
    fun['gallery_cleanup'] = [f'tickingarea remove {FN}a', f'tickingarea remove {FN}b']
    # ---- 打包 ----
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir(): f.unlink()
    desc = '16 個生態系各一座高架車站與地下車站，加上同風格的隧道段、高架段與升降坡道；全部共用斷面，可任意串接。'
    manifest = {'format_version': 2, 'header': {'name': NAME, 'description': desc, 'uuid': HEADER_UUID, 'version': VERSION, 'min_engine_version': [1, 26, 60]},
                'modules': [{'type': 'data', 'uuid': MODULE_UUID, 'version': VERSION}]}
    mc = OUT / (NAME + '.mcpack')
    with zipfile.ZipFile(mc, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        for k, lines in fun.items(): z.writestr(f'functions/{FN}/{k}.mcfunction', '\n'.join(lines) + '\n')
        for p in sorted(PARTS.iterdir()): z.write(p, f'structures/{NS}/{p.name}')
    with zipfile.ZipFile(mc) as z:
        assert z.testzip() is None
        for p in PARTS.iterdir():
            assert z.read(f'structures/{NS}/{p.name}') == p.read_bytes()
    shutil.copyfile(HERE / 'overall.png', OUT / (NAME + '_整體渲染.png'))
    shutil.copyfile(HERE / 'interior.png', OUT / (NAME + '_內部剖視.png'))
    (OUT / (NAME + '_使用說明.txt')).write_text(txt(), encoding='utf-8-sig')
    assert len(list(OUT.iterdir())) == 4
    json.dump(report, open(HERE / 'report.json', 'w'), ensure_ascii=False, indent=1)
    print('done', mc.stat().st_size, round(time.time() - t0, 1))


FEATURE = {
 'plains': '石砌橋墩＋橡木柱、雲杉山形屋頂、黃色月台邊線；地面草花、橡樹。',
 'desert': '切製砂岩、平頂加天窗、橘陶瓦月台邊；仙人掌、枯灌木。',
 'snowy': '雲杉木構、階梯式積雪屋頂、浮冰壁帶與海燈籠；積雪地面、雪杉。',
 'jungle': '苔石遺跡風、竹編屋頂上覆叢林樹葉、橋墩爬滿藤蔓；可可樹、竹子、西瓜。',
 'taiga': '圓石與雲杉、深色橡木屋頂；灰化土、甜莓叢、雲杉。',
 'birch': '閃長岩白牆、樺木柱、氧化銅綠屋頂（已上蠟不會再變色）；鈴蘭、樺樹。',
 'darkforest': '深板岩圓石、黑橡木、深板岩瓦屋頂、樺木腰帶；巨型紅蘑菇、黑橡樹。',
 'swamp': '泥磚、雲杉木地板、苔石磚屋頂；水窪與睡蓮、藍色蘭花、垂藤橡樹。',
 'mangrove': '泥磚與紅樹林木、懸根垂掛甲板下；泥地、紅樹林胎生苗、氣根樹。',
 'savanna': '赤陶與金合歡木、低坡屋頂；乾草堆、金合歡樹。',
 'badlands': '紅砂岩、平頂天窗、地層是彩色陶瓦條紋（在路塹剖面看得到）；仙人掌、枯灌木。',
 'mushroom': '蘑菇柄柱、紅蘑菇圓頂屋頂、菌光燈；菌絲地面、巨型紅／棕蘑菇。',
 'ocean': '海磷石、玻璃拱頂；地下段是「海底玻璃隧道」，上方就是海水；高架橋墩立在海中，出入口亭蓋在海上平台。',
 'cherry': '方解石白牆、櫻花木柱、深板岩瓦翹簷和風屋頂；粉紅花瓣、櫻花樹。',
 'palegarden': '凝灰岩磚與蒼白橡木、樹脂磚屋頂；蒼白苔蘚、眼眸花、垂掛蒼白苔蘚。',
 'nether': '磨製黑石磚、緋紅木、紅地獄磚屋頂、靈魂燈籠；緋紅菌岩、緋紅蕈與垂淚藤。',
}


def txt():
    rows = []
    for b in BIOMES:
        rows.append(f"【{b['zh']}】{FEATURE[b['id']]}")
        for k in ORDER:
            rows.append(f"  {b['zh']}{KIND_ZH[k]}　{NS}:{b['id']}_{k}　（{KINDS[k]}×{H}×{WZ}）")
        rows.append(f"  一鍵載入整條示範線：/function {FN}/{b['id']}（平放）　/function {FN}/{b['id']}_embed（嵌入地面）")
        rows.append('')
    biome_block = '\n'.join(rows)
    return f"""{NAME}　使用說明
================================

【這是什麼】
Minecraft 16 個生態系，每個生態系各一座「高架車站」與「地下車站」，再加上同風格的
「隧道段」「高架段」和「升降坡道」（把地下鐵路接到高架），一共 80 個小模組。
每件都只有 13 格寬，放置很方便；所有模組共用同一個斷面，可以照自己的需求任意串接。
可用建築放置台放置。

【每個生態系的 5 個模組】（寬 X × 高 Y × 深 Z）
・地下車站　_ug_station　24 × 30 × 13：島式月台、長椅花台、壁燈與壁柱、樓梯上到地面出入口亭。
・隧道段　　_ug_track　　16 × 30 × 13：雙線隧道，每 8 格一道拱圈、中央立柱與壁燈；地表有該生態系的樹和花草。
・升降坡道　_ramp　　　　32 × 30 × 13：西端接隧道（軌面低），經洞口、路塹、路堤，東端接高架（軌面高），共升 15 格。
・高架段　　_el_track　　16 × 30 × 13：橋墩＋拱腋、護欄、門型架與吊燈。
・高架車站　_el_station　24 × 30 × 13：島式月台、依生態系變化的屋頂、側窗、月台中央樓梯下到橋下廣場。

【接合規則（自己串接時看這裡）】
・軌道沿 X 方向（東西向），兩條軌道在 z=2 與 z=10，兩件只要 z 對齊、x 首尾相接就能接上。
・地下軌道高度 y=2，高架軌道高度 y=17（結構內座標）；坡道的西端是地下高度、東端是高架高度。
・示範線的順序（西→東）：地下車站(x0) → 隧道段(x24) → 升降坡道(x40) → 高架段(x72) → 高架車站(x88)，全長 112 格。
・隧道段、高架段可以重複接很多段；車站也可以直接接車站。坡道只能「地下在西、高架在東」，
  若要反方向，用 /structure load 的旋轉參數把整段轉 180° 即可。
・結構 y=9 是地表頂面（草地、沙、雪…），y0–8 是地層。
  - 想嵌進一般世界的地面：站在地面上，用 ~ ~-10 ~ 載入（地表剛好對齊你腳下那一層）。
  - 超平坦世界地層太薄，請用 ~ ~ ~ 平放，會變成一塊「立體剖面模型」，地下站剖面看得一清二楚。
・每欄最高方塊上方 3 格以內是空氣（保證軌道淨空），再往上是「結構空位」，不會清掉原地形的樹。

【搭車與拉桿】
・兩座車站的月台中段（x10–13）各有 4 格動力軌，由月台上的拉桿（x12，靠軌道那一側）供電。
  拉桿預設是開（直通）。把拉桿關掉，礦車進站就會停在月台；要發車時打開拉桿再按前進鍵。
・車站兩端（x2、x21）、隧道段與高架段（x4、x12）各有一格動力軌，下面墊紅石塊常時通電。
・升降坡道整段都是動力軌（下墊紅石塊），載人礦車可以直接爬上 15 格。
・各模組的動力段彼此不相鄰，所以常時通電的紅石塊不會讓車站拉桿失效。
・一鍵載入示範線時，函式會在線路兩端各放一塊石磚當擋塊，礦車碰到會反彈。

【一鍵載入】
請先在世界設定開啟作弊，並啟用本行為包。站在要放置的位置（會是西北下角）：
  /function {FN}/<生態系>          平放整條示範線（112 × 30 × 13）
  /function {FN}/<生態系>_embed    嵌入地面（向下 10 格）
  /function {FN}/<生態系>/<模組>    只放一件，例如 /function {FN}/cherry/el_station
全部 16 條一次排開（112 × 30 × 256）：
  /function {FN}/gallery_prepare   先建立常駐區塊（遠處才載得進去）
  /function {FN}/gallery           16 條示範線，每條間隔 16 格（z = 0, 16, 32 …）
  /function {FN}/gallery_cleanup   放完後移除常駐區塊

【手動載入】
  /give @s structure_block，把結構方塊切到「載入」模式，輸入下面的結構 ID。
  或用指令：/structure load {NS}:<生態系>_<模組> ~ ~ ~
  嵌入地面：/structure load {NS}:<生態系>_<模組> ~ ~-10 ~
  （例：櫻花林的高架車站是 cherry_el_station，前面加上 {NS}: 就是完整 ID。）

【16 個生態系與結構 ID】
生態系代號：plains 平原、desert 沙漠、snowy 雪原、jungle 叢林、taiga 針葉林、birch 樺木林、darkforest 黑森林、swamp 沼澤、
mangrove 紅樹林、savanna 莽原、badlands 惡地、mushroom 蘑菇島、ocean 海洋、cherry 櫻花林、palegarden 蒼白之園、nether 下界

{biome_block}
【附圖】
{NAME}_整體渲染.png：16 條示範線（西南上空）。
{NAME}_內部剖視.png：每個生態系的地下車站（剖去天花板）與高架車站（剖去屋頂）。
兩張圖都依方塊資料繪製，不是遊戲截圖；樓梯、半磚、柵欄、植物等以簡化方塊表示。

【測試狀態】
已通過：80 件 NBT 重新解析與逐格比對、所有方塊 ID 與 state 對照官方方塊表；
每件雙軌逐格檢查（軌道存在、下方支承、上方 2 格淨空、坡道方向、動力段分隔）；
兩種車站「月台 → 地面」步行可達檢查；重力方塊（沙、紅沙）下方有支撐、吊燈上方有方塊。
尚未在 Minecraft 遊戲內實測。海洋模組的海水是結構裡的水源方塊，放在陸地上時邊緣可能會流出一點水。
"""


if __name__ == '__main__':
    main()
