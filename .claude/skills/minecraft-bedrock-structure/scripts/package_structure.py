"""Validate Bedrock NBT and emit a mcpack, UTF-8 instructions and two renders."""
import argparse, hashlib, json, pathlib, re, uuid, zipfile, shutil
from PIL import Image
import amulet_nbt as n

def validate(raw):
    c=n.ReadContext()
    root=n.load(raw,compressed=False,little_endian=True,read_context=c).compound
    assert c.offset==len(raw),'Unexpected bytes after root NBT'
    assert isinstance(root['format_version'],n.IntTag) and int(root['format_version'])==1
    def ints(value,length=None):
        assert isinstance(value,n.ListTag) and all(isinstance(v,n.IntTag) for v in value)
        if length is not None:assert len(value)==length
        return [int(v) for v in value]
    dims=ints(root['size'],3);x,y,z=dims
    assert 0<x<=64 and 0<y<=256 and 0<z<=64,'Split oversized structures before packaging'
    ints(root['structure_world_origin'],3)
    st=root['structure'];layers=st['block_indices'];default=st['palette']['default'];pal=default['block_palette']
    assert isinstance(pal,n.ListTag) and len(pal)>0
    for b in pal:
        assert isinstance(b,n.CompoundTag)
        assert isinstance(b['name'],n.StringTag) and str(b['name']).startswith('minecraft:')
        assert isinstance(b['version'],n.IntTag)
        assert isinstance(b['states'],n.CompoundTag)
        assert all(isinstance(v,(n.ByteTag,n.IntTag,n.StringTag)) for v in b['states'].values())
    assert isinstance(st['entities'],n.ListTag) and st['entities'].list_data_type==10
    assert all(isinstance(e,n.CompoundTag) for e in st['entities'])
    assert isinstance(layers,n.ListTag) and len(layers)==2
    for layer in layers:
        indices=ints(layer,x*y*z)
        assert all(-1<=i<len(pal) for i in indices),'Invalid palette index'
    positions=default['block_position_data'];assert isinstance(positions,n.CompoundTag)
    for k,v in positions.items():
        assert k.isdigit() and 0<=int(k)<x*y*z and isinstance(v,n.CompoundTag)
    return dims

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--structure',type=pathlib.Path,required=True)
    p.add_argument('--output-dir',type=pathlib.Path,required=True)
    p.add_argument('--name',required=True)
    p.add_argument('--preview',type=pathlib.Path,required=True)
    p.add_argument('--interior',type=pathlib.Path,required=True)
    p.add_argument('--namespace',required=True)
    p.add_argument('--id',required=True)
    p.add_argument('--min-engine-version',default='1.21.60')
    p.add_argument('--version',default='1.0.0')
    p.add_argument('--previous-manifest',type=pathlib.Path)
    p.add_argument('--features',default='依照本次建築需求製作。')
    p.add_argument('--placement',default='原點為結構最小 X/Y/Z 角；請依建模配置確認地基高度與入口面向。')
    a=p.parse_args()
    assert re.fullmatch(r'[a-z][a-z0-9_]*',a.namespace),'Invalid namespace'
    assert re.fullmatch(r'[a-z0-9_]+',a.id),'Invalid structure id'
    assert a.name and not re.search(r'[<>:"/\\|?*\x00-\x1f]',a.name),'Unsafe filename'
    assert a.name not in ('.','..') and not a.name.endswith(('.', ' '))
    def version(s):
        assert re.fullmatch(r'\d+\.\d+\.\d+',s),'Use three numeric version components'
        return list(map(int,s.split('.')))
    for image_path in (a.preview,a.interior):
        with Image.open(image_path) as image:
            assert image.format=='PNG','Render must be PNG'
            assert max(image.size)>=1600,'Render long edge must be at least 1600 px'
            image.verify()
    raw=a.structure.read_bytes();dims=validate(raw)
    ver=version(a.version);engine=version(a.min_engine_version)
    h,m=str(uuid.uuid4()),str(uuid.uuid4())
    if a.previous_manifest:
        old=json.loads(a.previous_manifest.read_text(encoding='utf8'))
        h=old['header']['uuid'];m=old['modules'][0]['uuid']
        uuid.UUID(h);uuid.UUID(m)
        assert ver>old['header']['version'],'Increment the existing pack version'
    assert h!=m
    manifest={'format_version':2,'header':{'name':a.name,'description':a.features,'uuid':h,'version':ver,'min_engine_version':engine},'modules':[{'type':'data','uuid':m,'version':ver}]}
    out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    assert not any(out.iterdir()),'Use a fresh delivery directory; do not delete other user files'
    mcpack=out/(a.name+'.mcpack');txt=out/(a.name+'_使用說明.txt')
    preview=out/(a.name+'_整體渲染.png');interior=out/(a.name+'_內部剖視.png')
    member=f'structures/{a.namespace}/{a.id}.mcstructure';identifier=f'{a.namespace}:{a.id}'
    with zipfile.ZipFile(mcpack,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr(member,raw)
    with zipfile.ZipFile(mcpack) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'manifest.json',member}
        assert z.read(member)==raw
        assert json.loads(z.read('manifest.json'))==manifest
        validate(z.read(member))
    shutil.copyfile(a.preview,preview);shutil.copyfile(a.interior,interior)
    x,y,z=dims
    txt.write_text(f'''{a.name} — Minecraft 基岩版結構行為包

內容：{a.features}
附圖：{preview.name}、{interior.name}
附圖依建築方塊資料繪製，非遊戲截圖；材質或局部方塊形狀可能簡化。
尺寸：寬 {x} × 深 {z} × 高 {y} 格（結構方塊 X={x}、Y={y}、Z={z}）。
行為包宣告最低版本：{a.min_engine_version}；此宣告不代表已在該版本實測。

使用方法
1. 開啟 {mcpack.name}，用 Minecraft 匯入。
2. 在目標世界設定中，啟用剛匯入的行為包。
3. 在允許指令的世界取得結構方塊：/give @s structure_block
4. 放置結構方塊，切换成「載入」，輸入：{identifier}
5. 載入預覽並確認位置，再放置建築。
也可執行 /structure load {identifier} 100 70 100
這是示例座標，請換成自己的空地位置。

擺放：{a.placement}
請預留 {x} × {z} × {y} 格空間。結構中的空氣會清空原有方塊；索引 -1 才保留原地形。
不要按儲存來覆蓋已有結構。只需匯入行為包，不需更換 db 或世界檔。
此檔為基岩版行為包，不是 Java 版 schematic，也不是完整世界。

驗證：已重新解析 NBT、檢查尺寸與索引、驗證包內結構一致及 ZIP CRC。
尚未在 Minecraft 客戶端實際載入測試；方塊名稱與版本相容性另依建模時官方表檢查。
結構 SHA-256：{hashlib.sha256(raw).hexdigest()}
''',encoding='utf-8-sig')
    assert set(out.iterdir())=={mcpack,txt,preview,interior}
    print(mcpack);print(txt);print(preview);print(interior)

if __name__=='__main__':main()
