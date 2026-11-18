"""最終輸出：連接狀態、分件、重新解析驗證、渲染、打包 mcpack、說明檔。"""
import json, zipfile, shutil, time
from PIL import Image, ImageDraw, ImageFont
from core import *
import build as BD, render as R, tower as TW, land as LD

NAME = '哈利法塔'
FN = 'burj'
ROOT = HERE.parents[1]
OUT = ROOT / 'structures' / NAME
PARTS = HERE / 'parts'
HEADER_UUID = '6b1f3c2a-8d4e-4f7a-9c21-3e5d7a9b1f48'
MODULE_UUID = 'c2e9a4d7-1f6b-4b38-a5e2-7d4c9f1a6b30'
VERSION = [1, 0, 0]
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'


def tile_h(ix, iz):
    return SY if ix < 2 and iz < 2 else LD.LOW_H


def panel(W, title, **kw):
    p = HERE / ('_p_%d.png' % (abs(hash(title)) % 100000))
    R.render(W.a, W.names, p, **kw)
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


def section_panel(W, notes):
    """縱剖：沿 x=83 切開（露出核心筒、氣泡柱電梯、各樓層），附高度標尺"""
    p = HERE / '_section.png'
    a = W.a.copy()
    a[84:, :, :] = 0
    R.render(a, W.names, p, view='se', scale=2, crop=(40, 84, 40, 130), floor_y=0)
    return Image.open(p).convert('RGB')


