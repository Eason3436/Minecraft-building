from preview import *
from PIL import Image
ims=[]
for b in BIOMES:
    A,names,pcs=line(b)
    R.render(A,names,'_t.png',view='sw',scale=2,title=b['zh'])
    ims.append(Image.open('_t.png').convert('RGB'))
w=max(i.width for i in ims); h=max(i.height for i in ims)
M=Image.new('RGB',(w*4,h*4),(236,240,244))
for i,im in enumerate(ims): M.paste(im,((i%4)*w,(i//4)*h))
M.save('_all.png'); print(M.size)
