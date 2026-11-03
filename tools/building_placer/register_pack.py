"""讓建築包向「建築放置台」自動報到。

在 .mcpack 裡加一段 scripts/placer_register.js：世界載入後（或放置台發出 placer:discover 時），
用 scriptevent 把這座建築的名稱、版面與拼接表傳給放置台。啟用了這個包，放置台的選單就會
自動出現它，不必重新打包放置台。

用法：
  py -3 tools/building_placer/register_pack.py structures/<建築>/<建築>.mcpack [更多 .mcpack…]
  py -3 tools/building_placer/register_pack.py --all     # structures/ 底下全部

會直接改寫 .mcpack：加入 script 模組與 @minecraft/server 2.0.0 依賴、min_engine_version 至少 1.21.90，
內容有變時把 header 版本號的最後一碼 +1（遊戲才會接受重新匯入）。重複執行不會重複加入。
"""
import io, json, pathlib, sys, uuid, zipfile

from catalog_lib import all_packs, entry_for

sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_PATH = 'scripts/placer_register.js'
SERVER_VERSION = '2.0.0'
MIN_ENGINE = [1, 21, 90]

TEMPLATE = '''// 由 tools/building_placer/register_pack.py 產生：向「建築放置台」報到。
// 沒有安裝放置台時，這段程式什麼都不會做。
import { world, system } from '@minecraft/server';

const ENTRY = __ENTRY__;
const TEXT = JSON.stringify(ENTRY);
const CHUNK = 1800; // scriptevent 訊息上限 2048 字

function send() {
  const n = Math.ceil(TEXT.length / CHUNK);
  let i = 0;
  const step = () => {
    for (let k = 0; k < 8 && i < n; k++, i++) {
      // 格式：序號|總數|名稱長度|名稱+本段內容
      system.sendScriptEvent('placer:register', `${i}|${n}|${ENTRY.name.length}|${ENTRY.name}${TEXT.slice(i * CHUNK, (i + 1) * CHUNK)}`);
    }
    if (i < n) system.runTimeout(step, 1);
  };
  step();
}

system.afterEvents.scriptEventReceive.subscribe((e) => {
  if (e.id === 'placer:discover') send();
});
world.afterEvents.worldLoad.subscribe(() => system.runTimeout(send, 40));
'''


def render_script(entry):
    return TEMPLATE.replace('__ENTRY__', json.dumps(entry, ensure_ascii=False, separators=(',', ':')))


def patch(pack):
    pack = pathlib.Path(pack)
    entry = entry_for(pack)
    if not entry:
        print(f'略過（沒有結構）：{pack}')
        return False
    script = render_script(entry)
    with zipfile.ZipFile(pack) as z:
        files = {n: z.read(n) for n in z.namelist()}
    manifest = json.loads(files['manifest.json'].decode('utf-8-sig'))
    header = manifest['header']
    modules = manifest.setdefault('modules', [])
    other = [m for m in modules if m.get('type') == 'script' and m.get('entry') != SCRIPT_PATH]
    if other:
        print(f'略過（已有自己的腳本模組 {other[0].get("entry")}，請手動合併）：{pack}')
        return False

    changed = files.get(SCRIPT_PATH, b'').decode('utf-8') != script
    if not any(m.get('entry') == SCRIPT_PATH for m in modules):
        modules.append({
            'type': 'script',
            'language': 'javascript',
            'entry': SCRIPT_PATH,
            'uuid': str(uuid.uuid5(uuid.UUID(header['uuid']), 'placer_register')),
            'version': list(header['version']),
        })
        changed = True
    deps = manifest.setdefault('dependencies', [])
    if not any(d.get('module_name') == '@minecraft/server' for d in deps):
        deps.append({'module_name': '@minecraft/server', 'version': SERVER_VERSION})
        changed = True
    if list(header.get('min_engine_version', [0, 0, 0])) < MIN_ENGINE:
        header['min_engine_version'] = MIN_ENGINE
        changed = True
    if not changed:
        print(f'已是最新：{entry["name"]}（{header["version"]}）')
        return False

    old = list(header['version'])
    header['version'] = old[:2] + [old[2] + 1]
    for m in modules:
        if m.get('entry') == SCRIPT_PATH:
            m['version'] = list(header['version'])
    files['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    files[SCRIPT_PATH] = script.encode('utf-8')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in sorted(files, key=lambda n: (n != 'manifest.json', n)):
            z.writestr(n, files[n])
    pack.write_bytes(buf.getvalue())
    pieces = sum(len(l['pieces']) for l in entry['layouts'])
    print(f'已加入報到：{entry["name"]}  版本 {old} → {header["version"]}  {len(entry["layouts"])} 種版面、{pieces} 塊')
    return True


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    packs = all_packs() if argv == ['--all'] else [pathlib.Path(a) for a in argv]
    n = sum(patch(p) for p in packs)
    print(f'完成，改寫 {n} 個包。改寫過的包要在遊戲裡重新匯入。')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