def main():
    t0 = time.time()
    W, info = BD.main()
    print('auto_connect', W.auto_connect())
    st = W.stats(skip=('sandstone', 'water', 'smooth_sandstone', 'grass_block', 'cut_sandstone', 'sand'))
    print('stats', st)
    assert st['distinct'] >= 40 and st['top'][0][2] <= 0.6
    assert info['water_leaks'] == 0
    # 氣泡柱檢查：水平鄰格不能是空氣
    bx, by0, bz, by1 = info['bubble']
    for y in range(by0, by1 + 1):
        assert W.name(bx, y, bz) == 'bubble_column'
        for dx, dz in DIRS.values():
            assert W.get(bx + dx, y, bz + dz) != 0, (y, dx, dz)
    assert W.name(bx, by0 - 1, bz) == 'soul_sand'
    # 尖塔頂
    ys = np.nonzero(W.a.any(axis=(0, 2)))[0]
    assert ys.max() == TW.YTOP, ys.max()
    # 低分件不得有高處方塊
    for ix in range(4):
        for iz in range(4):
            h = tile_h(ix, iz)
            assert not W.a[ix * 64:ix * 64 + 64, h:, iz * 64:iz * 64 + 64].any(), (ix, iz)
    # ---- 分件 ----
    if PARTS.exists(): shutil.rmtree(PARTS)
    PARTS.mkdir()
    ids = []
    for ix in range(4):
        for iz in range(4):
            h = tile_h(ix, iz)
            raw, size, npal = W.part_bytes(ix * 64, iz * 64, h=h)
            pid = f'p_{ix}_{iz}'
            (PARTS / (pid + '.mcstructure')).write_bytes(raw)
            root = parse_nbt(raw)
            assert root['format_version'] == 1 and list(root['size']) == [64, h, 64]
            bi = root['structure']['block_indices']
            assert len(bi) == 2 and all(len(l) == 64 * h * 64 for l in bi)
            pal = root['structure']['palette']['default']['block_palette']
            assert len(pal) == npal and int(bi[0].max()) < npal and int(bi[0].min()) >= 0 and int(bi[1].min()) >= -1 and int(bi[1].max()) < npal
            for b in pal:
                assert b['name'] in DEFS and b['version'] == BLOCK_VERSION
            back = np.asarray(bi[0]).reshape(64, h, 64)
            names_local = np.array([b['name'][10:] for b in pal])
            src = np.array(W.names)[W.a[ix * 64:ix * 64 + 64, :h, iz * 64:iz * 64 + 64]]
            assert (names_local[back] == src).all()
            ids.append((pid, ix * 64, iz * 64, h, len(raw), npal))
    print('parts ok', len(ids), 'bytes', sum(i[4] for i in ids))
    # ---- 渲染 ----
    notes = '依方塊資料繪製，非遊戲截圖；樓梯、半磚、玻璃板等以簡化方塊表示，噴泉水柱為靜態玻璃。'
    R.render(W.a, W.names, HERE / 'overall.png', view='sw', scale=2,
             title=f'{NAME}（Burj Khalifa）1:2.25　256 x 256 x 376（16 分件）　塔高 368 格 ≈ 828 m　西南上空俯視', notes=notes)
    P = []
    P.append(panel(W, '地面層大廳：剖切 y=7（三翼入口、接待櫃台、核心筒、氣泡柱電梯門）', view='se', scale=6, crop=(50, 120, 50, 118), cut_y=7, floor_y=3))
    P.append(panel(W, '住宅樓層：剖切樓板 100 層（約 47 樓，家具、廚房、臥室）', view='se', scale=6, crop=(44, 126, 44, 126), cut_y=103, floor_y=100))
    P.append(panel(W, '122 樓 At.mosphere 餐廳：剖切 y=203', view='se', scale=7, crop=(56, 114, 56, 114), cut_y=203, floor_y=200))
    P.append(panel(W, '124 樓 At the Top 觀景台＋北翼戶外退台：剖切 y=211', view='se', scale=7, crop=(56, 114, 56, 114), cut_y=211, floor_y=207))
    P.append(panel(W, '148 樓 At the Top SKY：剖切 y=255（氣泡柱電梯出口、望遠鏡、座椅）', view='se', scale=8, crop=(62, 108, 62, 108), cut_y=255, floor_y=251))
    P.append(panel(W, '塔冠與尖塔（y 240–372）', view='se', scale=4, crop=(60, 110, 60, 110), floor_y=240))
    P.append(panel(W, '杜拜購物中心：剖切 y=12（水族館大水箱、中庭、店面）', view='se', scale=3, crop=(160, 256, 16, 122), cut_y=12, floor_y=2))
    P.append(panel(W, '巴哈爾市集：剖切 y=8（拱廊、攤位）與步行橋', view='se', scale=4, crop=(20, 116, 136, 254), cut_y=8, floor_y=0))
    montage(P, HERE / 'interior_a.png', '', '', cols=2, cell=(1100, 900))
    sec = section_panel(W, notes)
    a = Image.open(HERE / 'interior_a.png')
    f1 = ImageFont.truetype(FONT, 40); f2 = ImageFont.truetype(FONT, 26); f3 = ImageFont.truetype(FONT, 22)
    sec.thumbnail((900, a.height - 200), Image.LANCZOS)
    canvas = Image.new('RGB', (a.width + sec.width + 60, a.height), (236, 240, 244))
    canvas.paste(a, (0, 0)); canvas.paste(sec, (a.width + 30, 150))
    dr = ImageDraw.Draw(canvas)
    dr.text((30, 16), f'{NAME}　內部剖視（樓層剖切與縱剖面）', fill=(30, 40, 60), font=f1)
    dr.text((a.width + 30, 80), '縱剖面：沿核心筒切開', fill=(40, 60, 90), font=f2)
    dr.text((a.width + 30, 112), '每 4 格一層樓板，氣泡柱電梯直達 148 樓', fill=(40, 60, 90), font=f3)
    dr.text((30, a.height - 54), notes, fill=(70, 80, 90), font=f3)
    canvas.save(HERE / 'interior.png')
    # ---- 導覽座標 ----
    tr = TW.mask(299) & ~TW.mask(300)
    cand = [(x + TW.X0, z + TW.X0) for x, z in zip(*np.nonzero(tr)) if W.get(x + TW.X0, 300, z + TW.X0) == 0]
    crown = min(cand, key=lambda p: abs(p[0] - 84) + abs(p[1] - 92) * 0 + (0 if p[1] > 84 else 50))
    t124 = TW.mask(TW.DECK124) & ~TW.mask(TW.DECK124 + 1) & TW.erode(TW.mask(TW.DECK124))
    tx, tz = [(x + TW.X0, z + TW.X0) for x, z in zip(*np.nonzero(t124))][len(np.nonzero(t124)[0]) // 2]
    fx, fy, fz = info['fountain_center']
    # ---- 打包 ----
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir(): f.unlink()
    fun = {
        'build': [f'structure load {NAMESPACE}:{pid} ~{ox} ~ ~{oz}' for pid, ox, oz, *_ in ids],
        'prepare': [f'tickingarea add ~{i * 64} ~ ~0 ~{i * 64 + 63} ~{SY - 1} ~255 {FN}{i} true' for i in range(4)],
        'cleanup': [f'tickingarea remove {FN}{i}' for i in range(4)],
        'view': ['tp @s ~-60 ~150 ~300 facing ~84 ~150 ~84'],
        'lobby': ['tp @s ~84 ~4 ~64 facing ~84 ~5 ~84'],
        'elevator': ['tp @s ~82 ~4 ~85 facing ~82 ~5 ~82'],
        'restaurant': ['tp @s ~84 ~201 ~90 facing ~84 ~201 ~70'],
        'deck124': ['tp @s ~84 ~209 ~90 facing ~84 ~209 ~70'],
        'terrace124': [f'tp @s ~{tx} ~{TW.DECK124 + 1} ~{tz} facing ~{tx} ~{TW.DECK124 + 1} ~{tz - 20}'],
        'deck148': ['tp @s ~82 ~253 ~86 facing ~82 ~253 ~100'],
        'lounge': ['tp @s ~84 ~257 ~90 facing ~84 ~257 ~70'],
        'crown': [f'tp @s ~{crown[0]} ~300 ~{crown[1]} facing ~84 ~372 ~84'],
        'fountain': [f'tp @s ~{fx} ~8 ~{fz - 34} facing ~{fx} ~8 ~{fz}'],
        'mall': ['tp @s ~208 ~4 ~124 facing ~208 ~6 ~110'],
        'aquarium': ['tp @s ~208 ~4 ~80 facing ~208 ~10 ~68'],
        'souk': ['tp @s ~68 ~4 ~210 facing ~68 ~8 ~220'],
    }
    desc = '杜拜哈利法塔 1:2.25 還原：Y 形三翼、33 段螺旋退台、尖塔，含大廳、122 樓餐廳、124/148 樓觀景台、氣泡柱電梯，以及哈利法湖杜拜噴泉、購物中心與巴哈爾市集。256×256×376，16 分件。'
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
    fur = info['furniture']
    nfur = sum(fur.values())
    ents = info['entrances']
    txt = f"""{NAME}（Burj Khalifa）　使用說明
================================

【這是什麼】
杜拜哈利法塔的 Minecraft 基岩版還原，連同塔下的哈利法塔公園、哈利法湖與杜拜噴泉、杜拜購物中心、巴哈爾市集（Souk Al Bahar）。
可用建築放置台放置。

【縮放比例（重要）】
真實哈利法塔高 828 公尺，基岩版世界總高只有 384 格（y=−64～319），1:1 放不下。
本作採 1 格 = 2.25 公尺（1:2.25）：
・塔高 368 格（地面層 y=4 到避雷針頂 y=372）≈ 828 m。
・最高使用樓層屋頂在結構 y=264（≈ 585 m，真實 585.7 m）；尖塔從 y=300 開始收細到 y=372。
・基部翼尖到中心 30 格（≈ 68 m），三翼夾角 120°。
・樓板每 4 格一層（玩家需要 3 格淨高），一層約等於真實 2.25 個樓層；樓層名稱標的是對應的真實樓層。

【尺寸】
寬 256（X）× 深 256（Z）× 高 376（Y），共 16 分件。
・塔所在的 4 件（p_0_0、p_0_1、p_1_0、p_1_1）每件 64×376×64；其他 12 件每件 64×40×64。
・方位：北 = −Z。塔中心在 (84, *, 84)，三翼分別朝北、東南、西南。湖在塔的東南方，購物中心在東北，市集在南。
・y=0～2 是砂岩地基，y=3 是地面，建築從 y=4 開始。

【放置前一定要看】
・請用「超平坦」世界，站在地面上（腳底 y=−60）執行指令。這樣塔頂在 y=312，不會超出 320 的建築上限。
・如果在一般世界（地面 y≈64）放，塔身會在 y=319 以上被截掉，尖塔和上半部會不見。
・結構內的空氣會清空原有方塊；請預留 256×376×256 的空間。

【塔身特色】
・Y 形三翼平面＋中央核心，33 段退台依「北翼 → 西南翼 → 東南翼」逆時針輪流內縮，越往上越細，形成螺旋上升的剪影。
・帷幕牆：淡藍與銀灰玻璃間隔，拋光閃長岩做垂直鋁鰭；每層樓板處是銀灰色窗間玻璃。
・5 條深色機電層帶（約 17、40、73、109、136 樓）。
・每段退台的屋頂是白色石英，外緣有玻璃欄杆。
・三翼尖端各有入口雨庇（對應真實的亞曼尼酒店、住宅、辦公三個入口）：{ents[0]}、{ents[1]}、{ents[2]}。
・塔冠 y=264～299 是玻璃鰭片密排的收頭段，尖塔是鐵塊與淺灰混凝土相間的鋼構，頂上是避雷針，途中有末地燭當航空警示燈。

【室內】
・地面層大廳挑高兩層：黑白石英拼花地板、三翼各一座接待櫃台、天花板吊燈、沙發與植栽。
・核心筒（x80～88、z80～88）：白色混凝土牆、四面門洞、電梯井（實心裝飾）、一條梯子從大廳直通 154 樓 Lounge。
・氣泡柱電梯：核心筒西北角 (82, 4, 82)。從大廳打開木門走進水柱，就會被氣泡一路推上 148 樓觀景台（約 248 格）。
  到頂後往南跳出水面就是觀景台地板。水柱下面是靈魂沙；只有上行，下樓請用梯子或 /function {FN}/lobby。
・樓層用途（依真實配置簡化）：亞曼尼酒店客房（低樓層）、住宅（家具、床、廚房、餐桌）、辦公（書桌、會議桌）、機電層（機械設備）。
  全塔共擺了 {nfur} 組家具，樓面是開放式平面，沒有隔間。
・122 樓 At.mosphere 餐廳（結構 y=201）：灰地毯、石英餐桌、紅椅、吧台。
・124 樓 At the Top 觀景台（y=209），北翼有戶外觀景退台，立面有門可以走出去；125 樓（y=213）也是觀景層。
・148 樓 At the Top SKY（y=253）：深色地板、望遠鏡、座椅，氣泡柱電梯終點。
・152～154 樓 Lounge（y=257、261）：沙發與吧台。

【塔外】
・哈利法塔公園：草坪、步道、環道、三條沿翼軸延伸的 Y 形水道（每 4 格一座小噴泉）、{info['palms']} 棵棕櫚樹。
・哈利法湖與杜拜噴泉：橢圓湖面，噴泉排成環形與中央長線，共 {info['fountain_jets']} 支水柱，以白色與淡藍玻璃表示（靜態），底座是海燈籠。湖岸步道有 {info['lamps']} 盞路燈。
・步行橋：木棧橋跨湖 (70～73, 5, 140～196)，連到南岸的巴哈爾市集。
・杜拜購物中心：砂岩外牆、兩層店面、玻璃天窗中庭、中庭裡的水族館大水箱（{info['aquarium']}，內有珊瑚與海燈籠）、面湖的玻璃立面與大門。
・巴哈爾市集：阿拉伯風拱廊、二樓、攤位、四座風塔、三個小圓頂。
・北側與西側是謝赫穆罕默德大道（簡化為雙向道路），路邊有棕櫚。

【匯入與啟用】
1. 雙擊「{NAME}.mcpack」匯入 Minecraft 基岩版。
2. 建立（或編輯）世界 → 行為包 → 啟用「{NAME}」。請用「超平坦」世界並開啟作弊。
3. 進入世界後站在想放置的位置（腳底 y=−60），這裡會是結構的西北下角。

【一鍵載入（推薦）】
  /function {FN}/prepare     ← 先建立 4 個常駐區塊，遠處分件才載得進去
  /function {FN}/build       ← 載入全部 16 分件
  /function {FN}/cleanup     ← 載入完成後移除常駐區塊

【導覽傳送】（都從載入原點算，請在原點執行）
  /function {FN}/view        西南方遠景
  /function {FN}/lobby       地面層大廳（北翼入口內）
  /function {FN}/elevator    氣泡柱電梯門口
  /function {FN}/restaurant  122 樓 At.mosphere 餐廳
  /function {FN}/deck124     124 樓觀景台
  /function {FN}/terrace124  124 樓戶外退台
  /function {FN}/deck148     148 樓 At the Top SKY
  /function {FN}/lounge      152 樓 Lounge
  /function {FN}/crown       塔冠屋頂（仰望尖塔）
  /function {FN}/fountain    杜拜噴泉
  /function {FN}/mall        購物中心臨湖大門
  /function {FN}/aquarium    水族館
  /function {FN}/souk        巴哈爾市集

【手動載入】
結構 ID：{NAMESPACE}:p_{{0-3}}_{{0-3}}
分件偏移：p_A_B 放在原點 + (A×64, 0, B×64)。例如：
  /structure load {NAMESPACE}:p_0_0 ~0 ~ ~0
  /structure load {NAMESPACE}:p_1_1 ~64 ~ ~64
也可以用結構方塊（/give @s structure_block，切到「載入」模式）逐件輸入上面的 ID 與偏移。

【附圖】
{NAME}_整體渲染.png：西南上空俯視全景。
{NAME}_內部剖視.png：大廳、住宅樓層、122 樓餐廳、124 樓觀景台與戶外退台、148 樓觀景台、塔冠尖塔、購物中心、市集，以及沿核心筒切開的整座塔縱剖面。
兩張圖都依方塊資料繪製，不是遊戲截圖。

【與真實建築的差異（已簡化）】
・樓層數：真實 163 層，這裡每 4 格一層，共約 65 層。
・退台數：真實 27 段，這裡 33 段（含塔冠），形狀相近。
・電梯：真實有 57 部電梯，這裡用一條氣泡柱代表直達觀景台的高速電梯。
・噴泉水柱是靜態玻璃，不會隨音樂噴水。周邊建築（購物中心、市集）只做外觀與部分室內。
・家具、箱子、床沒有寫入方塊實體資料，床是預設顏色。

【測試狀態】
已通過：16 分件 NBT 重新解析與逐格比對、所有方塊 ID 與 state 對照官方 1.26.60 方塊表、湖與水道水面封閉檢查、
氣泡柱四周封閉檢查、塔頂高度檢查。
尚未在 Minecraft 遊戲內實測（氣泡柱電梯在遊戲中的實際表現以遊戲為準）。
"""
    (OUT / (NAME + '_使用說明.txt')).write_text(txt, encoding='utf-8-sig')
    assert len(list(OUT.iterdir())) == 4
    json.dump(dict(info={k: v for k, v in info.items()}, stats=st, parts=ids, funcs=list(fun), crown=crown, t124=(tx, tz)),
              open(HERE / 'report.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('mcpack', mc.stat().st_size, 'done', round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
