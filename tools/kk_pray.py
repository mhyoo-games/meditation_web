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
def smoother(x): x = max(0.0, min(1.0, x)); return x * x * x * (x * (x * 6 - 15) + 10)


BOW_T = 7.0


def bow_k(t, lag=0.0):     # 0 → 1 → 0, 부드럽게 (시작·끝이 같아 반복해도 이음매가 없음)
    t -= lag
    if t < 1.2: return 0.0
    if t < 3.1: return smoother((t - 1.2) / 1.9)
    if t < 4.3: return 1.0
    if t < 6.2: return 1 - smoother((t - 4.3) / 1.9)
    return 0.0


def bow_curve(t):          # 7초: 합장 → 허리부터 차례로 숙임(가슴·머리가 조금씩 늦게) → 머무름(숨) → 천천히 일어남
    ks, kc, kh = bow_k(t), bow_k(t, 0.15), bow_k(t, 0.3)
    br = 0.03 * math.sin(t / BOW_T * 2 * math.pi * 3) * bow_k(t)       # 엎드려 있는 동안 숨쉬기
    return {'spine': 0.62 * ks + br, 'chest': 0.48 * kc + br * 0.5, 'head': 0.08 + 0.32 * kh - 0.12 * kh * kh}


def slerp(a, b, w):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); d = float(np.dot(a, b))
    if d < 0: b = -b; d = -d
    if d > 0.9995: v = a + (b - a) * w; return v / np.linalg.norm(v)
    th = math.acos(d); return (math.sin((1 - w) * th) * a + math.sin(w * th) * b) / math.sin(th)


def compose_bow(L, name='Bow'):
    """앉은 자세(Sit_Floor_Idle) + 팔: 합장(Use_Item) → 숙이면서 두 손을 바닥 앞으로(PickUp 중간) → 다시 합장"""
    nm = {i: x.get('name') for i, x in enumerate(L.j['nodes'])}; idx = {v: k for k, v in nm.items()}
    ch, bd = kb.clip_data(L, 'Sit_Floor_Idle')
    joined = pose(L, 'Use_Item', 0.5)
    import json as _j; RA = _j.loads(os.environ.get('REACH', '{"upperarm.l": [1, 0, 0, 1.8], "upperarm.r": [1, 0, 0, 1.8], "lowerarm.l": [1, 0, 0, 0.4], "lowerarm.r": [1, 0, 0, 0.4]}'))   # {bone: [ax, ay, az, angle]}
    reach = {}
    for k, q in joined.items():
        if k[1] != 'rotation' or nm[k[0]] not in RA: continue
        ax, ay, az, ang = RA[nm[k[0]]]; reach[k] = kb.qmul(np.array(q), kb.qaxis([ax, ay, az], ang))
    T = np.linspace(0, BOW_T, int(BOW_T * 30) + 1)
    keys = set(ch) | {k for k in joined if nm[k[0]] in ARMS and k[1] == 'rotation'} | {(idx[b], 'rotation') for b in ('spine', 'chest', 'head')}
    tracks = {}
    for (node, path) in keys:
        b = nm[node]; vals = []
        for t in T:
            if (node, path) in ch: tt, vv = ch[(node, path)]; v = kb.sample(tt, vv, t % bd if bd > 0 else 0, path)
            else: v = np.array(kb.rest(L, node, path), float)
            if b in ARMS and path == 'rotation' and (node, path) in joined:
                w = bow_k(t, -0.1) ** 1.3          # 팔은 허리보다 살짝 먼저 내려가고 늦게 올라옴
                v = slerp(np.array(joined[(node, path)]), np.array(reach.get((node, path), joined[(node, path)])), w * 0.85)
            if path == 'rotation':
                a = bow_curve(t).get(b, 0.0)
                if a: v = kb.qmul(v, kb.qaxis([1, 0, 0], a)); v = v / np.linalg.norm(v)
            vals.append(v)
        tracks[(node, path)] = (T, np.array(vals))
    L.j['animations'] = [a for a in L.j['animations'] if a['name'] != name]
    kb.add_clip(L, name, tracks)


