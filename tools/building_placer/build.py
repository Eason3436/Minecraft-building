"""建築放置台打包腳本。

掃描 structures/*/*.mcpack，從每個包的 .mcfunction 讀出 `structure load` 拼接表，
產生 BP/scripts/catalog.js（建築清單）與 RP/textures/placer_icons/（選單縮圖），
最後輸出 addons/建築放置台/建築放置台.mcaddon。

用法：py -3 tools/building_placer/build.py
"""
import io, json, pathlib, re, struct, sys, zipfile

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BP, RP = HERE / 'BP', HERE / 'RP'
OUT_DIR = ROOT / 'addons' / '建築放置台'
OVERRIDES = json.loads((HERE / 'overrides.json').read_text(encoding='utf-8'))

LOAD_RE = re.compile(r'^structure load (\S+) (~-?\d*) (~-?\d*) (~-?\d*)\s*$')
CALL_RE = re.compile(r'^function (\S+)\s*$')
ABS_RE = re.compile(r'structure load (\S+) (-?\d+) (-?\d+) (-?\d+)(\s|$)')


def mcstructure_size(raw):
    """讀 mcstructure（小端序 NBT）根層的 size 清單。"""
    key = b'\x09\x04\x00size\x03\x03\x00\x00\x00'
    i = raw.find(key)
    if i < 0:
        raise ValueError('找不到 size 標籤')
    return list(struct.unpack_from('<3i', raw, i + len(key)))


def tilde(v):
    return int(v[1:] or 0)


def read_pack(path):
    z = zipfile.ZipFile(path)
    sizes, funcs = {}, {}
    for n in z.namelist():
        if n.startswith('structures/') and n.endswith('.mcstructure'):
            sid = n[len('structures/'):-len('.mcstructure')]
            ns, _, name = sid.partition('/')
            sizes[f'{ns}:{name}'] = mcstructure_size(z.read(n))
        elif n.startswith('functions/') and n.endswith('.mcfunction'):
            funcs[n[len('functions/'):-len('.mcfunction')]] = z.read(n).decode('utf-8', 'replace').splitlines()
    return sizes, funcs


def resolve(funcs, name, seen=()):
    """展開函式內的 structure load（含 function 呼叫），回傳 [(id, ox, oy, oz)]。"""
    if name in seen or name not in funcs:
        return []
    out = []
    for line in funcs[name]:
        line = line.strip()
        m = LOAD_RE.match(line)
        if m:
            out.append((m[1], tilde(m[2]), tilde(m[3]), tilde(m[4])))
            continue
        m = CALL_RE.match(line)
        if m:
            out += resolve(funcs, m[1], seen + (name,))
    return out


CJK = re.compile(r'[一-鿿]')


def txt_labels(folder, ids):
    """從使用說明 .txt 找「中文名　結構ID」的寫法，當作選單上的模組名稱。"""
    out = {}
    for txt in folder.glob('*使用說明.txt'):
        header = ''
        for line in txt.read_text(encoding='utf-8-sig', errors='replace').splitlines():
            h = re.search(r'【(?:\d+\.\s*)?([^】]+)】', line)
            if h:
                header = h[1].strip()
            for sid in ids:
                i = line.find(sid)
                if i < 0 or sid in out:
                    continue
                before = re.sub(r'^[\s\d.、：:（(）)-]+', '', line[:i]).strip(' 　：:ID')
                if CJK.search(before) and len(before) <= 12 and 'structure' not in before:
                    out[sid] = before
                elif header:
                    out[sid] = header + '｜'
    return out


