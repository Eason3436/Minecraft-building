"""Style-neutral Bedrock structure primitives. Dimensions are X, Y, Z.

Example in a task-specific generator (not a finished building):
    model = StructureBuilder((23, 15, 19), metadata_path, block_version=18168865)
    stone = model.block('stone_bricks')
    model.box(0, 0, 0, 22, 0, 18, stone)
    # Add the actual task-specific architecture and interiors here.
    model.save(work_dir / 'library.mcstructure')
No design, name, output directory or database is hardcoded.
"""
import json
from pathlib import Path
import numpy as np
import amulet_nbt as n

class StructureBuilder:
    def __init__(self, size_xyz, metadata_path, *, block_version):
        self.size=tuple(size_xyz)
        if len(self.size)!=3 or any(type(v)!=int or v<=0 for v in self.size):
            raise ValueError('Specify three positive integer dimensions X, Y, Z')
        meta=json.loads(Path(metadata_path).read_text(encoding='utf8'))
        self.defs={v['name']:v for v in meta['data_items']}
        self.props={v['name']:v for v in meta['block_properties']}
        self.version=block_version;self.palette=[];self.lookup={}
        self.block('air')
        self.blocks=np.zeros(self.size,dtype=np.int32)
        self.secondary=np.full(self.size,-1,dtype=np.int32)
        self.positions=n.CompoundTag()
        self.entities=n.ListTag([],10)

    def block(self,name,**states):
        if ':' not in name:name='minecraft:'+name
        if name not in self.defs:raise ValueError('Unknown block: '+name)
        allowed={p['name'] for p in self.defs[name]['properties']}
        if set(states)-allowed:raise ValueError('Unknown state for '+name)
        values={k:self.props[k]['values'][0]['value'] for k in allowed}
        for k,v in {'pillar_axis':'y','persistent_bit':True,'update_bit':False,'minecraft:vertical_half':'bottom'}.items():
            if k in values:values[k]=v
        values.update(states);tags={}
        for k,v in values.items():
            prop=self.props[k];t=prop['type']
            expected={'bool':bool,'int':int,'string':str}[t]
            if type(v)!=expected or v not in [a['value'] for a in prop['values']]:
                raise ValueError(f'Invalid state {name} {k}={v!r}')
            tags[k]={'bool':n.ByteTag,'int':n.IntTag,'string':n.StringTag}[t](int(v) if t=='bool' else v)
        key=(name,tuple(sorted(values.items())))
        if key not in self.lookup:
            self.lookup[key]=len(self.palette)
            self.palette.append(n.CompoundTag({'name':n.StringTag(name),'states':n.CompoundTag(tags),'version':n.IntTag(self.version)}))
        return self.lookup[key]

    def _check(self,x,y,z,block):
        if any(type(v)!=int or not 0<=v<dim for v,dim in zip((x,y,z),self.size)):
            raise ValueError('Coordinate outside structure')
        if type(block)!=int or not -1<=block<len(self.palette):raise ValueError('Invalid palette index')

    def put(self,x,y,z,block,*,secondary=False):
        self._check(x,y,z,block)
        (self.secondary if secondary else self.blocks)[x,y,z]=block

    def box(self,x0,y0,z0,x1,y1,z1,block,*,secondary=False):
        self._check(x0,y0,z0,block);self._check(x1,y1,z1,block)
        if x0>x1 or y0>y1 or z0>z1:raise ValueError('Reversed bounds')
        (self.secondary if secondary else self.blocks)[x0:x1+1,y0:y1+1,z0:z1+1]=block

    # --- discovery helpers: see which blocks/states exist instead of guessing ---
    def search(self,*keywords):
        """Block names containing every keyword (AND), e.g. search('copper','stairs')."""
        kws=[k.lower() for k in keywords]
        return sorted(n for n in self.defs if all(k in n.lower() for k in kws))

    def describe(self,name):
        """{state: (type, default, allowed values)} for a block; default mirrors block()."""
        if ':' not in name:name='minecraft:'+name
        if name not in self.defs:raise ValueError('Unknown block: '+name)
        out={}
        for p in self.defs[name]['properties']:
            prop=self.props[p['name']];vals=[v['value'] for v in prop['values']]
            default={'pillar_axis':'y','persistent_bit':True,'update_bit':False,'minecraft:vertical_half':'bottom'}.get(p['name'],vals[0])
            out[p['name']]=(prop['type'],default,vals)
        return out

    # --- self-check: single-block walls are the main source of "AI-looking" builds ---
    def stats(self):
        """palette count, placed block count, and the share of the most-used non-air block."""
        counts={}
        for k in self.blocks.ravel():
            if k:
                name=str(self.palette[int(k)]['name'])[10:];counts[name]=counts.get(name,0)+1
        total=sum(counts.values())
        top=[(name,c,round(c/total,3)) for name,c in sorted(counts.items(),key=lambda kv:-kv[1])[:5]]
        return {'distinct_blocks':len(counts),'palette_variants':len(self.palette)-1,'placed':total,'top_blocks':top,'max_share':top[0][2] if top else 0}

    # --- connection states for panes/bars/walls are not recomputed on structure load ---
    def auto_connect(self):
        """Fill minecraft:connection_* / wall_connection_type_* from solid neighbours. Call before save()."""
        X,Y,Z=self.size;solid={}
        def is_solid(k):
            if k<=0:return False
            if k not in solid:
                n=str(self.palette[k]['name']);solid[k]=not any(s in n for s in ('air','_pane','_bars','_wall','glass_pane','fence','carpet','torch','lantern','candle','flower','sapling','grass','fern','water','lava','rail','vine','button','pressure_plate','snow_layer','waterlily','pot','petals','lichen'))
            return solid[k]
        def is_linkable(k):
            n=str(self.palette[k]['name']) if k>0 else '';return any(s in n for s in ('_pane','_bars','_wall'))
        changed=0
        for x in range(X):
            for y in range(Y):
                for z in range(Z):
                    k=int(self.blocks[x,y,z])
                    if k<=0:continue
                    name=str(self.palette[k]['name']);st=self.palette[k]['states']
                    keys=[s for s in st if s.startswith('minecraft:connection_') or s.startswith('wall_connection_type_')]
                    if not keys:continue
                    new={}
                    for d,(dx,dz) in {'east':(1,0),'west':(-1,0),'south':(0,1),'north':(0,-1)}.items():
                        nx,nz=x+dx,z+dz
                        nk=int(self.blocks[nx,y,nz]) if 0<=nx<X and 0<=nz<Z else 0
                        link=is_solid(nk) or is_linkable(nk)
                        if 'minecraft:connection_'+d in st:new['minecraft:connection_'+d]=link
                        elif 'wall_connection_type_'+d in st:
                            above=int(self.blocks[x,y+1,z]) if y+1<Y else 0
                            new['wall_connection_type_'+d]=('tall' if is_solid(above) or is_linkable(above) else 'short') if link else 'none'
                    if 'wall_post_bit' in st:
                        links=[v for kk,v in new.items() if v not in (False,'none')]
                        ew=new.get('wall_connection_type_east','none')!='none' and new.get('wall_connection_type_west','none')!='none'
                        ns=new.get('wall_connection_type_north','none')!='none' and new.get('wall_connection_type_south','none')!='none'
                        above=int(self.blocks[x,y+1,z]) if y+1<Y else 0
                        new['wall_post_bit']=not((ew and len(links)==2) or (ns and len(links)==2)) or is_solid(above)
                    cur={kk:({'bool':lambda v:bool(int(v)),'int':lambda v:int(v),'string':str}[self.props[kk]['type']])(v) for kk,v in st.items()}
                    cur.update(new)
                    nk=self.block(name,**cur)
                    if nk!=k:self.blocks[x,y,z]=nk;changed+=1
        return changed

    def save(self,path,origin=(0,0,0)):
        if len(origin)!=3 or any(type(v)!=int for v in origin):raise ValueError('Invalid origin')
        def ints(values):return n.ListTag([n.IntTag(int(v)) for v in values],3)
        root=n.NamedTag(n.CompoundTag({'format_version':n.IntTag(1),'size':ints(self.size),
          'structure':n.CompoundTag({'block_indices':n.ListTag([ints(self.blocks.ravel()),ints(self.secondary.ravel())]),
          'entities':self.entities,'palette':n.CompoundTag({'default':n.CompoundTag({'block_palette':n.ListTag(self.palette,10),
          'block_position_data':self.positions})})}),'structure_world_origin':ints(origin)}))
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(root.to_nbt(compressed=False,little_endian=True))
        return path
