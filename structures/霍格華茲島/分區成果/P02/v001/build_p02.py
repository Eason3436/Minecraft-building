from pathlib import Path
import json, math
from collections import deque
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
V={}
def put(x,y,z,b):
    assert 650<=x<706 and 128<=y<177 and 530<=z<626,(x,y,z)
    V[x,y,z]='minecraft:'+b
def box(x0,x1,y0,y1,z0,z1,b):
    for x in range(x0,x1):
        for y in range(y0,y1):
            for z in range(z0,z1): put(x,y,z,b)

# Only the enclosed hall is explicitly cleared. The perimeter remains sparse.
box(655,701,128,151,534,622,'air')
for x0,x1 in [(653,655),(701,703)]: box(x0,x1,128,151,532,624,'smooth_sandstone')
for z0,z1 in [(532,534),(622,624)]: box(653,703,128,151,z0,z1,'smooth_sandstone')
# Low stone plinth, cornices and a continuous parapet under the slate eaves.
for y in [128,129,149,150]:
    for xa,xb in [(652,655),(701,704)]: box(xa,xb,y,y+1,532,624,'cut_sandstone')
    for za,zb in [(531,534),(622,625)]: box(652,704,y,y+1,za,zb,'cut_sandstone')
# Eight structural bays: tall lancets and three-stage buttresses.
for z in [538,550,562,586,598,610,620]:
    for xa,xb in [(650,653),(703,706)]:
        box(xa,xb,128,140,z-1,z+2,'stone_bricks')
    for xa,xb in [(651,654),(702,705)]: box(xa,xb,140,147,z-1,z+2,'cut_sandstone')
    for xa,xb in [(652,655),(701,704)]: box(xa,xb,147,154,z,z+1,'chiseled_stone_bricks')
for z in [544,556,568,584,596,608,616]:
    for x in [653,654,701,702]:
        for y in range(133,149):
            half=3 if y<145 else max(0,148-y)
            for zz in range(z-half,z+half+1): put(x,y,zz,'blue_stained_glass')
        box(x,x+1,133,146,z,z+1,'cut_sandstone')
        box(x,x+1,140,141,z-3,z+4,'cut_sandstone')
# End gables, steep continuous two-layer roof, inside blue-black sky vault.
for x in range(650,706):
    ry=151+int(min(x-650,705-x)*0.88)
    for z in range(530,626):
        put(x,ry,z,'deepslate_tiles')
        if ry>151: put(x,ry-1,z,'deepslate_tiles')
        if 655<=x<701 and 534<=z<622:
            for y in range(151,ry-1): put(x,y,z,'air')
            if ry>152: put(x,ry-2,z,'black_concrete')
    if 653<=x<703:
        for za,zb in [(532,534),(622,624)]: box(x,x+1,151,ry,za,zb,'smooth_sandstone')
# Ridge coping, roof seams and small stone finials.
box(677,679,175,176,530,626,'polished_deepslate')
for z in [531,547,563,579,595,611,624]:
    for x in range(651,705):
        ry=151+int(min(x-650,705-x)*0.88)
        put(x,ry+1,z,'polished_deepslate')
for z in [532,624]: put(677,176,z,'chiseled_stone_bricks')
# Rose windows in the two gables, stone radial tracery.
for z in [532,533,622,623]:
    for x in range(670,686):
        for y in range(150,165):
            r=((x-677.5)**2+(y-157)**2)**.5
            if r<7: put(x,y,z,'blue_stained_glass')
            if 6<=r<7.8 or (r<7 and (x in [677,678] or y==157)):
                put(x,y,z,'cut_sandstone')
# Timber hammerbeam frames with brackets and thin tie members.
for z in [546,562,590,606,618]:
    for x in [655,700]: box(x,x+1,128,151,z,z+2,'dark_oak_planks')
    for k in range(8):
        for x in [655+k,700-k]: box(x,x+1,150+k,152+k,z,z+1,'dark_oak_planks')
    box(663,693,158,159,z,z+1,'dark_oak_planks')
# Teacher dais and high table; two block risers permit ordinary jumping.
box(658,698,128,129,536,545,'polished_deepslate')
box(660,696,129,130,536,543,'polished_deepslate')
box(661,695,131,132,540,542,'dark_oak_planks')
for x in range(662,695,4):
    box(x,x+1,130,131,537,539,'spruce_planks')
    box(x,x+1,131,134,537,538,'dark_oak_planks')
    put(x,132,540,'gold_block')
# Four house tables with bench seating, broad aisles, and supported candle lamps.
for n,x in enumerate([660,670,680,690]):
    box(x,x+3,129,130,553,607,'dark_oak_planks')
    for z in range(554,607,7):
        box(x,x+3,128,129,z,z+1,'spruce_planks')
        put(x+1,130,z,'white_concrete');put(x+1,131,z,'glowstone')
    for bx in [x-2,x+4]: box(bx,bx+1,128,129,553,607,'spruce_planks')
    # House colour runners end in heraldic panels at the teacher end.
    col=['red_wool','yellow_wool','blue_wool','green_wool'][n]
    box(x,x+3,144,150,534,535,col)
    put(x+1,146,534,'gold_block')
# Floating candle clusters are deliberate magical scenery, no physics blocks.
for x in [662,672,682,692]:
    for z in [555,573,591,605]:
        y=143+((x+z)%4)
        put(x,y,z,'white_concrete');put(x,y+1,z,'glowstone')
