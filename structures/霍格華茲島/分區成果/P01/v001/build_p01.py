from pathlib import Path
import numpy as np, json, math
W=Path(__file__).parent
V={}
def box(x0,y0,z0,x1,y1,z1,b):
    for x in range(x0,x1):
      for y in range(y0,y1):
       for z in range(z0,z1): V[x,y,z]=b
def put(x,y,z,b): V[x,y,z]=b
stone='stone_bricks';trim='smooth_sandstone';roof='deepslate_tiles'
# Entrance hall, clear volume restricted to its actual footprint.
box(600,128,556,650,164,596,'air')
box(600,128,556,650,148,596,stone)
box(603,128,559,647,148,593,'air')
for x in range(603,647):
 for z in range(559,593):put(x,127,z,'polished_diorite' if (x//4+z//4)%2 else 'polished_andesite')
# steep hipped slate roof, horizontal cornices, projecting buttresses
for y in (128,143,147):
 box(600,y,556,650,y+1,558,trim);box(600,y,594,650,y+1,596,trim)
 box(600,y,556,602,y+1,596,trim);box(648,y,556,650,y+1,596,trim)
for t in range(16):
 box(600+t,148+t,556+t,650-t,149+t,557+t,roof)
 box(600+t,148+t,595-t,650-t,149+t,596-t,roof)
 box(600+t,148+t,556+t,601+t,149+t,596-t,roof)
 box(649-t,148+t,556+t,650-t,149+t,596-t,roof)
for x in (604,614,634,644):
 for z in (556,594):
  box(x,128,z,x+2,148,z+2,trim)
  box(x+3,133,z,x+7,141,z+2,'light_blue_stained_glass')
  box(x+4,141,z,x+6,143,z+2,'light_blue_stained_glass')
# main south pointed portal / east dining-room connection / north future tower
box(615,163,571,635,164,581,roof)
box(619,128,592,631,139,596,'air');box(621,139,592,629,142,596,'air');box(623,142,592,627,144,596,'air')
box(647,128,570,650,138,580,'air')
box(619,128,556,631,138,559,'air')
box(600,128,573,603,137,581,'air')
# Marble stair to Y140 northern landing, with real half-step stairs.
for t in range(12):box(609,128,574-t,615,129+t,575-t,'quartz_stairs')
box(605,139,559,619,140,563,'quartz_block')
# Four house hourglasses, sand held between glazed frames.
for x,c in zip((630,634,638,642),('red_concrete','yellow_concrete','blue_concrete','green_concrete')):
 box(x,128,561,x+2,129,564,'gold_block');box(x,129,561,x+2,135,564,'glass')
 box(x,129,562,x+2,131,563,c);box(x,133,562,x+2,135,563,c)
 box(x,135,561,x+2,136,564,'gold_block')
for z in (565,586):
 for x in (605,641):
  box(x,128,z,x+2,132,z+2,'chiseled_stone_bricks');box(x,132,z,x+2,133,z+2,'glowstone')
# Forecourt, cloister, open central axis and landscaped quadrants.
box(536,128,602,636,143,650,'air')
for x in range(536,636):
 for z in range(602,650):put(x,127,z,'stone_bricks' if (x+z)%7 else 'mossy_stone_bricks')
for x0,x1 in ((548,575),(592,611)):
 for z0,z1 in ((612,621),(633,642)):
  box(x0,127,z0,x1,128,z1,'grass_block')
  for x in range(x0+2,x1-1,6):put(x,128,z0+3,'poppy')
for x in range(536,615,10):
 box(x,128,603,x+2,136,605,trim)
 box(x,136,602,min(x+10,616),138,607,stone)
 if x+9<616:
  box(x+2,133,603,x+3,136,605,trim);box(x+7,133,603,x+8,136,605,trim)
box(536,138,602,616,140,608,roof)
for z in range(608,647,10):
 box(536,128,z,538,136,z+2,trim);box(536,136,z,540,138,min(z+10,650),stone)
box(536,138,608,541,140,650,roof)
# low parapet, spaced piers, southern entry to later boat-house stair
for x in range(536,636):
 if not 617<=x<631:box(x,128,648,x+1,130,650,stone)
for x in range(539,636,12):
 if not 617<=x<631:box(x,128,647,x+2,132,650,trim);put(x,132,648,'glowstone')
# link forecourt to hall; ceremonial carpet and statue plinths
box(617,127,596,633,128,606,'stone_bricks');box(622,128,579,628,129,594,'red_carpet')
for x in (609,634):
 box(x,128,599,x+3,130,602,'chiseled_stone_bricks')
 box(x+1,130,600,x+2,135,601,'quartz_block');box(x,132,600,x+3,133,601,'quartz_block')
# keep west/east circulation and northern continuation unblocked.
keys=list(V);np.savez_compressed(W/'voxels.npz',coords=np.array(keys,dtype=np.int16),names=np.array([V[k] for k in keys]))
ports=[{'name':'P02 大餐廳','box':[647,128,570,650,138,580],'direction':'+X','width':10,'height':10},
 {'name':'P03 未建連廊','box':[619,128,556,631,138,559],'direction':'-Z','width':12,'height':10},
 {'name':'P16 未建船屋石階','box':[617,128,648,631,138,650],'direction':'+Z','width':14,'height':10}]
(W/'interfaces.json').write_text(json.dumps(ports,ensure_ascii=False,indent=2),encoding='utf8')
print('P01 authored',len(V),'voxels')
