"""最終輸出：連接狀態、含水、切 16 分件、重新解析驗證、渲染、打包 mcpack。"""
import sys, json, zipfile, hashlib, shutil, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from core import *
import build as BD, render as R, mine as MN, town

NAME = '潮音環線山城'
FN = 'chaoyin'
ROOT = HERE.parents[1]
OUT = ROOT / 'structures' / NAME
PARTS = HERE / 'parts'
HEADER_UUID = '3d5b1c7e-9a42-4f6b-8c1d-5e7a2b9f4c61'
MODULE_UUID = 'a4c8e2f1-6b3d-4a95-9e7c-1d2f8b5a3c74'
VERSION = [1, 1, 0]
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'


def waterlog(W, T):
    """海面以下、非整塊的方塊補上次層水。"""
    names = W.names
    part = np.array([any(k in n for k in ('fence', '_wall', 'stairs', 'slab', 'kelp', 'seagrass', 'bars', 'ladder', 'trapdoor')) for n in names])
    sub = W.a[:, :SEA + 1, :]
    m = part[sub] & T['sea'][:, None, :]
    W.w2[:, :SEA + 1, :] |= m
    return int(m.sum())


def panel(W, title, **kw):
    p = HERE / ('_p_%s.png' % abs(hash(title)))
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


