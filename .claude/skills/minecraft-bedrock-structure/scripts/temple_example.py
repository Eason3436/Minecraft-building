import sys, pathlib, json, math, shutil, zipfile, hashlib, collections
import argparse, re
ap=argparse.ArgumentParser(description='Generate the worked temple example in scratch space')
ap.add_argument('--work-dir',type=pathlib.Path,required=True)
ap.add_argument('--metadata',type=pathlib.Path,required=True)
ap.add_argument('--id',required=True,help='Structure filename identifier chosen for this task')
args=ap.parse_args()
assert re.fullmatch(r'[a-z0-9_]+',args.id),'Invalid structure id'
P=args.work_dir.resolve();P.mkdir(parents=True,exist_ok=True)
import numpy as np
import amulet_nbt as n
from PIL import Image, ImageDraw, ImageFont

PKG=P
meta=json.loads(args.metadata.read_text(encoding='utf8'))
blocks={i['name']:i for i in meta['data_items']}
props={i['name']:i for i in meta['block_properties']}
palette=[]; specs=[]; lookup={}; colors=[]
def color(name):
 if name=='minecraft:air':return (235,231,220)
 for term,c in [('air',(235,231,220)),('gold',(220,169,49)),('red',(150,40,32)),('crimson',(134,42,36)),('deepslate',(48,64,69)),('blackstone',(45,47,52)),('dark_oak',(65,44,32)),('spruce',(94,66,42)),('quartz',(226,220,203)),('white',(220,213,194)),('water',(48,139,155)),('prismarine',(61,128,119)),('cherry_leaves',(225,154,177)),('leaves',(65,108,66)),('grass',(84,119,57)),('moss',(93,113,58)),('lantern',(247,180,65)),('glowstone',(244,193,98)),('pink',(228,144,173)),('lily',(57,133,80)),('sand',(174,157,119)),('chain',(56,55,50)),('log',(91,62,40)),('copper',(146,88,49)),('iron',(136,147,144)),('lightning',(161,91,55)),('hay',(184,150,54)),('brown',(103,64,42)),('end_rod',(241,231,177))]:
  if term!='air' and term in name:return c
 return (144,146,139)
def b(name,**state):
 if name=='chain':name='iron_bars';state={}
 name='minecraft:'+name
 assert name in blocks,name
 ss={p['name']:props[p['name']]['values'][0]['value'] for p in blocks[name]['properties']}
 if 'pillar_axis' in ss:ss['pillar_axis']='y'
 if 'persistent_bit' in ss:ss['persistent_bit']=True
 if 'update_bit' in ss:ss['update_bit']=False
 if 'minecraft:vertical_half' in ss:ss['minecraft:vertical_half']='bottom'
 ss.update(state)
 assert set(ss)=={p['name'] for p in blocks[name]['properties']},(name,ss)
 for k,v in ss.items():assert v in [a['value'] for a in props[k]['values']],(name,k,v)
 key=(name,tuple(sorted(ss.items())))
 if key not in lookup:
  st=n.CompoundTag({k:(n.ByteTag(int(v)) if props[k]['type']=='bool' else n.IntTag(v) if props[k]['type']=='int' else n.StringTag(v)) for k,v in ss.items()})
  lookup[key]=len(palette); palette.append(n.CompoundTag({'name':n.StringTag(name),'states':st,'version':n.IntTag(18168865)}))
  specs.append({'name':name,'states':ss});colors.append(color(name))
 return lookup[key]
AIR=b('air'); A=np.zeros((61,35,61),dtype=np.int32)
STONE=b('stone_bricks'); SMOOTH=b('smooth_stone'); AND=b('polished_andesite'); WHITE=b('smooth_quartz'); RED=b('red_concrete'); DARK=b('dark_oak_planks'); GOLD=b('gold_block'); TILE=b('deepslate_tiles'); TRIM=b('polished_blackstone_bricks'); GRASS=b('grass_block')
def put(x,y,z,k):
 assert 0<=x<61 and 0<=y<35 and 0<=z<61,(x,y,z)
 A[x,y,z]=k
def box(x0,y0,z0,x1,y1,z1,k):
 assert 0<=x0<=x1<61 and 0<=y0<=y1<35 and 0<=z0<=z1<61,(x0,y0,z0,x1,y1,z1)
 A[x0:x1+1,y0:y1+1,z0:z1+1]=k
def ring(x0,z0,x1,z1,y,k):
 box(x0,y,z0,x1,y,z0,k);box(x0,y,z1,x1,y,z1,k);box(x0,y,z0,x0,y,z1,k);box(x1,y,z0,x1,y,z1,k)