def layouts_for(pack_name, sizes, funcs, folder):
    cands = {}
    for name in funcs:
        loads = resolve(funcs, name)
        if loads and all(l[0] in sizes for l in loads):
            cands[name] = loads
    # build1、build2… 合併成一個「整座」
    groups = {}
    for name in list(cands):
        m = re.fullmatch(r'(.*/)?build(\d+)', name)
        if m:
            groups.setdefault((m[1] or '') + 'build', []).append((int(m[2]), name))
    for base, parts in groups.items():
        if base not in cands:
            cands[base] = [l for _, n in sorted(parts) for l in cands[n]]
        for _, n in parts:
            cands.pop(n, None)
    # 同一組結構 ID 的函式只留一個（例如 berth1～3 與 build 相同）
    order = sorted(cands, key=lambda n: (0 if n.endswith('build') else 1, n))
    kept, seen_sets = [], set()
    for n in order:
        key = frozenset(l[0] for l in cands[n])
        if key in seen_sets:
            continue
        seen_sets.add(key)
        kept.append(n)
    labels = OVERRIDES.get('labels', {})
    pack_labels = OVERRIDES.get('packs', {}).get(pack_name, {})
    ids_labels = {**txt_labels(folder, sizes), **OVERRIDES.get('ids', {})}
    result = []
    used = set()
    for n in kept:
        loads = cands[n]
        used.update(l[0] for l in loads)
        short = n.split('/')[-1]
        label = pack_labels.get(short) or labels.get(short)
        if not label and len(loads) == 1:
            label = ids_labels.get(loads[0][0], '').rstrip('｜')
        result.append(make_layout(label or short, loads, sizes))
    # 只有絕對座標載入（例如 execute … run structure load id 100 64 100）時，整理成一個整座版面
    if len(used) * 2 < len(sizes):
        absolute = {}
        for lines in funcs.values():
            for line in lines:
                m = ABS_RE.search(line)
                if m and m[1] in sizes and m[1] not in absolute:
                    absolute[m[1]] = (m[1], int(m[2]), int(m[3]), int(m[4]))
        if len(absolute) > 1:
            result.insert(0, make_layout(labels.get('build', 'build'), list(absolute.values()), sizes))
            used.update(absolute)
    for sid in sorted(sizes):
        if sid not in used:
            short = sid.split(':')[1]
            label = pack_labels.get(short) or ids_labels.get(sid) or labels.get(short) or short
            if label.endswith('｜'):
                label += labels.get(short, short)
            result.append(make_layout(label, [(sid, 0, 0, 0)], sizes))
    if len(result) == 1 and not pack_labels.get(result[0]['name']):
        result[0]['name'] = '整座建築'
    return result


def make_layout(label, loads, sizes):
    mn = [min(l[i + 1] for l in loads) for i in range(3)]
    pieces = []
    for sid, ox, oy, oz in loads:
        s = sizes[sid]
        pieces.append([sid, ox - mn[0], oy - mn[1], oz - mn[2], *s])
    size = [max(p[1 + i] + p[4 + i] for p in pieces) for i in range(3)]
    return {'name': label, 'size': size, 'pieces': pieces}


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
    skipped = OVERRIDES.get('skip', [])
    packs = sorted(p for p in (ROOT / 'structures').rglob('*.mcpack') if '/work/' not in p.as_posix())
    for pack in packs:
        rel = pack.parent.relative_to(ROOT / 'structures').as_posix()
        if any(k in rel for k in skipped):
            continue
        parts = rel.split('/')
        name = parts[0] if len(parts) == 1 else f'{parts[0]}（{parts[-1]}）'
        sizes, funcs = read_pack(pack)
        if not sizes:
            continue
        key = f'p{len(catalog) + 1:02d}'
        render = next(pack.parent.glob('*整體渲染.png'), None)
        make_icon(render, icons / f'{key}.png', big)
        layouts = layouts_for(name, sizes, funcs, pack.parent)
        catalog.append({'name': name, 'icon': f'textures/placer_icons/{key}', 'layouts': layouts})
        summary = '、'.join(f"{l['name']}({len(l['pieces'])}塊 {l['size'][0]}×{l['size'][1]}×{l['size'][2]})" for l in layouts)
        print(f'{key} {name}: {summary}')

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