def main():
    t0 = time.time()
    W, T = BD.main()
    c = T['checks']
    assert c['houses_unreachable'][0] == 0, c['houses_unreachable']
    assert all(c['walk'].values()), c['walk']
    for k in ('simA', 'simB', 'sim_slowA', 'sim_slowB'):
        assert min(v[0] for v in c[k]) > 0.15, (k, c[k])
    print('auto_connect', W.auto_connect())
    print('waterlog', waterlog(W, T))
    # 再驗一次（連接狀態改寫後）
    c2 = BD.checks(W, T)
    assert c2['railA'] == c['railA'] and c2['railB'] == c['railB']
    st = W.stats(skip=('deepslate', 'stone', 'andesite', 'tuff', 'cobblestone', 'mossy_cobblestone', 'water', 'dirt', 'grass_block', 'sand', 'gravel', 'calcite', 'sandstone', 'clay', 'coarse_dirt'))
    print('stats', st)
    assert st['distinct'] >= 40 and st['top'][0][2] <= 0.6
    # ---- 分件 ----
    if PARTS.exists(): shutil.rmtree(PARTS)
    PARTS.mkdir()
    ids = []
    for ix in range(4):
        for iz in range(4):
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
            # 逐格比對
            back = np.asarray(bi[0]).reshape(64, SY, 64)
            names_local = np.array([b['name'][10:] for b in pal])
            src = np.array(W.names)[W.a[ix * 64:ix * 64 + 64, :, iz * 64:iz * 64 + 64]]
            assert (names_local[back] == src).all()
            ids.append((pid, ix * 64, iz * 64, len(raw), npal))
    print('parts ok', len(ids), 'bytes', sum(i[3] for i in ids))
    # ---- 渲染 ----
    notes = '依方塊資料繪製，非遊戲截圖；樓梯、半磚、柵欄等以簡化方塊表示。'
    R.render(W.a, W.names, HERE / 'overall.png', view='sw', scale=2,
             title=f'{NAME}　256 x 256 x 128（16 分件）　西南上空俯視', notes=notes)
    P = []
    P.append(panel(W, '海濱總站與下城：一樓剖切（大廳、售票亭、店面）', view='se', scale=7, crop=(98, 150, 166, 206), cut_y=26, floor_y=19))
    P.append(panel(W, '後山地下車站：移除上方山體（月台、軌道、出口樓梯）', view='se', scale=8, crop=(78, 114, 20, 56), cut_y=40, floor_y=32))
    P.append(panel(W, '教堂廣場：剖切在二樓高度（教堂長椅、祭壇、市政廳）', view='se', scale=7, crop=(100, 146, 88, 122), cut_y=62, floor_y=54))
    P.append(panel(W, '西側溺谷高拱橋與雙軌門型架', view='sw', scale=5, crop=(20, 80, 70, 150), floor_y=12))
    P.append(panel(W, '金礦場：剖切在坑道高度（主坑室、金礦脈、支坑道、坑口礦場）', view='se', scale=6, crop=(122, 180, 38, 84), cut_y=49, floor_y=44))
    P.append(panel(W, '黃金碼頭：專用鐵路終點、保稅金庫倉、起重機與運金商船', view='se', scale=5, crop=(176, 226, 196, 252), floor_y=12))
    montage(P, HERE / 'interior.png', f'{NAME}　內部剖視與結構細節', notes, cols=3, cell=(1200, 950))
    # ---- 打包 ----
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir(): f.unlink()
    px, pg, pz = T['summit']; ex, ey, ez = T['ug_exit']; wm = T.get('windmill') or (54, 90, 66)
    fun = {
        'build': [f'structure load {NAMESPACE}:{pid} ~{ox} ~ ~{oz}' for pid, ox, oz, _, _ in ids],
        'prepare': [f'tickingarea add ~{i * 64} ~ ~0 ~{i * 64 + 63} ~{SY - 1} ~255 {FN}{i} true' for i in range(4)],
        'cleanup': [f'tickingarea remove {FN}{i}' for i in range(4)],
        'life': ['summon minecart ~120 ~31 ~197', 'summon minecart ~126 ~31 ~199', 'summon minecart ~96 ~35 ~30', 'summon minecart ~96 ~35 ~28',
                 'summon minecart ~125 ~24 ~175', 'summon chest_minecart ~140 ~48 ~60', 'summon chest_minecart ~202 ~30 ~110', 'summon chest_minecart ~202 ~24 ~228', 'summon minecart ~168 ~48 ~60', 'summon villager ~120 ~23 ~179', 'summon villager ~92 ~23 ~183', 'summon villager ~127 ~59 ~108',
                 'summon villager ~150 ~23 ~179', 'summon cat ~118 ~23 ~184', 'summon dolphin ~120 ~16 ~236', 'summon tropicalfish ~110 ~17 ~226'],
        'view': ['tp @s ~20 ~110 ~290 facing ~122 ~50 ~120'],
        'station': ['tp @s ~123 ~31 ~194 facing ~123 ~31 ~210'],
        'harbor': ['tp @s ~148 ~24 ~236 facing ~123 ~40 ~190'],
        'church': ['tp @s ~127 ~59 ~111 facing ~115 ~66 ~100'],
        'summit': [f'tp @s ~{px} ~{pg + 18} ~{pz} facing ~{px} ~{pg} ~{pz + 60}'],
        'metro': ['tp @s ~96 ~35 ~33 facing ~96 ~35 ~28'],
        'metroexit': [f'tp @s ~{ex} ~{ey + 1} ~{ez} facing ~{ex} ~{ey} ~{ez + 20}'],
        'viaduct': ['tp @s ~60 ~40 ~118 facing ~40 ~34 ~108'],
        'highline': ['tp @s ~214 ~40 ~100 facing ~224 ~38 ~120'],
        'lighthouse': ['tp @s ~245 ~32 ~184 facing ~245 ~45 ~190'],
        'funicular': ['tp @s ~123 ~23 ~178 facing ~125 ~40 ~140'],
        'mine': ['tp @s ~140 ~47 ~62 facing ~132 ~48 ~58'],
        'mineyard': ['tp @s ~172 ~47 ~58 facing ~164 ~49 ~60'],
        'goldline': ['tp @s ~198 ~30 ~150 facing ~202 ~26 ~176'],
        'goldport': ['tp @s ~203 ~24 ~214 facing ~210 ~28 ~232'],
        'goldmarket': ['tp @s ~152 ~23 ~181 facing ~152 ~24 ~190'],
        'windmill': [f'tp @s ~{wm[0] + 8} ~{wm[1] + 3} ~{wm[2] + 8} facing ~{wm[0]} ~{wm[1] + 8} ~{wm[2]}'],
    }
    desc = '由雙軌環狀鐵路圍繞的靠海山城：地中海彩色台地聚落、海堤高架總站、爬坡高架、後山地下鐵路、溺谷高拱橋、纜索鐵道、山腹金礦場、黃金專用鐵路與黃金出口碼頭、金市與生活店鋪。256×256×128，16 分件。'
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
    ri = T['railinfo']; sim = c2['simA'][0]
    kinds = {}
    for h_ in T['houses']:
        if h_.get('kind'): kinds.setdefault(h_['kind'], []).append((h_['x0'], h_['base'] + 1, h_['z0']))
    shop_lines = '\n'.join(f"  {town.KIND_NAME[k]} ×{len(v)}：" + '、'.join(str(p) for p in v[:3]) + ('…' if len(v) > 3 else '') for k, v in kinds.items())
    mp = T['mine_path']; sh = T['mine_shaft']
    txt = f"""{NAME}　使用說明
================================

【這是什麼】
一座被雙軌環狀鐵路圍繞、靠海的地中海風山城。房屋順著山坡一層層往上疊，山腳是港口與沙灘，
鐵路沿著地形繞城一圈：南邊走海堤高架、東邊爬坡上高架、北邊鑽進後山變成地下鐵路、西邊用高拱橋跨過溺谷。
適合放在超平坦世界。可用建築放置台放置。

【尺寸】
寬 256（X）× 深 256（Z）× 高 128（Y），共 16 分件（每件 64×128×64）。
方位：北 = −Z（後山），南 = +Z（大海），東側也是海。海面在結構內 y=20。

【環狀雙軌鐵路】
・內軌一圈 {ri['A']['length']} 格、外軌 {ri['B']['length']} 格，兩軌中間隔一格，可雙向對開。軌面高度 {ri['A']['levels'][0]}～{ri['A']['levels'][1]}。
・南段「海堤高架」：軌面 y=30，石砌連拱，拱洞可從下城走到沙灘與碼頭；海濱總站在這一段。
・東段「爬坡高架」：每 3 格升 1 格，從 y=30 爬到 y=38，接著以高架跨過東城。
・北段「地下鐵路」：整段鑽進後山，隧道內有石襯砌、每 6 格一座深色木框與吊燈；途中從 y=38 降到 y=34，並設有後山地下車站。
・西段「溺谷高橋」：軌面 y=34，橋下離水面 13 格，之後降回 y=30 接回海堤。
・路線不是方框：斜線段是之字軌，並且每隔一小段插入 3 格直線來放動力軌。
・動力：內軌 {ri['A']['powered']} 格、外軌 {ri['B']['powered']} 格動力鐵軌，全部下墊紅石塊常時通電；坡道每一格都是動力軌。
  最長的無動力區間 {c2['maxgapA']} 格。以載人礦車的近似公式模擬（雙向、含低速進場），全程最低速度約 {sim[0] * 20:.1f} 格/秒，一圈約 {sim[2]:.0f} 秒。
  空礦車阻力大很多，不保證能自己繞完一圈。
・沿線裝飾：{ri['gantries']} 座雙軌門型架（橫樑＋吊燈）、高架石護欄與燈柱、平地段樹籬與圍籬交錯、橋墩與拱、隧道洞門。

【金礦場與黃金出口】
・金礦坑：開在山體東北側的山腹裡。坑口礦場在 (168, 46, 60)，有洞門、礦石堆、礦石斗、起重架與工寮。
  主坑道往西通到主坑室 (139, 46, 60)：不規則穹頂、兩根岩柱、岩壁上的金礦脈（金礦石、深板岩金礦石、原金塊）、熔爐與箱子、木棧台。
  另有北、南兩條支坑道和掌子面；西南支坑道接一座梯子豎井，直通山頂平台的井架 ({sh[0]}, {sh[1]}, {sh[2]})。
・黃金專用鐵路：單線，全長 {len(mp)} 格，從主坑室出坑口，沿台地一路下坡往東，再貼著環線高架橋腳往南，
  從環線高架底下的石造箱涵穿過，直達黃金碼頭突堤末端 (202, 22, {MN.PIER_END})。全線落差 {mp[0][1] - mp[-1][1]} 格。
  除了轉角以外全部是動力鐵軌，每 3 格墊一個紅石塊，兩端有擋塊，礦車碰到擋塊會自動折返。
  /function {FN}/life 會在線上放三台運輸礦車（箱子礦車）。它和環狀雙軌是分開的兩套鐵路，不相接。
・黃金碼頭（港口東側加大）：石岸壁與突堤、磚造保稅金庫倉（庫內金磚垛）、兩座橫跨鐵路的門型起重機、金箱堆。
  突堤東側停一艘三桅大型運金商船（甲板載金磚與箱子），西側停一艘雙桅商船。防波堤改到港口東側。 (205, 22, 212)
・金市：站前廣場東側，四個黃白篷攤位與金秤台。 (152, 22, 188)

【生活機能店鋪】（門楣上有代表方塊當招牌，一樓是對應的店內陳設；座標是建築西北角）
{shop_lines}
  礦場旁的台地是金飾街；下城主街集中了大部分店鋪。

【石階】
全城石階都是曲折的：每爬上一層台地，就在平台上橫移幾格再繼續往上；登頂步道是之字形，接到山頂平台。

【搭車方式】
1. /function {FN}/life 會在總站與地下車站的軌道上各放礦車（也可以自己放）。
2. 坐上礦車後按一下前進鍵，碰到動力軌就會自己加速繞行。
3. 海濱總站月台上有兩支拉桿（內外軌各一支），預設是開（直通）。把拉桿關掉，礦車進站會停在拉桿前；要發車時打開拉桿再按前進鍵。
4. 纜索鐵道：站前廣場北側 (125, 23, 176) 直上教堂廣場，全程動力軌，長 {c2['funi'][0]} 格、爬升 {c2['funi'][1]} 格。兩端有擋塊，礦車放上去按前進鍵即可。

【主要景點】（座標為相對於載入原點的 x, y, z）
・海濱總站：一樓大廳與售票亭、樓梯上月台、二樓候車室、鐘塔、兩側月台雨棚；面海月台有樓梯下到沙灘。 (123, 30, 192)
・下城：濱海主街、市場攤位與水井、店面街屋。 (120, 22, 179)
・台地聚落：6 層擋土牆台地，共 {len(T['houses'])} 棟彩色街屋，每棟都有室內（家具、床、吊燈、梯子），門口都能從總站步行走到。
・主石階從站前廣場 (119, 22, 176) 曲折上到教堂廣場，另有東、西、東城等石階與之字登頂步道。
・教堂廣場：教堂（玫瑰窗、彩色玻璃、長椅、祭壇）、30 格高鐘樓、市政廳、噴泉。 (127, 58, 104)
・山頂瞭望鐘樓與城堡遺跡：({px}, {pg}, {pz})，由東側登頂石階上山。
・後山地下車站：(96, 34, 30)，樓梯往南通到後山山腰出口 ({ex}, {ey}, {ez})。
・西側溺谷高拱橋：(40, 34, 108)；旁邊有葡萄梯田、瀑布與風車 ({wm[0]}, {wm[1]}, {wm[2]})。
・東城與舊機務段：磚造車庫、靜態蒸汽機車與兩節車廂（展示用，不與環線相連）。 (215, 28, 120)
・港口：石碼頭、商港突堤與木起重機、兩艘帆船、漁港木棧橋與小漁船、亂石防波堤、沙灘陽傘。 (120, 22, 208)
・燈塔岬：紅白燈塔與守燈人小屋。 (245, 30, 190)

【匯入與啟用】
1. 雙擊「{NAME}.mcpack」匯入 Minecraft 基岩版。
2. 建立（或編輯）世界 → 行為包 → 啟用「{NAME}」。建議用「超平坦」世界，並開啟作弊。
3. 進入世界後站在想放置的位置（這裡會是結構的西北下角）。

【一鍵載入（推薦）】
  /function {FN}/prepare     ← 先建立 4 個常駐區塊，遠處分件才載得進去
  /function {FN}/build       ← 載入全部 16 分件
  /function {FN}/cleanup     ← 載入完成後移除常駐區塊
  /function {FN}/life        ← （選用）放礦車、村民、貓、海豚

【導覽傳送】（都從載入原點算，請在原點執行）
  /function {FN}/view        全景
  /function {FN}/station     海濱總站
  /function {FN}/harbor      港口
  /function {FN}/church      教堂廣場
  /function {FN}/summit      山頂
  /function {FN}/metro       後山地下車站
  /function {FN}/metroexit   地下車站出口
  /function {FN}/viaduct     溺谷高拱橋
  /function {FN}/highline    東側高架
  /function {FN}/funicular   纜索鐵道下站
  /function {FN}/lighthouse  燈塔
  /function {FN}/windmill    風車
  /function {FN}/mine        金礦主坑室
  /function {FN}/mineyard    坑口礦場
  /function {FN}/goldline    黃金專用鐵路（橋下箱涵前）
  /function {FN}/goldport    黃金碼頭
  /function {FN}/goldmarket  金市

【手動載入】
結構 ID：{NAMESPACE}:p_{{0-3}}_{{0-3}}
分件偏移：p_A_B 放在原點 + (A×64, 0, B×64)。例如：
  /structure load {NAMESPACE}:p_0_0 ~0 ~ ~0
  /structure load {NAMESPACE}:p_2_3 ~128 ~ ~192
結構內的空氣會清空原有方塊，請預留 256×128×256 的空間。

【附圖】
{NAME}_整體渲染.png：西南上空俯視全景。
{NAME}_內部剖視.png：總站與下城一樓剖切、地下車站、教堂廣場剖切、溺谷高拱橋、金礦場剖切、黃金碼頭。
兩張圖都依方塊資料繪製，不是遊戲截圖；樓梯、半磚、柵欄等以簡化方塊表示。

【測試狀態】
已通過：16 分件 NBT 重新解析與逐格比對、所有方塊 ID 與 state 對照官方 1.26.60 方塊表、
兩條環線沿軌 3D 走查（相接、淨空、支承、供電）、纜索鐵道與黃金專用鐵路走查、礦車動能模擬、
全部房屋門口與各景點（含金礦坑室、豎井頂、黃金碼頭）的步行連通檢查。
尚未在 Minecraft 遊戲內實測。動能模擬用的是近似公式，實際速度可能略有出入。
床、箱子、熔爐等沒有寫入方塊實體資料，載入後是遊戲預設內容（空箱、預設床色）；店鋪的「商品」是擺設方塊，不是可交易的村民。
"""
    (OUT / (NAME + '_使用說明.txt')).write_text(txt, encoding='utf-8-sig')
    assert len(list(OUT.iterdir())) == 4
    json.dump(dict(checks={k: v for k, v in c2.items()}, rail=T['railinfo'], houses=len(T['houses']), stats=st, summit=T['summit'], ug_exit=T['ug_exit'], windmill=T.get('windmill'),
                   portals=T['portals'], parts=ids, funcs=list(fun)), open(HERE / 'report.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('mcpack', mc.stat().st_size, 'done', round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