def slab(name='deepslate_tile_slab',top=False):return b(name,**{'minecraft:vertical_half':'top' if top else 'bottom'})
def stair(name,d,up=False):return b(name,weirdo_direction=d,upside_down_bit=up)
def pillar(x,z,y0,y1):
 put(x,y0,z,WHITE);box(x,y0+1,z,x,y1-1,z,RED);put(x,y1,z,GOLD)
 for dx,dz in [(-1,0),(1,0),(0,-1),(0,1)]:
  put(x+dx,y1,z+dz,slab('dark_oak_slab',True))
  put(x+dx,y1-1,z+dz,stair('dark_oak_stairs',0 if dx<0 else 1 if dx>0 else 2 if dz<0 else 3,True))
def lantern(x,y,z):
 put(x,y,z,b('lantern',hanging=True));put(x,y+1,z,b('chain',pillar_axis='y'))
def red_lamp(x,y,z):
 put(x,y+2,z,b('chain',pillar_axis='y'));put(x,y+1,z,slab('dark_oak_slab'))
 put(x,y,z,b('shroomlight'))
 for dx,dz in [(-1,0),(1,0),(0,-1),(0,1)]:put(x+dx,y,z+dz,b('red_stained_glass_pane'))
 put(x,y-1,z,slab('dark_oak_slab',True));put(x,y-2,z,b('lantern',hanging=True))
