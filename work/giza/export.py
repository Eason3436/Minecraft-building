"""最終輸出：連接狀態、分件、重新解析驗證、渲染、打包 mcpack、說明檔。"""
import json, zipfile, shutil, time, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import *
import gen, render as R, section as S, closeups, check
from gen import PX, PZ, QX, Y

NAME = '吉薩大金字塔'
FN = 'giza'
ROOT = HERE.parents[1]
OUT = ROOT / 'structures' / NAME
PARTS = HERE / 'parts'
HEADER_UUID = '6f1c2b8e-3d47-4a95-b2e1-8c7d5a9f0e31'
MODULE_UUID = 'c2a7e5d1-94b3-4f68-a1d0-7e3b6c9f2a54'
VERSION = [1, 0, 0]
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
OY = -(G + 1)          # 載入時 y 偏移：玩家腳下＝鋪石面上一格
NT = 6


def rel(p):
    x, m, z = p
    return x, Y(m) + OY, z


def montage(main, panels, path, title, notes, cols=3, cell=(1000, 760), bg=(236, 240, 244)):
    f1 = ImageFont.truetype(FONT, 46); f2 = ImageFont.truetype(FONT, 28); f3 = ImageFont.truetype(FONT, 24)
    Wd = cols * cell[0]
    mw = Wd - 60
    main = main.copy()
    if main.width > mw:
        main = main.resize((mw, int(main.height * mw / main.width)), Image.LANCZOS)
    rows = (len(panels) + cols - 1) // cols
    Ht = 100 + main.height + 30 + rows * (cell[1] + 50) + 90
    im = Image.new('RGB', (Wd, Ht), bg); dr = ImageDraw.Draw(im)
    dr.text((30, 22), title, fill=(30, 40, 60), font=f1)
    im.paste(main, ((Wd - main.width) // 2, 100))
    top = 100 + main.height + 30
    for i, (p, cap) in enumerate(panels):
        r, c = divmod(i, cols)
        p = p.copy(); p.thumbnail((cell[0] - 40, cell[1] - 30), Image.LANCZOS)
        x = c * cell[0] + (cell[0] - p.width) // 2; y = top + r * (cell[1] + 50) + 44 + (cell[1] - 30 - p.height) // 2
        dr.text((c * cell[0] + 30, top + r * (cell[1] + 50) + 4), cap, fill=(40, 60, 90), font=f2)
        im.paste(p, (x, y))
    yy = Ht - 80
    for line in notes.split('\n'):
        dr.text((30, yy), line, fill=(70, 80, 90), font=f3); yy += 34
    im.save(path)
    return im.size


def main():
    t0 = time.time()
    W, C = gen.build()
    P = C.P
    zf = PZ - gen.hw_of(7)
    tg = {k: (v[0], Y(v[1]), v[2]) for k, v in P.items() if k not in ('gant', 'temple', 'boatpit') and not k.startswith('queen_')}
    walk, nseen = check.walk(W, C, (PX + 4, G + 1, zf - 13), tg, (PX - 20, PX + 30, 2, G + 80, 15, 265))
    print('walk', walk, nseen)
    assert all(walk.values()), walk
    print('auto_connect', W.auto_connect())
    st = W.stats(skip=('end_stone', 'sand', 'sandstone', 'cut_sandstone', 'smooth_sandstone'))
    print('stats', st)
    assert st['distinct'] >= 30
    # ---- 分件（每件高度依內容裁切）----
    if PARTS.exists(): shutil.rmtree(PARTS)
    PARTS.mkdir()
    ids = []
    for ix in range(NT):
        for iz in range(NT):
            sub = W.a[ix * 64:ix * 64 + 64, :, iz * 64:iz * 64 + 64]
            ys = np.nonzero(sub.any(axis=(0, 2)))[0]
            h = int(min(W.size[1], max(ys.max() + 3, G + 12)))
            raw, size, npal = W.part_bytes(ix * 64, iz * 64, h=h)
            pid = f'p_{ix}_{iz}'
            (PARTS / (pid + '.mcstructure')).write_bytes(raw)
            root = parse_nbt(raw)
            assert root['format_version'] == 1 and list(root['size']) == [64, h, 64]
            bi = root['structure']['block_indices']
            assert len(bi) == 2 and all(len(l) == 64 * h * 64 for l in bi)
            pal = root['structure']['palette']['default']['block_palette']
            assert len(pal) == npal and int(bi[0].max()) < npal and int(bi[0].min()) >= 0 and int(bi[1].max()) < npal
            for b in pal:
                assert b['name'] in DEFS and b['version'] == BLOCK_VERSION
            back = np.asarray(bi[0]).reshape(64, h, 64)
            names_local = np.array([b['name'][10:] for b in pal])
            assert (names_local[back] == np.array(W.names)[sub[:, :h, :]]).all()
            ids.append((pid, ix * 64, iz * 64, h, len(raw), npal))
    print('parts ok', len(ids), 'MB', round(sum(i[4] for i in ids) / 1e6, 1))
    # ---- 渲染：整體 ----
    notes = '依方塊資料繪製，非遊戲截圖；樓梯、半磚以簡化方塊表示。'
    R.render(W.a, W.names, HERE / 'overall.png', view='ne', scale=2, floor_y=G - 6,
             title=f'{NAME}（古夫金字塔）1:1　384 x 384 x 190（36 分件）　東北上空俯視', notes=notes + '　白色外殼為剛完工時的圖拉石灰岩樣貌；金色塔頂為推測。')
    # ---- 渲染：剖面＋近景 ----
    z0, z1, y0, y1, s = 18, 264, 2, G + 152, 6
    sec = S.section(W, C.VD.V, QX + 1, 14, z0, z1, y0, y1, s=s)
    kz0, kz1 = C.kz
    L = [
        ('大空洞（2017 緲子偵測，示意）', PZ - 20, Y(55), 'L', 260),
        ('大走廊（高 9、疊澀頂）', PZ - 22, Y(36), 'L', 330),
        ('北面走廊（2023 發現，密封）', PZ - gen.hw_of(24) + 5, Y(25), 'L', 400),
        ('原始入口（離地 17 m）', P['entrance'][2] + 1, Y(18), 'L', 470),
        ('上升通道與花崗岩塞', PZ - 66, Y(10), 'L', 540),
        ('阿爾-馬蒙盜洞（今參觀入口）', P['mamun'][2] + 4, Y(8), 'L', 610),
        ('井道與洞穴', PZ - 41, Y(5), 'L', 680),
        ('下降通道 26.5°', PZ - 60, Y(-4), 'L', 760),
        ('國王墓室通氣孔（通到外面）', PZ + 40, Y(71), 'R', 260),
        ('減壓室 5 層（頂層山形）', kz0 + 2, Y(58), 'R', 330),
        ('國王墓室（花崗岩）', kz0 + 2, Y(45), 'R', 400),
        ('王后墓室通氣孔（甘騰布林克小門）', P['gant'][2] - 2, Y(P['gant'][1]), 'R', 470),
        ('王后墓室（山形頂）', PZ, Y(23), 'R', 560),
        ('地下室（岩盤下 30 m，未完工）', PZ - 2, Y(-27), 'R', 860),
    ]
    sec = S.annotate2(sec, L, z0, y1, s, font_size=26)
    sec.save(HERE / 'section.png')
    cp = closeups.panels(W, C)
    pan = [(Image.open(cp['king']), '國王墓室平面（拿掉天花板）：石棺、前室吊門槽'),
           (Image.open(cp['gallery']), '大走廊剖切：坡台、疊澀、下端木梯'),
           (Image.open(cp['queen']), '王后墓室平面：山形頂、東牆疊澀龕'),
           (Image.open(cp['sub']), '地下室平面：未完工岩丘、坑、死路通道'),
           (Image.open(cp['mamun']), '北面：盜洞口現代階梯、原始入口山形石'),
           (Image.open(cp['pit']), '南側船坑（拿掉蓋石）：拆解的雪松木船件'),
           (Image.open(cp['temple']), '葬祭殿：玄武岩地坪、花崗岩柱廊、參道')]
    montage(sec, pan, HERE / 'interior.png', f'{NAME}　南北向剖面（切在通道平面，往西看）與內部近景',
            notes + '\n剖面中淺色虛影＝切面後方的空腔（通氣孔、大空洞等）；通道為了能走而放大成 2 寬 3 高。', cols=4, cell=(900, 700))
    # ---- 打包 ----
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir(): f.unlink()
    def tp(p, dx=0, dy=0, dz=0, look=None):
        x, y, z = rel(p); s = f'tp @s ~{x + dx} ~{y + dy} ~{z + dz}'
        if look:
            lx, ly, lz = rel(look); s += f' facing ~{lx} ~{ly} ~{lz}'
        return [s]
    fun = {
        'build': [f'structure load {NAMESPACE}:{pid} ~{ox} ~{OY} ~{oz}' for pid, ox, oz, *_ in ids],
        'build_flat': [f'structure load {NAMESPACE}:{pid} ~{ox} ~ ~{oz}' for pid, ox, oz, *_ in ids],
        'prepare': [f'tickingarea add ~{i * 64} ~ ~0 ~{i * 64 + 63} ~ ~383 {FN}{i} true' for i in range(NT)],
        'cleanup': [f'tickingarea remove {FN}{i}' for i in range(NT)],
        'view': [f'tp @s ~330 ~{150 + OY} ~-90 facing ~{PX} ~{60 + OY} ~{PZ}'],
        'north': [f'tp @s ~{PX + 4} ~{G + 2 + OY} ~{zf - 30} facing ~{PX + 4} ~{G + 20 + OY} ~{PZ}'],
        'entrance': tp(P['entrance'], 0, 0, 1, (QX, 10, PZ - 80)),
        'mamun': tp(P['mamun'], 0, 0, 1, (PX + 4, 7, PZ)),
        'gallery': tp(P['gallery'], 0, 0, 0, (QX, 40, PZ)),
        'queen': tp(P['queen'], 0, 0, 0, (PX + 9, 22, PZ)),
        'king': tp(P['king'], 0, 0, 0, (PX, 44, P['king'][2])),
        'relief': tp(P['relief'], 0, 0, 0, (PX - 1, 63, P['relief'][2])),
        'sub': tp(P['sub'], 0, 0, 0, (PX - 5, -27, PZ - 2)),
        'grotto': tp(P['grotto']),
        'top': [f'tp @s ~{PX} ~{Y(gen.TOPK) + 1 + OY} ~{PZ}'],
        'temple': [f'tp @s ~{285} ~{G + 1 + OY} ~{PZ} facing ~256 ~{G + 4 + OY} ~{PZ}'],
        'queens': [f'tp @s ~{360} ~{G + 3 + OY} ~{196} facing ~322 ~{G + 10 + OY} ~{196}'],
        'boatpit': [f'tp @s ~{P["boatpit"][0]} ~{G - 3 + OY} ~{273}'],
    }
    desc = '古夫金字塔 1:1 實尺還原（剛完工時的白色外殼），含國王墓室、減壓室、王后墓室、大走廊、上升／下降通道、地下室、井道、盜洞、通氣孔，周邊有葬祭殿、參道、三座王后金字塔、衛星金字塔、船坑與馬斯塔巴墓群。384×384×190，36 分件。'
    manifest = {'format_version': 2, 'header': {'name': NAME, 'description': desc, 'uuid': HEADER_UUID, 'version': VERSION, 'min_engine_version': [1, 26, 60]},
                'modules': [{'type': 'data', 'uuid': MODULE_UUID, 'version': VERSION}]}
    mc = OUT / (NAME + '.mcpack')
    with zipfile.ZipFile(mc, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        for k, lines in fun.items(): z.writestr(f'functions/{FN}/{k}.mcfunction', '\n'.join(lines) + '\n')
        for pid, *_ in ids: z.write(PARTS / (pid + '.mcstructure'), f'structures/{NAMESPACE}/{pid}.mcstructure')
    with zipfile.ZipFile(mc) as z:
        assert z.testzip() is None
        for pid, *_ in ids:
            assert z.read(f'structures/{NAMESPACE}/{pid}.mcstructure') == (PARTS / (pid + '.mcstructure')).read_bytes()
    shutil.copyfile(HERE / 'overall.png', OUT / (NAME + '_整體渲染.png'))
    shutil.copyfile(HERE / 'interior.png', OUT / (NAME + '_內部剖視.png'))
    kx = P['king']
    txt = f"""{NAME}　使用說明
================================

【這是什麼】
埃及吉薩的古夫金字塔（大金字塔），以 1 格＝1 公尺的實尺比例還原成約西元前 2560 年剛完工的樣子：
整座外表是磨光的白色圖拉石灰岩外殼，內部通道與墓室依考古實測的位置、角度與尺寸配置。
周邊一起做了葬祭殿、參道、三座王后金字塔、衛星金字塔、五個船坑與東、南兩區馬斯塔巴墓群。
可用建築放置台放置。

【尺寸】
全區 寬 384（X）× 深 384（Z）× 高 190（Y），共 36 分件（6×6，每件 64×64，高度依內容裁切）。
方位：北 = −Z，東 = +X。金字塔四面正對東西南北，跟真的一樣。
大金字塔：底邊 231 格（實測 230.33 m）、高 147 層（原高 146.6 m）、斜率約 51.8°，中心在結構座標 ({PX}, {PZ})。
地面（鋪石面）在結構內 y={G}；地下室在地面下 30 格，所以結構最底部在地面下 36 格。

【內部（全部可以走到）】
・阿爾-馬蒙盜洞：北面離地 7 格的洞口，有現代石階上去。西元 820 年代盜挖，現在的參觀入口。
  往南走 38 格，會接到上升通道（繞過三塊花崗岩塞）和下降通道。
・原始入口：北面離地 17 格，偏東 7 格；入口上方有山形石（chevron）。
・下降通道：坡度 26.5°（每前進 2 格下降 1 格），一路穿過金字塔、鑽進岩盤，到地面下 27 格。
・地下室：地面下 30 格，14×8，從未完工：西半部還是一條條沒鑿完的岩丘，中央有坑，南牆有一條 16 格的死路通道。
・上升通道：從下降通道頂部分岔往上，底端被三塊花崗岩塞封住（這就是盜洞要繞路的原因）。
・王后墓室通道與王后墓室：離地 21 格的水平通道，墓室 6×5，山形頂，東牆有疊澀龕（龕後有尋寶者挖的洞）。
  南北兩條通氣孔沒有通到外面，南孔盡頭是銅色的「甘騰布林克小門」。
・大走廊：長約 40 格、高 9 格，兩側坡台、上方疊澀收窄；下端缺口處有現代木梯可以爬上走廊。
・大台階、前室（花崗岩，三道吊門槽、花崗岩橫板）、國王墓室：10×5×6，全花崗岩，西端有石棺。
  南北兩條通氣孔一路通到金字塔外面。
・減壓室：國王墓室上方 5 層，花崗岩樑分隔，最上層是山形頂，牆上有施工隊留下的紅色塗鴉。
  從大走廊頂端東側的梯子上去，經過戴維森通道，再爬維斯炸開的梯井即可逐層參觀。
・井道與洞穴：從大走廊下端西牆的豎井爬梯子下去，途中有天然小岩洞，最後以台階接到下降通道底部。
・北面走廊（2023 年掃描發現）與大空洞（2017 年緲子成像發現）：都做成密封空腔，只有剖面圖看得到，挖進去才進得了。
・照明：通道與墓室頂上嵌了赭黃蛙明燈（現代參觀照明），避免裡面生怪。

【周邊】
・圍牆與鋪石台：金字塔四周 10 格寬白色鋪石，外圍一道 2 厚 8 高的石牆，北、南、西各有開口。
・葬祭殿：緊貼東面中央，黑色玄武岩地坪、紅色花崗岩柱廊、西側聖所假門。
・參道：從葬祭殿往東一直延伸到結構邊緣（原本通到 740 m 外的河谷神殿），有屋頂與中央採光縫。
・王后金字塔 G1-a、G1-b、G1-c：在東側由北往南排列，各有東側小禮拜堂；北面入口可以走進去，地下有墓室。
・衛星金字塔 G1-d：大金字塔東南角外。
・船坑：東面兩個、參道北側一個（船形，開放），南面兩個長方形船坑（蓋石封頂，坑內放著拆解的雪松木船件）。
・馬斯塔巴墓群：東區一排、南區三排；每座有斜面牆、東側禮拜堂與假門。

【匯入與啟用】
1. 雙擊「{NAME}.mcpack」匯入 Minecraft 基岩版。
2. 建立（或編輯）世界 → 行為包 → 啟用「{NAME}」，並開啟作弊。
3. 站在想放置的位置（這裡會是全區的西北角，腳下會變成鋪石面）。

【一鍵載入】
  /function {FN}/prepare     ← 先建立 6 個常駐區塊，遠處分件才載得進去（世界最多 10 個，滿了請先移除舊的）
  /function {FN}/build       ← 一般世界：載入 36 分件，地面對齊你的腳下（結構會往下挖 41 格，請站在 y ≥ −20）
  /function {FN}/cleanup     ← 載入完成後移除常駐區塊
超平坦世界：地面太靠近世界底部，請改用
  /function {FN}/build_flat  ← 整塊沙漠台地放在腳下，台地面會比你目前高 41 格，之後用 /function {FN}/view 傳送過去

【導覽傳送】（從載入原點算，請站回原點執行；build_flat 時 y 會差 41，請先把自己往上 tp 41 格再執行）
  /function {FN}/view       全景
  /function {FN}/north      北面（盜洞與原始入口）
  /function {FN}/mamun      盜洞內
  /function {FN}/entrance   原始入口
  /function {FN}/gallery    大走廊
  /function {FN}/queen      王后墓室
  /function {FN}/king       國王墓室
  /function {FN}/relief     最上層減壓室（坎貝爾室）
  /function {FN}/sub        地下室
  /function {FN}/grotto     井道洞穴
  /function {FN}/top        塔頂
  /function {FN}/temple     葬祭殿
  /function {FN}/queens     王后金字塔
  /function {FN}/boatpit    南側船坑內

【手動載入】
結構 ID：{NAMESPACE}:p_{{0-5}}_{{0-5}}
分件偏移：p_A_B 放在原點 + (A×64, −41, B×64)。例如：
  /structure load {NAMESPACE}:p_0_0 ~0 ~-41 ~0
  /structure load {NAMESPACE}:p_2_3 ~128 ~-41 ~192
結構內的空氣會清空原有方塊，請預留 384×384 的空間。

【和真實的差異（已簡化之處）】
・通道實際只有 1.05 m 寬、1.2 m 高，人要彎腰；這裡放大成 2 寬 3 高才能走。大走廊底寬也放大成 4（實際 2.06 m）。
・石棺放大約 1.5 倍以便辨識；減壓室每層實際不到 1 m 高，這裡做成 2 格。
・金色塔頂（金字塔尖）是推測，原物已失傳。北面走廊、大空洞的實際形狀未知，為示意。
・通氣孔實際 20 cm 見方，這裡是 1×1 斜孔。下降、上升通道統一用 1:2 坡度（實際 26°～26.5°，非常接近）。
・現代設施（木梯、石階、照明）是為了遊玩加的。

【附圖】
{NAME}_整體渲染.png：東北上空俯視全區。
{NAME}_內部剖視.png：切在通道平面的南北向剖面（含標註）＋國王墓室、大走廊、王后墓室、地下室、北面入口、船坑、葬祭殿近景。
兩張圖都依方塊資料繪製，不是遊戲截圖。

【測試狀態】
已通過：36 分件 NBT 重新解析與逐格比對、所有方塊 ID 與 state 對照官方 1.26.60 方塊表、
從北面石階出發到原始入口、盜洞、大走廊、王后墓室、國王墓室、最上層減壓室、井道洞穴、地下室的步行連通檢查。
尚未在 Minecraft 遊戲內實測。
"""
    (OUT / (NAME + '_使用說明.txt')).write_text(txt, encoding='utf-8-sig')
    assert len(list(OUT.iterdir())) == 4
    json.dump(dict(P=P, parts=ids, stats=st, walk=walk, lights=C.nlights, funcs=list(fun)), open(HERE / 'report.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('mcpack MB', round(mc.stat().st_size / 1e6, 2), 'done', round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
