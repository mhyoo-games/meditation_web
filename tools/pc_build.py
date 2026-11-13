"""그림책풍(Pepper&Carrot 느낌) 견습 마법사 동물 11종: KayKit Mage 몸체(모자·망토 살림) + 그림책풍 눈 머리 + 붓칠 느낌 정점 색.
usage: python3 -I pc_build.py <kaykit gltf dir> <pc heads dir> <out dir> [key ...]
"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kk_build as kb
from kaykit_swap import worlds, hexlin

DROP = ["Spellbook", "Spellbook_open", "1H_Wand", "2H_Staff"]          # 모자·망토는 남김
# robe(겉옷), trim(옷깃·소매), hat(모자), band(모자 띠·허리띠), cape(망토), pants
WEAR = {
    'hamster':  ('#5FB8A9', '#F1E6D2', '#2E3A5A', '#C8A040', '#3B4A6B', '#2E3A5A'),
    'rabbit':   ('#E0789F', '#FFF1F4', '#7A2E4A', '#F2C45A', '#B04466', '#5A2238'),
    'cat':      ('#6A4A9A', '#EDE0CA', '#2A2238', '#C8963A', '#4A2E6A', '#2A2238'),
    'dog':      ('#3A62A6', '#EDE0CA', '#22304E', '#C8A040', '#C8573A', '#22304E'),
    'lion':     ('#B0302A', '#F2C45A', '#5A1612', '#F2C45A', '#2E3A6E', '#3A1A12'),
    'bear':     ('#C08A2E', '#F1E2C2', '#4A3020', '#8E2F3A', '#6E8E4E', '#4A3020'),
    'panda':    ('#4E7E4E', '#FAFAF5', '#24222A', '#D94E4E', '#2E4E2E', '#24222A'),
    'fox':      ('#2E6E8E', '#E8D9B8', '#1E2E3E', '#E8A030', '#8E2F3A', '#1E2E3E'),
    'raccoon':  ('#5A6E96', '#EDE0CA', '#2E2E36', '#B8862A', '#8A6AB0', '#2E2E36'),
    'squirrel': ('#A84E2E', '#FFF1DC', '#4E2A1A', '#E8B040', '#5E7A3A', '#4E2A1A'),
    'deer':     ('#E3D3B6', '#8A5A3A', '#4A6E3A', '#E8B040', '#6E4A8E', '#5A3A22'),
}
FUR = {'hamster': '#F4A65A', 'rabbit': '#7A5A4A', 'cat': '#9AA0AE', 'dog': '#D9873A', 'lion': '#F0C163', 'bear': '#8E5E3B', 'panda': '#24222A',
       'fox': '#E8823A', 'raccoon': '#8E8C96', 'squirrel': '#C9783C', 'deer': '#B97C4A'}
HAT_TILT = {'rabbit': 0.0, 'deer': 0.0}       # 귀·뿔이 긴 동물은 모자를 똑바로


def node_by_name(K, name):
    for i, n in enumerate(K.j['nodes']):
        if n.get('name') == name: return i
    return None


def prim_points(K, mi):
    return np.concatenate([K.acc(p['attributes']['POSITION']) for p in K.j['meshes'][mi]['primitives']])


def fit_hat(K, key):
    """KayKit 마법사 모자를 동물 머리 위에 맞춤 (머리뼈 기준 위치·크기·기울기)"""
    W = worlds(K); hat = node_by_name(K, 'Mage_Hat'); head = node_by_name(K, 'animal-head')
    par = {c: i for i, n in enumerate(K.j['nodes']) for c in n.get('children', [])}
    hb = par[hat]; Hinv = np.linalg.inv(W[hb])
    def local_pts(ni):
        P = prim_points(K, K.j['nodes'][ni]['mesh']); Pw = (W[ni] @ np.c_[P, np.ones(len(P))].T).T
        return (Hinv @ Pw.T).T[:, :3]
    pts = [local_pts(head)]
    for nm in ('ear-left', 'ear-right'):
        e = node_by_name(K, nm)
        if e is not None and 'mesh' in K.j['nodes'][e]: pass      # 귀는 모자를 뚫고 나와도 됨 (크기 계산에서 뺌)
    H = np.concatenate(pts); lo, hi = H.min(0), H.max(0); w = hi[0] - lo[0]; h = hi[1] - lo[1]
    HP = prim_points(K, K.j['nodes'][hat]['mesh']); hw = HP[:, 0].max() - HP[:, 0].min()
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    mid = H[(np.abs(H[:, 0] - cx) < 0.18 * w) & (np.abs(H[:, 2] - cz) < 0.3 * (hi[2] - lo[2]))]   # 머리 가운데 기둥 (귀·뿔 제외)
    top = np.percentile(mid[:, 1], 99.5) if len(mid) > 20 else hi[1]
    w = min(w, (top - lo[1]) * 1.25); s = w * 0.98 / hw
    brim_y = top - (top - lo[1]) * 0.2
    n = K.j['nodes'][hat]; n['scale'] = [s, s, s]
    n['translation'] = [float(cx), float(brim_y - s * (-0.06)), float(cz - 0.04 * w)]
    tilt = HAT_TILT.get(key, 0.16)
    q = kb.qmul(kb.qaxis([0, 0, 1], tilt), kb.qaxis([1, 0, 0], -0.12)); n['rotation'] = [float(v) for v in q]


def hash3(P):
    return np.modf(np.sin(P @ np.array([12.9898, 78.233, 37.719])) * 43758.5453)[0] % 1.0


def vnoise(P):
    i = np.floor(P); f = P - i; f = f * f * (3 - 2 * f); out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * hash3(i + np.array([dx, dy, dz]))
    return out


def paint(K):
    """붓칠 느낌: 위는 밝고 따뜻하게, 아래는 살짝 어둡고 차갑게 + 붓자국 같은 낮은 주파수 얼룩"""
    done = set()
    for n in K.j['nodes']:
        if 'mesh' not in n or n['mesh'] in done: continue
        done.add(n['mesh'])
        for p in K.j['meshes'][n['mesh']]['primitives']:
            if 'COLOR_0' not in p['attributes'] or 'NORMAL' not in p['attributes']: continue
            mat = K.j['materials'][p.get('material', 0)].get('name', '')
            if 'Glow' in mat: continue
            P = K.acc(p['attributes']['POSITION']); N = K.acc(p['attributes']['NORMAL']); Cc = K.acc(p['attributes']['COLOR_0']).copy()
            d = np.linalg.norm(P.max(0) - P.min(0)) + 1e-6; Q = P / d
            ny = N[:, 1] / (np.linalg.norm(N, axis=1) + 1e-6)
            hemi = 0.86 + 0.2 * (0.5 + 0.5 * ny)
            nz = vnoise(Q * 7.0) * 0.6 + vnoise(Q * 17.0 + 3.1) * 0.4
            k = hemi * (0.93 + 0.14 * nz)
            warm = np.c_[1 + 0.05 * (ny > 0) * nz, np.ones(len(ny)), 1 - 0.05 * (ny > 0) * nz]
            cool = np.c_[1 - 0.03 * (ny < -0.2), np.ones(len(ny)), 1 + 0.04 * (ny < -0.2)]
            rgb = np.clip(Cc[:, :3] * k[:, None] * warm * cool, 0, 1)
            Cc[:, :3] = rgb
            p['attributes']['COLOR_0'] = K.add(Cc.astype(np.float32), 'VEC4', target=34962)


def main(kdir, ourdir, outdir, keys):
    meta = {}
    for key in keys:
        robe, trim, hat, band, cape, pants = WEAR[key]; fur = FUR[key]
        cfg = dict(base='Mage', drop=DROP, head_drop=0.02, inflate={},
                   cells={"0,1": robe, "2,2": trim, "0,2": trim, "4,0": trim, "7,1": pants, "2,1": cape, "5,0": band},
                   mesh_cells={"Arm": {"0,1": robe, "4,0": trim, "7,2": fur}, "Hat": {"1,1": hat, "3,0": band, "5,0": band}})
        K, kn, info = kb.build(os.path.join(kdir, 'Mage.glb'), os.path.join(ourdir, key, f'{key}_stage1.glb'), cfg, None)
        fit_hat(K, key); paint(K)
        kb.trait_clip(K, info, key)
        K.j['animations'] = [a for a in K.j['animations'] if a['name'] in kb.KEEP_CLIPS]
        K.j['asset'] = {'version': '2.0', 'generator': 'animal-asset pc_build', 'extras': {'credits': 'Body, rig, hat, cape and animations: KayKit Adventurers (CC0, Kay Lousberg). Animal heads/tails: original, picture-book style inspired by Pepper&Carrot (David Revoy, CC BY 4.0).'}}
        os.makedirs(os.path.join(outdir, key), exist_ok=True)
        p = os.path.join(outdir, key, f'{key}_witch.glb'); K.compact(); K.save(p)
        meta[key] = dict(base='Mage', u=round(float(info['body_scale']), 4)); print(p, meta[key], flush=True)
    json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:] or list(WEAR))