def compose_multi(L, name, base, dur, arms=None, fn=None, fps=30):
    """base 동작을 dur 동안 반복 + arms 팔 자세 + fn(t) -> {bone: [(axis, angle), ...]} (뼈 자기 축 기준 회전)"""
    nm = {i: x.get('name') for i, x in enumerate(L.j['nodes'])}; idx = {v: k for k, v in nm.items()}
    ch, bd = kb.clip_data(L, base); ap = pose(L, *arms) if arms else {}
    T = np.linspace(0, dur, int(dur * fps) + 1)
    bones = set()
    for t in np.linspace(0, dur, 9): bones |= set((fn(t) if fn else {}).keys())
    keys = set(ch) | {k for k in ap if nm[k[0]] in ARMS and k[1] == 'rotation'} | {(idx[b], 'rotation') for b in bones}
    tracks = {}
    for (node, path) in keys:
        b = nm[node]; vals = []
        for t in T:
            if path == 'rotation' and b in ARMS and (node, path) in ap: v = np.array(ap[(node, path)], float)
            elif (node, path) in ch: tt, vv = ch[(node, path)]; v = kb.sample(tt, vv, t % bd if bd > 0 else 0, path)
            else: v = np.array(kb.rest(L, node, path), float)
            if path == 'rotation' and fn:
                for ax, a in fn(t).get(b, []):
                    if a: v = kb.qmul(v, kb.qaxis(ax, a))
                v = v / np.linalg.norm(v)
            vals.append(v)
        tracks[(node, path)] = (T, np.array(vals))
    L.j['animations'] = [a for a in L.j['animations'] if a['name'] != name]
    kb.add_clip(L, name, tracks)


X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
TAU = 2 * math.pi


def sing(t):       # 4초: 악보를 든 손, 몸을 좌우로 천천히 흔들며 고개를 살짝 끄덕
    a = math.sin(TAU * t / 4.0); b = math.sin(TAU * t / 2.0)
    return {'spine': [(Z, 0.05 * a)], 'chest': [(Z, 0.04 * a), (X, 0.03 + 0.02 * b)], 'head': [(X, 0.12 + 0.06 * b), (Z, -0.05 * a)],
            'upperarm.l': [(X, 0.35)], 'upperarm.r': [(X, 0.35)]}


MOK_T = 2.4        # 2.4초에 네 번 (0.15, 0.75, 1.35, 1.95초에 딱)
MOK_HITS = [0.15, 0.75, 1.35, 1.95]


def moktak(t):     # 앉아서 왼손은 합장 반쪽, 오른손 채로 톡톡
    ph = (t % 0.6) / 0.6
    up = 0.5 * (1 - math.cos(TAU * ph)) if ph > 0.25 else (1 - ph / 0.25) * 0.15   # 0.15초에 가장 아래(딱), 다시 들어 올림
    lift = 0.55 * smooth((ph - 0.25) / 0.45) * (1 - smooth((ph - 0.75) / 0.25)) if ph > 0.25 else 0.0
    return {'upperarm.r': [(X, 0.9 + 0.25 * lift)], 'lowerarm.r': [(X, 0.35 + 0.6 * lift)], 'head': [(X, 0.22)], 'chest': [(X, 0.08)],
            'upperarm.l': [(X, 0.5)]}


def main(src, dst):
    L = ks.G(src)
    compose(L, 'Pray_Stand', 'Idle', 4.0, arms=('Use_Item', 0.5), bend=lambda t: {'head': 0.28, 'chest': 0.06})
    compose(L, 'Pray_Sit', 'Sit_Chair_Idle', 4.0, arms=('Use_Item', 0.5), bend=lambda t: {'head': 0.3, 'chest': 0.08})
    compose_bow(L)
    compose_multi(L, 'Sing', 'Idle', 4.0, arms=('Use_Item', 0.5), fn=sing)
    compose_multi(L, 'Moktak', 'Sit_Floor_Idle', MOK_T, arms=('Use_Item', 0.5), fn=moktak)
    keep = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
    if keep: L.j['animations'] = [a for a in L.j['animations'] if a['name'] in keep]
    L.compact(); L.save(dst); print('saved', dst, [a['name'] for a in L.j['animations']])


if __name__ == '__main__':
    main(*sys.argv[1:3])
