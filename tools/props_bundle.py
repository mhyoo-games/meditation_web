"""Quaternius(CC0) 모델들을 하나의 props.glb로 묶는다: 모델마다 메시 하나(정점 색), 이름 = 모델 이름.
단풍 나무는 잎 색을 바꾼 변형(~r 빨강, ~o 주황, ~g 노랑)도 만든다.
usage: python3 -I props_bundle.py <used.json> <out.glb>"""
import sys, json, struct
import numpy as np
sys.path.insert(0, '/home/claude/tools')
from kaykit_swap import G, worlds, hexlin
BASE = '/home/claude/gh_assets/qs/public/glb/'
LEAF = {'Orange', 'LightOrange'}
VARS = {'r': ('#B8281A', '#D8442A'), 'o': ('#D2601A', '#EE8A22'), 'g': ('#D89A1C', '#F2C640')}
RECOLOR = {'RoofTiles': '#6E3A2C', 'Windows': '#2A2620'}

def load(m):
    for p in ('nature_pack', 'medieval_village_pack'):
        try: return G(BASE + p + '/' + m + '.glb')
        except FileNotFoundError: pass

def flatten(g):
    WM = worlds(g); P, N, C, I, L = [], [], [], [], []; base = 0
    for ni, n in enumerate(g.j['nodes']):
        if 'mesh' not in n or ni not in WM: continue
        M = WM[ni]; R = M[:3, :3]; Rn = np.linalg.inv(R).T
        for pr in g.j['meshes'][n['mesh']]['primitives']:
            p = g.acc(pr['attributes']['POSITION']); nn = g.acc(pr['attributes']['NORMAL'])
            mt = g.j['materials'][pr['material']]; nm = mt['name']
            col = np.array(mt.get('pbrMetallicRoughness', {}).get('baseColorFactor', [1, 1, 1, 1])[:3])
            if nm in RECOLOR: col = hexlin(RECOLOR[nm])
            idx = g.acc(pr['indices']).astype(np.uint32).ravel() if 'indices' in pr else np.arange(len(p), dtype=np.uint32)
            P.append(p @ R.T + M[:3, 3]); nv = nn @ Rn.T; N.append(nv / np.linalg.norm(nv, axis=1, keepdims=True).clip(1e-9))
            C.append(np.tile(col, (len(p), 1))); L.append(np.full(len(p), 1.0 if nm in LEAF else (0.5 if nm == 'LightOrange' else 0.0)))
            if nm == 'LightOrange': L[-1][:] = 2.0
            I.append(idx + base); base += len(p)
    return np.concatenate(P), np.concatenate(N), np.concatenate(C), np.concatenate(I), np.concatenate(L)

def main(used, out):
    b = bytearray(); views, accs, meshes, nodes = [], [], [], []
    def push(arr, typ, comp, target, mm=False, norm=False):
        while len(b) % 4: b.append(0)
        raw = np.ascontiguousarray(arr).tobytes(); views.append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw), 'target': target}); b.extend(raw)
        a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': int(arr.shape[0]), 'type': typ}
        if norm: a['normalized'] = True
        if mm: a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
        accs.append(a); return len(accs) - 1
    def add(name, P, N, C, I, share=None):
        Cc = np.concatenate([np.clip(C, 0, 1), np.ones((len(C), 1))], 1)
        if share is None: share = (push(P.astype(np.float32), 'VEC3', 5126, 34962, True), None, push(I.astype(np.uint16), 'SCALAR', 5123, 34963) if I.max() < 65535 else push(I.astype(np.uint32), 'SCALAR', 5125, 34963))
        prim = {'attributes': {'POSITION': share[0], 'COLOR_0': push(np.round(Cc * 255).astype(np.uint8), 'VEC4', 5121, 34962, norm=True)},
                'indices': share[2], 'material': 0}
        meshes.append({'name': name, 'primitives': [prim]}); nodes.append({'name': name, 'mesh': len(meshes) - 1}); return share
    for m in used:
        g = load(m); P, N, C, I, L = flatten(g)
        sh = add(m, P, N, C, I)
        if (L > 0).any() and ('Autumn' in m):
            for k, (c1, c2) in VARS.items():
                Cv = C.copy(); Cv[L == 1] = hexlin(c1); Cv[L == 2] = hexlin(c2); add(m + '~' + k, P, N, Cv, I, sh)
    while len(b) % 4: b.append(0)
    j = {'asset': {'version': '2.0', 'generator': 'props_bundle (Quaternius CC0 models)'}, 'scene': 0, 'scenes': [{'nodes': list(range(len(nodes)))}],
         'nodes': nodes, 'meshes': meshes, 'materials': [{'name': 'Prop', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.9}}],
         'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(b)}]}
    js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    open(out, 'wb').write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(b), 0x004E4942) + bytes(b))
    print('meshes', len(meshes), 'bytes', 28 + len(js) + len(b), 'verts', sum(accs[mm['primitives'][0]['attributes']['POSITION']]['count'] for mm in meshes))

main(json.load(open(sys.argv[1])), sys.argv[2])