def roof(x0,z0,x1,z1,base,rings=None):
 depth=(min(x1-x0,z1-z0)//2)
 if rings is not None:depth=min(depth,rings)
 for x in range(x0,x1+1):
  for z in range(z0,z1+1):
   d=min(x-x0,x1-x,z-z0,z1-z)
   if d>depth:continue
   h=base+max(0,d-2)
   # Raised tips at each corner and a shallow, curved outer eave.
   corner=min(abs(x-x0),abs(x-x1))+min(abs(z-z0),abs(z-z1))
   if d==0:h=base+(1 if corner<=2 else 0)
   k=TILE
   if d==0:k=slab('deepslate_tile_slab')
   elif d>2:
    direction=0 if x-x0==d else 1 if x1-x==d else 2 if z-z0==d else 3
    k=stair('deepslate_tile_stairs',direction)
   put(x,h,z,k)
   if d in (0,2):put(x,h-1,z,slab('dark_oak_slab',True))
   if corner<=depth*2 and abs(min(x-x0,x1-x)-min(z-z0,z1-z))==0:
    put(x,h,z,slab('polished_blackstone_brick_slab'))
 for x,z,sx,sz in [(x0,z0,1,1),(x1,z0,-1,1),(x0,z1,1,-1),(x1,z1,-1,-1)]:
  put(x,base+2,z,GOLD);put(x,base+3,z,b('lightning_rod',facing_direction=1))
  put(x+sx,base+1,z+sz,GOLD)
 if rings is None:
  z=(z0+z1)//2;y=base+max(0,depth-2)+1
  box(x0+depth,y,z,x1-depth,y,z,GOLD)
  for x in [x0+depth,x1-depth]:
   put(x,y+1,z,GOLD);put(x,y+2,z,b('lightning_rod',facing_direction=1))
  for x in range(x0+depth+2,x1-depth,3):put(x,y+1,z,slab('polished_blackstone_brick_slab'))
def stone_lamp(x,z):
 put(x,2,z,STONE);put(x,3,z,b('stone_brick_wall',wall_post_bit=True));put(x,4,z,b('glowstone'))
 for dx,dz in [(-1,0),(1,0),(0,-1),(0,1)]:put(x+dx,4,z+dz,slab('stone_brick_slab'))
 put(x,5,z,slab('stone_brick_slab'));put(x,6,z,slab('stone_brick_slab'))

# Stone podium, quiet patterned court, perimeter wall.
box(0,0,0,60,0,60,STONE);box(0,1,0,60,1,60,SMOOTH)
for x in range(1,60):
 for z in range(1,60):
  if x%6==0 or z%6==0:put(x,1,z,AND)
ring(0,0,60,60,1,TRIM);ring(1,1,59,59,1,WHITE)
for x0,z0,x1,z1 in [(1,1,18,1),(42,1,59,1),(1,1,1,59),(59,1,59,59),(1,59,59,59)]:
 box(x0,2,z0,x1,4,z1,b('white_terracotta'))
 box(x0,5,z0,x1,5,z1,slab('deepslate_tile_slab'))
for x,z in [(x,z) for x in (1,59) for z in range(1,60,6)]+[(x,z) for z in (1,59) for x in range(1,60,6)]:
 box(x,2,z,x,5,z,STONE);put(x,6,z,slab('stone_brick_slab'))
box(27,1,0,33,1,33,WHITE)
for z in range(0,34):
 for x in (27,33):put(x,1,z,TRIM)
 for x in (29,31):
  if z%4==0:put(x,1,z,b('chiseled_stone_bricks'))

# Front mountain gate: three bays, painted bracket sets, two roof tiers.
box(21,2,4,39,2,12,STONE);box(22,2,4,38,2,12,WHITE)
for x in (23,27,33,37):
 for z in (5,11):pillar(x,z,3,9)
for z in (5,11):box(23,9,z,37,9,z,RED);box(23,8,z,37,8,z,DARK)
for x in (23,37):box(x,9,5,x,9,11,RED)
roof(19,2,41,14,10,rings=3)
box(25,13,6,35,15,10,RED)
for z in (6,10):
 for x in range(26,35,2):put(x,14,z,b('dark_oak_fence'))
roof(22,4,38,12,16)
box(28,8,4,32,9,4,DARK)
for x in (28,30,32):put(x,9,3,GOLD)
for x in (25,35):red_lamp(x,6,6)
for x in range(25,36):put(x,2,3,stair('stone_brick_stairs',2))

# Twin bell / drum towers, with accessible internal stair flights.
for cx,kind in [(9,'bell'),(51,'drum')]:
 box(cx-5,2,16,cx+5,3,26,STONE);box(cx-4,3,17,cx+4,3,25,DARK)
 for x in (cx-4,cx+4):
  for z in (17,25):pillar(x,z,4,10)
 ring(cx-4,17,cx+4,25,10,RED)
 for z in range(18,25):
  put(cx-4,4,z,b('dark_oak_fence'));put(cx+4,4,z,b('dark_oak_fence'))
 for x in range(cx-3,cx+4):put(x,4,25,b('dark_oak_fence'))
 roof(cx-7,14,cx+7,28,11,rings=3)
 box(cx-3,13,18,cx+3,13,24,DARK)
 for x in (cx-3,cx+3):
  for z in (18,24):pillar(x,z,14,17)
 ring(cx-3,18,cx+3,24,17,RED)
 roof(cx-5,16,cx+5,26,18)
 for j in range(7):put(cx-2,4+j,18+j,stair('dark_oak_stairs',2))
 for j in range(3):put(cx-1+j,11+j,24,stair('dark_oak_stairs',0))
 for x in range(cx-2,cx+3):
  put(x,14,18,b('dark_oak_fence'))
  if x!=cx:put(x,14,24,b('dark_oak_fence'))
 for z in range(19,24):
  put(cx-3,14,z,b('dark_oak_fence'));put(cx+3,14,z,b('dark_oak_fence'))
 for x in (cx-1,cx,cx+1):put(x,2,15,stair('stone_brick_stairs',2))
 if kind=='bell':
  box(cx-2,8,20,cx+2,8,20,DARK);put(cx,7,20,b('chain',pillar_axis='y'))
  put(cx,6,20,b('bell',attachment='hanging',direction=0,toggle_bit=False))
  # Monumental stylized upper bell.
  box(cx-1,15,20,cx+1,15,22,GOLD);put(cx,16,21,GOLD)
 else:
  box(cx-1,5,20,cx+1,7,22,b('red_terracotta'))
  box(cx-1,5,19,cx+1,7,19,b('brown_terracotta'));put(cx,6,19,b('white_terracotta'))
  box(cx-1,4,20,cx+1,4,22,DARK)
  box(cx-1,15,20,cx+1,16,22,b('red_terracotta'));box(cx-1,15,19,cx+1,16,19,b('white_terracotta'))
 for x in (cx-3,cx+3):lantern(x,8,16)

# Side cloisters: long open arcades and lattice screens.
for x0,x1 in [(3,9),(51,57)]:
 box(x0,2,29,x1,2,55,DARK)
 for z in range(30,56,5):
  for x in (x0,x1):pillar(x,z,3,7)
 for x in (x0,x1):box(x,7,30,x,7,55,RED)
 roof(x0-1,28,x1+1,57,8,rings=4)
 outer=x0 if x0<30 else x1
 for z in range(31,55):
  if (z-30)%5:
   put(outer,3,z,RED)
   box(outer,4,z,outer,5,z,b('dark_oak_fence'))
 for z in (32,37,42,47,52):lantern((x0+x1)//2,6,z)
 # rear connector to main hall, ending at the platform edge.
 if x0<30:box(9,2,53,16,2,55,DARK)
 else:box(44,2,53,51,2,55,DARK)

# Main sanctuary on a three-step white stone terrace.
box(14,2,34,46,3,57,STONE);box(14,4,34,46,4,57,WHITE)
box(17,4,37,43,4,55,DARK)
for z,y in [(31,2),(32,3),(33,4)]:
 box(25,2,z,35,y,z,STONE)
 for x in range(25,36):put(x,y,z,stair('quartz_stairs',2))
for x in (15,45):
 for z in range(35,57):put(x,5,z,b('dark_oak_fence'))
for z in (35,57):
 for x in range(16,45):
  if z==57 or x<25 or x>35:put(x,5,z,b('dark_oak_fence'))
for x in (17,23,30,37,43):
 for z in (37,55):
  if not (x==30 and z==37):pillar(x,z,5,14)
for x in (17,43):
 for z in (43,49):pillar(x,z,5,14)
ring(17,37,43,55,14,RED);ring(17,37,43,55,13,DARK)
# Wall panels retain separate windows rather than a solid box.
for x in (17,43):
 for z in range(38,55):
  if z in (43,49):continue
  box(x,5,z,x,6,z,b('red_terracotta'))
  box(x,7,z,x,10,z,b('dark_oak_fence'))
  box(x,11,z,x,12,z,b('white_terracotta'))
for x in range(18,43):
 box(x,5,55,x,12,55,b('red_terracotta'))
 if x%6 in (1,2,3):box(x,7,55,x,10,55,b('dark_oak_fence'))
for x in range(18,43):
 if x in (23,37) or 26<=x<=34:continue
 box(x,5,37,x,6,37,RED);box(x,7,37,x,11,37,b('dark_oak_fence'))
# Open central portal and beams.
box(25,5,37,25,13,37,RED);box(35,5,37,35,13,37,RED)
box(25,12,37,35,13,37,RED);box(27,12,36,33,13,36,DARK)
for x in (28,30,32):put(x,13,35,GOLD)
roof(12,33,48,59,16,rings=6)
# Raised clerestory with its own full hipped roof.
ring(19,40,41,52,20,RED);ring(19,40,41,52,23,RED)
for x in range(19,42):
 for z in (40,52):
  box(x,21,z,x,22,z,RED if x%4==0 else b('dark_oak_fence'))
for x in (19,41):
 for z in range(41,52):box(x,21,z,x,22,z,RED if z%4==0 else b('dark_oak_fence'))
# Vertical inner columns support both tiers from the hall floor.
for x in (21,39):
 for z in (41,51):pillar(x,z,5,23)
roof(16,37,44,57,23)
# Roof pearl / finial reaches the 35th layer.
put(30,33,47,GOLD);put(30,34,47,b('lightning_rod',facing_direction=1))
# Interior red runner, geometric floor border, lanterns and coffer beams.
box(28,5,38,32,5,48,b('red_carpet'))
for x in (19,41):
 for z in range(39,54):put(x,4,z,WHITE)
for z in (41,47,53):
 box(18,13,z,42,13,z,DARK)
 for x in (24,36):lantern(x,11,z)
for x in (23,37):red_lamp(x,10,35)
# Altar dais and stylized seated gilded shrine figure.
box(24,5,50,36,5,54,TRIM);box(25,6,51,35,6,54,WHITE)
box(28,7,52,32,7,54,GOLD);box(29,8,52,31,10,53,GOLD)
put(30,11,52,GOLD);put(30,12,52,b('polished_blackstone'))
put(28,9,52,GOLD);put(32,9,52,GOLD)
for x in (27,33):box(x,7,54,x,12,54,RED)
box(27,13,54,33,13,54,GOLD)
for x in (25,35):
 put(x,7,52,b('chiseled_quartz_block'));put(x,8,52,b('lantern',hanging=False))
# Offering table with legs, candles and fruit-like offerings.
for x in (25,29,31,35):put(x,5,48,b('dark_oak_fence'))
box(25,6,48,35,6,48,slab('dark_oak_slab',True))
for x in (25,35):put(x,7,48,b('red_candle',candles=2,lit=True))
for x in (27,33):put(x,7,48,b('light_weighted_pressure_plate',redstone_signal=0))
put(30,7,48,b('flower_pot',update_bit=False))
for x in (23,37):
 for z in (42,45):put(x,5,z,slab('spruce_slab'))

# Twin lotus pools, fully contained source water and tiny stone bridges.
for x0,x1 in [(15,24),(36,45)]:
 z0,z1=19,28
 box(x0,1,z0,x1,1,z1,b('prismarine_bricks'));ring(x0,z0,x1,z1,2,slab('stone_brick_slab'))
 box(x0+1,1,z0+1,x1-1,1,z1-1,b('water',liquid_depth=0))
 for dx,dz in [(2,2),(6,3),(3,7),(7,6)]:
  x=x0+dx;z=z0+dz;put(x,2,z,b('waterlily'))
 # Block-built lotus blossoms on broad pads.
 for x,z in [(x0+3,22),(x0+6,26)]:
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:put(x+dx,2,z+dz,b('waterlily'))
  put(x,1,z,GRASS);put(x,2,z,b('pink_petals',growth=3))
 for x in range(x0,x1+1):put(x,2,24,slab('stone_brick_slab',True))
 for x in (x0,x1):put(x,3,24,b('chiseled_stone_bricks'))

# Bronze incense burner on center axis, leaving paths around both sides.
box(28,2,26,32,2,30,TRIM)
for x in (29,31):
 for z in (27,29):put(x,3,z,b('cut_copper'))
box(29,4,27,31,4,29,b('cut_copper'));ring(29,27,31,29,5,b('waxed_oxidized_cut_copper'))
put(30,5,28,b('sand'))
for x,z in [(29,28),(31,28),(30,29)]:put(x,6,z,b('lightning_rod',facing_direction=1));put(x,7,z,b('red_candle',candles=0,lit=True))
for x in (28,32):box(x,5,28,x,6,28,b('waxed_oxidized_cut_copper'))

# Ornamental cherry and pine plantings.
def tree(x,z,cherry=False):
 r0=3 if cherry else 2
 box(x-r0+1,1,z-r0+1,x+r0-1,1,z+r0-1,GRASS);ring(x-r0,z-r0,x+r0,z+r0,2,slab('stone_brick_slab'))
 box(x,2,z,x,7,z,b('cherry_log' if cherry else 'spruce_log',pillar_axis='y'))
 leaf=b('cherry_leaves' if cherry else 'spruce_leaves')
 if cherry:
  for y,r in [(6,3),(7,3),(8,2),(9,1)]:
   for dx in range(-r,r+1):
    for dz in range(-r,r+1):
     if abs(dx)+abs(dz)<=r+2 and not (dx==dz==0 and y<8):put(x+dx,y,z+dz,leaf)
 else:
  for y,r in [(5,2),(6,2),(7,2),(8,1),(9,1),(10,0)]:
   for dx in range(-r,r+1):
    for dz in range(-r,r+1):
     if abs(dx)+abs(dz)<=r+1 and not(dx==dz==0 and y<8):put(x+dx,y,z+dz,leaf)
for x,z,cherry in [(9,8,True),(51,8,True),(12,44,False),(48,44,False)]:tree(x,z,cherry)
for x,z in [(20,15),(40,15),(20,31),(40,31),(11,34),(49,34)]:stone_lamp(x,z)
for x in (12,48):
 for z in (31,49,53):
  put(x,2,z,b('moss_block'));put(x,3,z,b('azalea'))
# Low benches on the two sides of the open forecourt.
for x0 in (17,39):
 for x in range(x0,x0+5):put(x,2,16,stair('spruce_stairs',3))

# Serialize standard uncompressed little-endian Bedrock NBT.
L=lambda values:n.ListTag([n.IntTag(int(i)) for i in values])
root=n.NamedTag(n.CompoundTag({'format_version':n.IntTag(1),'size':L([61,35,61]),'structure':n.CompoundTag({'block_indices':n.ListTag([L(A.ravel()),L([-1]*A.size)]),'entities':n.ListTag([],10),'palette':n.CompoundTag({'default':n.CompoundTag({'block_palette':n.ListTag(palette),'block_position_data':n.CompoundTag()})})}),'structure_world_origin':L([0,0,0])}))
raw=root.to_nbt(compressed=False,little_endian=True)
(PKG/(args.id+'.mcstructure')).write_bytes(raw)
np.savez_compressed(P/'temple_voxels.npz',blocks=A,colors=np.array(colors))
(P/'palette.json').write_text(json.dumps(specs,indent=2),encoding='utf8')


print('Scratch structure:',PKG/(args.id+'.mcstructure'))
print('Occupied blocks:',int(np.count_nonzero(A)))
