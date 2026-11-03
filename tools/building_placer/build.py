"""建築放置台打包腳本。

掃描 structures/**/*.mcpack（讀取邏輯在 catalog_lib.py），從每個包的 .mcfunction 讀出 `structure load` 拼接表，
產生 BP/scripts/catalog.js（建築清單）與 RP/textures/placer_icons/（選單縮圖），
最後輸出 addons/建築放置台/建築放置台.mcaddon。

用法：py -3 tools/building_placer/build.py
"""
import io, json, pathlib, sys, zipfile

from PIL import Image, ImageDraw

from catalog_lib import ROOT, all_packs, entry_for

sys.stdout.reconfigure(encoding='utf-8')
HERE = pathlib.Path(__file__).resolve().parent
BP, RP = HERE / 'BP', HERE / 'RP'
OUT_DIR = ROOT / 'addons' / '建築放置台'

def make_icon(src, dst, fallback):
    img = Image.open(src).convert('RGBA') if src else fallback.copy()
    img.thumbnail((128, 128), Image.LANCZOS)
    canvas = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    canvas.paste(img, ((128 - img.width) // 2, (128 - img.height) // 2), img)
    canvas.save(dst, optimize=True)


def block_textures():
    """畫放置台的 16×16 貼圖：深色框、金色角、中央十字準星。"""
    side = Image.new('RGBA', (16, 16), (52, 44, 66, 255))
    d = ImageDraw.Draw(side)
    d.rectangle([0, 0, 15, 15], outline=(28, 22, 36, 255))
    d.rectangle([1, 1, 14, 14], outline=(96, 84, 120, 255))
    for x, y in [(1, 1), (13, 1), (1, 13), (13, 13)]:
        d.rectangle([x, y, x + 1, y + 1], fill=(232, 186, 64, 255))
    d.rectangle([4, 4, 11, 11], fill=(36, 30, 48, 255))
    d.rectangle([5, 5, 10, 10], outline=(120, 214, 255, 255))
    top = side.copy()
    t = ImageDraw.Draw(top)
    t.line([7, 3, 7, 12], fill=(255, 220, 90, 255))
    t.line([8, 3, 8, 12], fill=(255, 220, 90, 255))
    t.line([3, 7, 12, 7], fill=(255, 220, 90, 255))
    t.line([3, 8, 12, 8], fill=(255, 220, 90, 255))
    return side, top


def ui_icons(folder):
    """選單按鈕用的 32×32 小圖示（不依賴原版 UI 貼圖路徑）。"""
    folder.mkdir(parents=True, exist_ok=True)
    W = 32

    def new():
        img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        return img, ImageDraw.Draw(img)

    green, red, gold, blue, grey = (92, 200, 90, 255), (220, 70, 60, 255), (240, 196, 70, 255), (110, 190, 255, 255), (200, 200, 210, 255)
    img, d = new(); d.line([6, 17, 13, 24, 26, 8], fill=green, width=5); img.save(folder / 'confirm.png')
    img, d = new(); d.line([7, 7, 25, 25], fill=red, width=5); d.line([25, 7, 7, 25], fill=red, width=5); img.save(folder / 'stop.png')
    img, d = new()
    d.ellipse([7, 7, 25, 25], outline=gold, width=4)
    for a, b in [((16, 2), (16, 8)), ((16, 24), (16, 30)), ((2, 16), (8, 16)), ((24, 16), (30, 16))]:
        d.line([a, b], fill=gold, width=4)
    d.ellipse([13, 13, 19, 19], fill=gold); img.save(folder / 'settings.png')
    img, d = new()
    d.line([5, 11, 25, 11], fill=blue, width=3); d.polygon([(25, 5), (31, 11), (25, 17)], fill=blue)
    d.line([7, 21, 27, 21], fill=blue, width=3); d.polygon([(7, 15), (1, 21), (7, 27)], fill=blue); img.save(folder / 'swap.png')
    img, d = new()
    d.rectangle([8, 10, 24, 28], outline=grey, width=3); d.line([5, 7, 27, 7], fill=grey, width=3)
    d.line([13, 4, 19, 4], fill=grey, width=3); d.line([13, 13, 13, 25], fill=grey, width=2); d.line([19, 13, 19, 25], fill=grey, width=2)
    img.save(folder / 'trash.png')
    img, d = new()
    d.arc([6, 8, 28, 28], 180, 450, fill=gold, width=4); d.polygon([(1, 18), (11, 18), (6, 10)], fill=gold); img.save(folder / 'undo.png')
    img, d = new()
    d.line([8, 24, 24, 8], fill=gold, width=6); d.polygon([(4, 28), (6, 21), (11, 26)], fill=grey); img.save(folder / 'edit.png')


def zip_dir(folder, zf, prefix):
    for f in sorted(folder.rglob('*')):
        if f.is_file():
            zf.write(f, prefix + f.relative_to(folder).as_posix())


def main():
    icons = RP / 'textures' / 'placer_icons'
    icons.mkdir(parents=True, exist_ok=True)
    for old in icons.glob('*.png'):
        old.unlink()
    (RP / 'textures' / 'blocks').mkdir(parents=True, exist_ok=True)
    side, top = block_textures()
    side.save(RP / 'textures' / 'blocks' / 'building_placer_side.png')
    top.save(RP / 'textures' / 'blocks' / 'building_placer_top.png')
    big = top.resize((128, 128), Image.NEAREST)
    big.save(RP / 'pack_icon.png')
    big.save(BP / 'pack_icon.png')
    ui_icons(RP / 'textures' / 'placer_ui')

    catalog = []
    for pack in all_packs():
        entry = entry_for(pack)
        if not entry:
            continue
        key = f'p{len(catalog) + 1:02d}'
        render = next(pack.parent.glob('*整體渲染.png'), None)
        make_icon(render, icons / f'{key}.png', big)
        catalog.append({'name': entry['name'], 'icon': f'textures/placer_icons/{key}', 'layouts': entry['layouts']})
        summary = '、'.join(f"{l['name']}({len(l['pieces'])}塊 {l['size'][0]}×{l['size'][1]}×{l['size'][2]})" for l in entry['layouts'])
        print(f"{key} {entry['name']}: {summary}")
    big.resize((128, 128)).save(icons / 'default.png')

    js = ('// 由 tools/building_placer/build.py 自動產生，請勿手改。\n'
          '// pieces: [結構ID, 偏移x, 偏移y, 偏移z, 寬x, 高y, 深z]\n'
          'export const CATALOG = ' + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')) + ';\n')
    (BP / 'scripts' / 'catalog.js').write_text(js, encoding='utf-8')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / '建築放置台.mcaddon'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder, inner in [(BP, '建築放置台_BP.mcpack'), (RP, '建築放置台_RP.mcpack')]:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as pz:
                zip_dir(folder, pz, '')
            zf.writestr(inner, buf.getvalue())
    print(f'共 {len(catalog)} 座建築 → {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
