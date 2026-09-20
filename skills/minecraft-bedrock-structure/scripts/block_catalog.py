"""Query the official mojang-blocks.json so the model can see which blocks and states exist.

    python block_catalog.py --metadata <mojang-blocks.json> families
    python block_catalog.py --metadata <mojang-blocks.json> search stairs copper
    python block_catalog.py --metadata <mojang-blocks.json> states minecraft:oak_stairs
    python block_catalog.py --metadata <mojang-blocks.json> material spruce

Only reads JSON; no numpy/amulet needed. The defaults column in `states` mirrors what
scripts/structure_builder.py applies when a state is not given explicitly.
"""
import argparse, json, re
from collections import defaultdict
from pathlib import Path

BUILDER_DEFAULTS={'pillar_axis':'y','persistent_bit':True,'update_bit':False,'minecraft:vertical_half':'bottom'}
# Suffixes that identify shape variants of a material family (order matters: longest first).
SHAPES=['_double_slab','_pressure_plate','_fence_gate','_hanging_sign','_wall_sign','_standing_sign','_trapdoor','_stairs','_slab','_wall','_fence','_door','_button','_planks','_log','_wood','_leaves','_sapling','_sign']

def load(path):
    meta=json.loads(Path(path).read_text(encoding='utf8'))
    defs={v['name']:v for v in meta['data_items']}
    props={v['name']:v for v in meta['block_properties']}
    return defs,props

def short(name):return name.split(':',1)[1] if name.startswith('minecraft:') else name

def cmd_search(defs,props,keywords):
    kws=[k.lower() for k in keywords]
    hits=[n for n in sorted(defs) if all(k in n.lower() for k in kws)]
    for n in hits:
        st=','.join(p['name'] for p in defs[n]['properties'])
        print(f'{short(n):45s} {st}')
    print(f'-- {len(hits)} blocks match {" AND ".join(keywords)}')

def cmd_states(defs,props,name):
    if ':' not in name:name='minecraft:'+name
    if name not in defs:
        near=[n for n in defs if short(name) in n]
        raise SystemExit(f'Unknown block {name}. Similar: {", ".join(map(short,near[:15])) or "none"}')
    print(name)
    for p in defs[name]['properties']:
        prop=props[p['name']];values=[v['value'] for v in prop['values']]
        default=BUILDER_DEFAULTS.get(p['name'],values[0])
        print(f"  {p['name']:32s} {prop['type']:6s} default={default!r:8} values={values}")
    if not defs[name]['properties']:print('  (no states)')

def cmd_families(defs,props):
    fam=defaultdict(set)
    for n in defs:
        s=short(n)
        for suf in SHAPES:
            if s.endswith(suf):fam[s[:-len(suf)]].add(suf.lstrip('_'));break
    rows=sorted(fam.items(),key=lambda kv:(-len(kv[1]),kv[0]))
    print('material family                 shape variants available')
    for base,shapes in rows:
        if len(shapes)>=2:print(f'{base:32s} {", ".join(sorted(shapes))}')
    print(f'-- {sum(1 for _,s in rows if len(s)>=2)} families with 2+ shape variants; use `material <family>` for the full list')

def cmd_material(defs,props,base):
    base=base.lower();hits=[n for n in sorted(defs) if re.search(rf'(^|_){re.escape(base)}(_|$)',short(n))]
    for n in hits:print(short(n))
    print(f'-- {len(hits)} blocks contain "{base}"')

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--metadata',required=True,help='path to mojang-blocks.json for the target game version')
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('search');s.add_argument('keywords',nargs='+')
    s=sub.add_parser('states');s.add_argument('name')
    sub.add_parser('families')
    s=sub.add_parser('material');s.add_argument('base')
    a=ap.parse_args();defs,props=load(a.metadata)
    if a.cmd=='search':cmd_search(defs,props,a.keywords)
    elif a.cmd=='states':cmd_states(defs,props,a.name)
    elif a.cmd=='families':cmd_families(defs,props)
    else:cmd_material(defs,props,a.base)

if __name__=='__main__':main()
