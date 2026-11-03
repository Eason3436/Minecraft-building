"""建築放置台共用：讀取 .mcpack 的結構尺寸與 function 拼接表，整理成選單用的建築資料。

build.py（放置台內建清單）與 register_pack.py（建築包自動報到）都用這裡，確保同一座建築
在兩邊的名稱與版面完全相同，選單才能合併成一筆。
"""
import json, pathlib, re, struct, zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STRUCT_ROOT = ROOT / 'structures'
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


def pack_name(pack):
    """選單上的建築名稱：structures/<名稱>/x.mcpack → 名稱；多版本子資料夾 → 名稱（版本）。"""
    pack = pathlib.Path(pack).resolve()
    try:
        rel = pack.parent.relative_to(STRUCT_ROOT).as_posix()
    except ValueError:
        return pack.stem
    parts = rel.split('/')
    return parts[0] if len(parts) == 1 else f'{parts[0]}（{parts[-1]}）'


def skipped(pack):
    rel = pathlib.Path(pack).resolve().as_posix()
    return '/work/' in rel or any(k in rel for k in OVERRIDES.get('skip', []))


def entry_for(pack):
    """回傳 {'name', 'layouts'}；包內沒有結構時回傳 None。"""
    pack = pathlib.Path(pack)
    sizes, funcs = read_pack(pack)
    if not sizes:
        return None
    name = pack_name(pack)
    return {'name': name, 'layouts': layouts_for(name, sizes, funcs, pack.parent)}


def all_packs():
    return sorted(p for p in STRUCT_ROOT.rglob('*.mcpack') if not skipped(p))
