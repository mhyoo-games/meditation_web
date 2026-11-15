"""동물 머리 메시 가볍게 만들기 (꺼짐 방지).
머리 한 개가 삼각형 5만 개라, 동물 11마리 × 그림자까지 그리면 한 장면에 150만 개가 넘어 휴대폰·노트북 그래픽 메모리가 버티지 못했어요.
격자로 가까운 꼭짓점을 묶는 방식(색·면 방향이 다르면 따로 묶음)으로 머리를 약 1/5로 줄이고, 색은 8비트로 저장해요.

python3 tools/slim_heads.py <캐릭터 GLB 폴더> [목표 삼각형 수=9000] [눈·무늬 층 목표=0(그대로)] [귀·꼬리 목표]
머리 모양을 줄이면 눈·무늬 층과 어긋나 얼굴에 얼룩이 생길 수 있어요 → 머리는 큰 목표(99999)로 그대로 두고 귀·꼬리만 줄이기도 해요
(animal-asset의 kaykit_swap이 없으면 같은 폴더의 glbmini.py를 써요)
"""
import sys, os, glob
import numpy as np
try:
    import kaykit_swap as ks
except ImportError:   # 없으면 이 폴더의 작은 GLB 도구로
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import glbmini as ks

NB = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
               [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1], [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1]], float)
NB /= np.linalg.norm(NB, axis=1, keepdims=True)


def cluster(P, N, Cc, I, h):
    q = np.floor(P / h).astype(np.int64)
    nb = np.argmax(N @ NB.T, axis=1)                     # 면 방향 14갈래 (얇은 귀 앞뒤가 붙지 않게)
    cq = np.round(Cc[:, :3] * 7).astype(np.int64)        # 색 (눈 둘레·볼 색 경계를 지킴)
    key = np.stack([q[:, 0], q[:, 1], q[:, 2], nb, cq[:, 0], cq[:, 1], cq[:, 2]], 1)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
    k = inv.max() + 1
    cnt = np.bincount(inv, minlength=k).astype(float)[:, None]
    P2 = np.zeros((k, 3)); np.add.at(P2, inv, P); P2 /= cnt
    N2 = np.zeros((k, 3)); np.add.at(N2, inv, N); N2 /= np.maximum(np.linalg.norm(N2, axis=1, keepdims=True), 1e-9)
    C2 = np.zeros((k, 4)); np.add.at(C2, inv, Cc); C2 /= cnt
    T = inv[I]
    ok = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2]); T = T[ok]
    s = np.sort(T, 1); _, u = np.unique(s, axis=0, return_index=True); T = T[np.sort(u)]
    used = np.unique(T); remap = -np.ones(k, int); remap[used] = np.arange(len(used))
    return P2[used], N2[used], C2[used], remap[T]


def slim(path, target, decal=0, ears=0):
    g = ks.G(path); j = g.j; changed = False; report = []
    for m in j['meshes']:
        for p in m['primitives']:
            mat = j['materials'][p['material']].get('name', '') if 'material' in p else ''
            if 'JOINTS_0' in p['attributes'] or not (m.get('name', '').startswith('animal-') or m.get('name', '').startswith('ear-')) or mat in ('Glow', 'DarkGlow', 'AuraGlow', 'AuraDark'): continue
            if mat == 'Decal' and not decal: continue   # 눈·무늬(데칼)는 decal 목표를 줄 때만 (곱게 줄임)
            A = p['attributes']; P = g.acc(A['POSITION']); N = g.acc(A['NORMAL']); Cc = g.acc(A['COLOR_0']) if 'COLOR_0' in A else np.ones((len(P), 4))
            I = g.acc(p['indices']).astype(np.int64).reshape(-1, 3)
            tg = (decal if mat == 'Decal' else target) if m.get('name') == 'animal-head' else (ears or target * 4 // 7)   # 꼬리·귀는 조금 더 적게
            if len(I) <= tg * 1.2: continue
            ext = (P.max(0) - P.min(0)).max(); lo, hi = ext / 400, ext / 20; best = None
            for _ in range(18):   # 목표 수에 맞는 격자 크기 찾기
                mid = (lo * hi) ** 0.5; r = cluster(P, N, Cc, I, mid)
                if len(r[3]) > tg: lo = mid
                else: hi = mid; best = r
            if best is None: best = cluster(P, N, Cc, I, hi)
            P2, N2, C2, T2 = best
            A['POSITION'] = g.add(P2.astype(np.float32), 'VEC3', 5126, 34962, minmax=True)
            A['NORMAL'] = g.add(N2.astype(np.float32), 'VEC3', 5126, 34962)
            A['COLOR_0'] = g.add(np.round(np.clip(C2, 0, 1) * 255).astype(np.uint8), 'VEC4', 5121, 34962); j['accessors'][A['COLOR_0']]['normalized'] = True
            p['indices'] = g.add(T2.reshape(-1).astype(np.uint16 if len(P2) < 65535 else np.uint32), 'SCALAR', 5123 if len(P2) < 65535 else 5125, 34963)
            report.append(f'{len(I)}→{len(T2)}'); changed = True
    if changed: g.compact(); g.save(path)
    return report


if __name__ == '__main__':
    folder = sys.argv[1]; target = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    decal = int(sys.argv[3]) if len(sys.argv) > 3 else 0   # 눈·무늬 층 목표 삼각형 수 (0 = 그대로)
    ears = int(sys.argv[4]) if len(sys.argv) > 4 else 0    # 귀·꼬리 목표 (0 = 머리 목표의 4/7)
    for f in sorted(glob.glob(os.path.join(folder, '*.glb'))):
        b = os.path.getsize(f); r = slim(f, target, decal, ears); print(os.path.basename(f), r, f'{b // 1024}KB → {os.path.getsize(f) // 1024}KB')
