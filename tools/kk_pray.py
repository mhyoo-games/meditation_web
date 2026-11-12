"""절하기·기도 동작을 KayKit 동작에서 합성해 애니메이션 라이브러리에 더한다.
usage: python3 -I kk_pray.py <in anim lib glb> <out glb>
"""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaykit_swap as ks, kk_build as kb

ARMS = [f'{b}.{s}' for b in ('upperarm', 'lowerarm', 'wrist', 'hand') for s in 'lr']


def pose(L, clip, t):
    ch, _ = kb.clip_data(L, clip)
    return {k: kb.sample(T, V, min(t, T[-1]), k[1]) for k, (T, V) in ch.items()}


def compose(L, name, base, dur, arms=None, bend=None, n=None):
    """base: clip name (looped over dur); arms: (clip, t) constant arm pose; bend: f(t)->{bone: angle(rad) about local X}"""
    nm = {i: x.get('name') for i, x in enumerate(L.j['nodes'])}; idx = {v: k for k, v in nm.items()}
    ch, bd = kb.clip_data(L, base)
    ap = pose(L, *arms) if arms else {}
    T = np.linspace(0, dur, int(dur * 15) + 1)
    tracks = {}
    for (node, path), (tt, vv) in ch.items():
        vals = []
        for t in T:
            v = kb.sample(tt, vv, t % bd if bd > 0 else 0, path)
            b = nm[node]
            if b in ARMS and (node, path) in ap: v = ap[(node, path)]
            if path == 'rotation' and bend:
                a = bend(t).get(b, 0.0)
                if a: v = kb.qmul(v, kb.qaxis([1, 0, 0], a)); v = v / np.linalg.norm(v)
            vals.append(v)
        tracks[(node, path)] = (T, np.array(vals))
    # 움직임이 없던 뼈에도 숙이기를 넣어야 할 때
    if bend:
        for b in ('spine', 'chest', 'head'):
            k = (idx[b], 'rotation')
            if k not in tracks:
                r = kb.rest(L, *k); tracks[k] = (T, np.array([kb.qmul(r, kb.qaxis([1, 0, 0], bend(t).get(b, 0))) for t in T]))
    L.j['animations'] = [a for a in L.j['animations'] if a['name'] != name]
    kb.add_clip(L, name, tracks)


def smooth(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def bow_curve(t):          # 6초: 합장 → 천천히 숙여 이마를 바닥 쪽으로 → 머무름 → 일어남
    if t < 1.0: k = 0
    elif t < 2.4: k = smooth((t - 1.0) / 1.4)
    elif t < 3.6: k = 1
    elif t < 5.0: k = 1 - smooth((t - 3.6) / 1.4)
    else: k = 0
    return {'spine': 0.55 * k, 'chest': 0.45 * k, 'head': 0.25 * k + 0.08}


def main(src, dst):
    L = ks.G(src)
    compose(L, 'Pray_Stand', 'Idle', 4.0, arms=('Use_Item', 0.5), bend=lambda t: {'head': 0.28, 'chest': 0.06})
    compose(L, 'Pray_Sit', 'Sit_Chair_Idle', 4.0, arms=('Use_Item', 0.5), bend=lambda t: {'head': 0.3, 'chest': 0.08})
    compose(L, 'Bow', 'Sit_Floor_Idle', 6.0, arms=('Use_Item', 0.5), bend=bow_curve)
    L.compact(); L.save(dst); print('saved', dst, [a['name'] for a in L.j['animations']])


if __name__ == '__main__':
    main(*sys.argv[1:3])
