"""kaykit_animations.glb에 'Jump'(공중 자세) 더하기: 달리기의 한 장면(TB초)에 멈춰 두 팔을 벌리고 무릎을 살짝 모음.
python3 kk_jump.py in.glb out.glb [TB]"""
import sys, math
import numpy as np
import kaykit_swap as ks, kk_build as kb
from kk_pray import X, Y, Z

def main(src, dst, tb=0.2):
    L = ks.G(src)
    nm = {i: x.get('name') for i, x in enumerate(L.j['nodes'])}; idx = {v: k for k, v in nm.items()}
    ch, bd = kb.clip_data(L, 'Running_A')
    add = {'upperarm.l': [(Z, -0.9)], 'upperarm.r': [(Z, 0.9)], 'lowerarm.l': [(X, 0.3)], 'lowerarm.r': [(X, 0.3)], 'head': [(X, -0.12)], 'chest': [(X, -0.08)]}
    T = np.linspace(0, 1.0, 31); tracks = {}
    keys = set(ch) | {(idx[b], 'rotation') for b in add}
    for (node, path) in keys:
        b = nm[node]
        if (node, path) in ch: tt, vv = ch[(node, path)]; v0 = kb.sample(tt, vv, tb % bd, path)
        else: v0 = np.array(kb.rest(L, node, path), float)
        v = np.array(v0, float)
        if path == 'rotation':
            for ax, a in add.get(b, []): v = kb.qmul(v, kb.qaxis(ax, a))
            v = v / np.linalg.norm(v)
        tracks[(node, path)] = (T, np.array([v] * len(T)))
    L.j['animations'] = [a for a in L.j['animations'] if a['name'] != 'Jump']
    kb.add_clip(L, 'Jump', tracks)
    L.compact(); L.save(dst); print('saved', [a['name'] for a in L.j['animations']])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.2)