# Recessed glowstone stars on sloping vault, deterministic and sparse.
for x in range(657,700):
    ry=151+int(min(x-650,705-x)*0.88)
    for z in range(536,620):
        if (x*37+z*19)%137==0: put(x,ry-2,z,'glowstone')
# Entrances written last so tracery and bands cannot occlude them.
box(650,659,128,138,570,580,'air')
for z in [569,580]: box(650,656,128,140,z,z+1,'chiseled_stone_bricks')
box(650,656,138,140,570,580,'cut_sandstone')
box(699,706,128,138,569,579,'air')
for z in [568,579]: box(701,706,128,139,z,z+1,'chiseled_stone_bricks')
box(701,706,138,140,569,579,'cut_sandstone')
# Southeast service landing. Its downward stair is reserved for P22.
box(695,701,128,134,612,622,'air')
box(694,695,128,132,612,621,'cut_sandstone')
box(695,701,128,132,621,622,'cut_sandstone')
box(694,695,128,131,614,618,'air')
for x in [695,700]: put(x,132,621,'glowstone')

metadata=ROOT/'work/active_mob_tower/mojang-blocks.json'
if not metadata.exists(): metadata=Path.cwd()/'work/active_mob_tower/mojang-blocks.json'
official={b['name'] for b in json.loads(metadata.read_text())['data_items']}
assert set(V.values())<=official, set(V.values())-official
coords=np.array(list(V),dtype=np.int16)
names=np.array(list(V.values()),dtype='U48')
np.savez_compressed(OUT/'voxels.npz',coords=coords,names=names)
for x in range(650,659):
    for y in range(128,138):
        for z in range(570,580): assert V[x,y,z]=='minecraft:air'
interfaces={
 'coordinate_system':'island global; all ranges half-open',
 'west_P01':{'x':[650,659],'y':[128,138],'z':[570,580],'facing':'west','clear_width':10,'clear_height':10,'floor_y':127},
 'east_P11_future':{'x':[699,706],'y':[128,138],'z':[569,579],'facing':'east','clear_width':10,'clear_height':10,'floor_y':127,'note':'P11 corridor beyond X706 not built'},
 'P22_service_stair_reserved':{'x':[695,701],'y':[112,128],'z':[612,621],'facing':'down','note':'P02 only builds landing; parent base must leave future stair footprint removable. P22 builds staircase and opens floor later'},
 'floor_owner':'merged foundation builder supplies Y127; no P02 writes below Y128',
 'bounds':{'x':[650,706],'y':[128,177],'z':[530,626]}}
(OUT/'interfaces.json').write_text(json.dumps(interfaces,ensure_ascii=False,indent=2),encoding='utf-8')
report={'status':'geometry and block identifiers passed; not tested in game','total_records':len(V),'solid_blocks':sum(n!='minecraft:air' for n in V.values()),'bounds_min':coords.min(axis=0).tolist(),'bounds_max':coords.max(axis=0).tolist(),'palette':sorted(set(V.values())),'west_interface_open':True,'underground_untouched':True,'roof_max_y':176,'table_rows':4,'numpy_format':'coords Nx3 int16 global X,Y,Z; names N Unicode U48; air explicit; all blocks use default states'}
start=(650,575); seen={start}; queue=deque([start])
while queue:
    x,z=queue.popleft()
    for xx,zz in [(x-1,z),(x+1,z),(x,z-1),(x,z+1)]:
        if 650<=xx<706 and 530<=zz<626 and (xx,zz) not in seen and all(V.get((xx,y,zz),'minecraft:air')=='minecraft:air' for y in [128,129]):
            seen.add((xx,zz));queue.append((xx,zz))
targets=[(657,555),(666,560),(676,560),(686,560),(697,560),(705,574),(699,615),(678,548)]
assert all(t in seen for t in targets)
report['ground_level_connectivity']={'start':list(start),'targets':[list(t) for t in targets],'passed':True,'clearance':2,'note':'2-block-high cardinal walkability at base Y128; every table aisle, east door and service landing reachable'}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'施工說明.md').write_text('''# P02 大餐廳 v001

依原設計 X650–706、Z530–626，主層腳底 Y128，最高方塊 Y176。
外觀為砂岩哥德尖窗、分段扶壁、藍玻璃玫瑰窗、深灰陡坡石板屋頂與石脊；室內含四排學院長桌、雙側長凳、北端教師台、四色院徽、木構架、星空拱頂和燭光。

本分區未寫入 Y127 或以下方塊，地下廚房由 P22 後續施工。東南 X695–701/Z612–621 是服務梯預留，現在為有護欄的平層待接區，未宣稱地下梯已完成。主通道保持西 X650–659/Z570–580/Y128–138 暢通。東接口 X699–706/Z569–579/Y128–138 預留 P11 門樓走廊；外部連廊未建。

`build_p02.py` 可重現 `voxels.npz`、`interfaces.json` 與 `validation.json`。NPZ 是 coords（N×3 int16，依 X,Y,Z）與 names（N Unicode），使用全島座標，air 僅在本建物內部及門洞。所有材料名稱已對現有 Mojang 官方表核對；所有方塊採預設狀態，不使用方向樓梯。桌上燭光為白色方塊＋螢光石的方塊化造型，懸浮燭光為魔法場景装飾。教師台為兩級完整方塊，可跳上；未冒稱為無障礙。

幾何、界限、入口、材料名稱與地下不覆寫檢查通過。合併渲染與格式序列化由主代理處理；尚未在 Minecraft 遊戲內實測。
''',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
