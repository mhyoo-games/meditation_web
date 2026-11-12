"""힐링 마을 주민: 1단계 동물들을 KayKit 몸체 + 가을 일상복으로.
usage: python3 -I kk_villagers.py <kaykit gltf dir> <stage1 dir(our models)> <out dir> key ...
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kk_build as kb

RW, MW = kb.ROGUE_DROP, kb.MAGE_DROP
# (base, cells, mesh_cells, fur, white, paw)
WEAR = {
    'bear':     ('Rogue', {"0,1": "#B8862A", "1,1": "#D9A43A", "3,2": "#5A4636"}, {"Arm": {"5,2": "FUR", "5,0": "#D9A43A"}}, '#8E5E3B', '#EED9B8'),
    'panda':    ('Rogue', {"0,1": "#4E7E4E", "1,1": "#6E9E62", "3,2": "#3A3A44"}, {"Arm": {"5,2": "#24222A", "5,0": "#6E9E62"}}, '#24222A', '#FAFAF5'),
    'fox':      ('Mage',  {"0,1": "#8E2F3A", "5,0": "#E8D9B8"}, {"Arm": {"0,1": "#8E2F3A", "4,0": "#E8D9B8", "7,2": "FUR"}}, '#E8823A', '#FFF6EC'),
    'raccoon':  ('Rogue', {"0,1": "#4A5E80", "1,1": "#5A6E8E", "3,2": "#2E2E36"}, {"Arm": {"5,2": "#2A2830", "5,0": "#5A6E8E"}}, '#8E8C96', '#F4F1EC'),
    'squirrel': ('Rogue', {"0,1": "#A84E2E", "1,1": "#C0603A", "3,2": "#6A4A36"}, {"Arm": {"5,2": "WHITE", "5,0": "#C0603A"}}, '#C9783C', '#FFF1DC'),
    'deer':     ('Mage',  {"0,1": "#E3D3B6", "5,0": "#8A5A3A"}, {"Arm": {"0,1": "#E3D3B6", "4,0": "#C9B89A", "7,2": "FUR"}}, '#B97C4A', '#FFF5E6'),
}

def main(kdir, ourdir, outdir, keys):
    meta = {}
    for key in keys:
        base, cells, mesh_cells, fur, white = WEAR[key]
        sub = lambda v: {'FUR': fur, 'WHITE': white}.get(v, v)
        cfg = dict(base=base, drop=RW if base == 'Rogue' else MW, cells={k: sub(v) for k, v in cells.items()},
                   mesh_cells={m: {k: sub(v) for k, v in d.items()} for m, d in mesh_cells.items()}, head_drop=0.02, inflate={})
        K, kn, info = kb.build(os.path.join(kdir, base + '.glb'), os.path.join(ourdir, key, f'{key}_stage1.glb'), cfg, None)
        kb.trait_clip(K, info, key)
        K.j['animations'] = [a for a in K.j['animations'] if a['name'] in kb.KEEP_CLIPS]
        K.j['asset'] = {'version': '2.0', 'generator': 'meditation_web kk_villagers', 'extras': {'credits': 'Body, rig and animations: KayKit Adventurers (CC0, Kay Lousberg). Animal head/tail: original.'}}
        os.makedirs(os.path.join(outdir, key), exist_ok=True)
        p = os.path.join(outdir, key, f'{key}.glb'); K.compact(); K.save(p)
        meta[key] = dict(base=base, u=round(float(info['body_scale']), 4)); print(p, meta[key], flush=True)
    json.dump(meta, open(os.path.join(outdir, 'villagers_meta.json'), 'w'), indent=1)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:] or list(WEAR))
