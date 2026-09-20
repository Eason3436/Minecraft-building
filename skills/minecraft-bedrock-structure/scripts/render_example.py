import pathlib,sys,json,math
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--work-dir',type=pathlib.Path,required=True);ap.add_argument('--font');ap.add_argument('--title',required=True);args=ap.parse_args();P=args.work_dir.resolve()
import numpy as np
from PIL import Image,ImageDraw,ImageFont
data=np.load(P/'temple_voxels.npz');A=data['blocks'];colors=data['colors'];specs=json.loads((P/'palette.json').read_text())
font_path=args.font or ('C:/Windows/Fonts/msjh.ttc' if pathlib.Path('C:/Windows/Fonts/msjh.ttc').exists() else None)
font=lambda size:ImageFont.truetype(font_path,size) if font_path else ImageFont.load_default(size=size)
def render(path,cut=False):
 B=A.copy()
 if cut:B[:,10:,:]=0
 W,H=1700,1450;s=12.1;ox=850;oy=565 if not cut else 410
 im=Image.new('RGB',(W,H),(237,233,222));d=ImageDraw.Draw(im)
 def pr(x,y,z):
  v=61-z
  return (ox+(x-v)*s,oy+(x+v)*s*.49-y*s)
 def cub(x0,y0,z0,x1,y1,z1,c):
  shade=lambda f:tuple(max(0,min(255,int(t*f))) for t in c)
  d.polygon([pr(x0,y0,z0),pr(x1,y0,z0),pr(x1,y1,z0),pr(x0,y1,z0)],fill=shade(.77))
  d.polygon([pr(x1,y0,z0),pr(x1,y0,z1),pr(x1,y1,z1),pr(x1,y1,z0)],fill=shade(.60))
  d.polygon([pr(x0,y1,z0),pr(x1,y1,z0),pr(x1,y1,z1),pr(x0,y1,z1)],fill=shade(1.06))
 coords=[tuple(map(int,p)) for p in np.argwhere(B)]
 coords.sort(key=lambda p:p[0]+(60-p[2])+p[1])
 for x,y,z in coords:
  k=int(B[x,y,z]);name=specs[k]['name'];st=specs[k]['states'];c=colors[k]
  if x<60 and y<34 and z>0 and B[x+1,y,z] and B[x,y+1,z] and B[x,y,z-1]:continue
  x0,y0,z0=x,y,z;x1,y1,z1=x+1,y+1,z+1
  if 'slab' in name:
   if st.get('minecraft:vertical_half')=='top':y0+=.5
   else:y1-=.5
  elif 'carpet' in name or 'waterlily' in name or 'pressure_plate' in name:y1=y+.09
  elif 'candle' in name or 'lightning_rod' in name:
   x0+=.35;x1-=.35;z0+=.35;z1-=.35;y1-=.25
  elif 'fence' in name or 'iron_bars' in name or 'pane' in name:
   x0+=.32;x1-=.32;z0+=.32;z1-=.32
  elif 'lantern' in name or 'flower_pot' in name:
   x0+=.2;x1-=.2;z0+=.2;z1-=.2;y1-=.2
  if 'stairs' in name:
   up=st['upside_down_bit'];di=st['weirdo_direction']
   cub(x,y+.5 if up else y,z,x+1,y+1 if up else y+.5,z+1,c)
   lo,hi=(y,y+.5) if up else (y+.5,y+1)
   xx0,xx1,zz0,zz1=x,x+1,z,z+1
   if di==0:xx0+=.5
   elif di==1:xx1-=.5
   elif di==2:zz0+=.5
   else:zz1-=.5
   cub(xx0,lo,zz0,xx1,hi,zz1,c)
  else:cub(x0,y0,z0,x1,y1,z1,c)
 d.text((75,55),args.title,font=font(44),fill=(48,57,53))
 d.text((77,120),'61 × 61 × 35 格  ·  Minecraft 基岩版結構',font=font(24),fill=(93,101,88))
 d.text((77,H-110),'移除上層的內部配置預覽' if cut else '紅柱山門 · 重簷主殿 · 鐘鼓雙樓 · 迴廊蓮池',font=font(26),fill=(48,57,53))
 d.text((77,H-60),'依輸出方塊資料繪製的示意圖，非遊戲截圖；材質與局部方塊形狀已簡化。',font=font(19),fill=(102,105,96))
 im.save(path)
render(P/'temple_preview.png')
render(P/'temple_interior.png',True)
