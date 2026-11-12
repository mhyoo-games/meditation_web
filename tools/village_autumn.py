"""단풍마을 — 힐링 산책용 아늑한 가을 마을 (절, 교회, 성당).
사용법: python3 village_autumn.py <출력폴더> [check]
출력: village.glb, village_layout.js
단위 미터, 캐릭터 키 약 0.7m 기준 (새싹마을과 같은 축척)
"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hamster as mh
from make_hamster import C, Rx, Ry, Rz, torus, lathe, CONE
import village as v1
from village import box, cyl, cone, ell, roof_gable, CYL, CYL8, PYR4, PRISM, bench, lamp, fence, flower, rock
from village2 import pagoda_roof

R_WORLD = 40.0
TEMPLE = (0.0, -23.0); CHURCH = (-19.0, 1.5); CATHEDRAL = (20.0, 3.0); POND = (-7.5, 12.5)
MAPLES = ['#D9382B', '#E8552E', '#F07A2E', '#C42F2F', '#F29A38']
GINKGO = ['#F2C230', '#F5D04A', '#E8B428']
rng = np.random.default_rng(11)


# ---------------------------------------------------------------- 지형
PATHS = [((0, 4), (0, -13.5)), ((0, -13.5), (0, -19.5)), ((0, 0), (-15.6, 1.5)), ((0, 0), (16.2, 3.0)),
         ((0, 0), (0, 14)), ((0, 6), (-6, 9.5)), ((-3, 0.5), (-4, 6)), ((3, 0.5), (5, 7))]


def height(x, z):
    h = 0.0
    h += 0.9 * math.exp(-((x - TEMPLE[0]) ** 2 / 90 + (z - TEMPLE[1]) ** 2 / 60))      # 절은 낮은 언덕 위
    r = math.hypot(x, z); h += 3.0 * max(0.0, min(1.0, (r - 31.0) / 7.0)) ** 2        # 가장자리 산
    h += 0.18 * math.sin(x * 0.31) * math.cos(z * 0.27)
    h -= 0.5 * math.exp(-((x - POND[0]) ** 2 + (z - POND[1]) ** 2) / 7.0)
    for c, rad in ((TEMPLE, 7.5), (CHURCH, 5.5), (CATHEDRAL, 7.0), ((0, 0), 5.0)):    # 건물 터는 평평하게
        d = math.hypot(x - c[0], z - c[1])
        if d < rad + 3:
            k = max(0.0, min(1.0, (d - rad) / 3.0)); base = flat_h(c)
            h = base * (1 - k) + h * k
    return h


def flat_h(c):
    if c == TEMPLE: return 0.9
    return 0.0


def seg_dist(px, pz, a, b): return v1.seg_dist(px, pz, a, b)


def terrain(P, R=R_WORLD, n=180):
    xs = np.linspace(-R, R, n); X, Z = np.meshgrid(xs, xs)
    Hh = np.vectorize(height)(X, Z); V = np.stack([X, Hh, Z], -1).reshape(-1, 3)
    i, j = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (i * n + j).reshape(-1)
    I = np.concatenate([np.stack([a, a + n, a + 1], 1), np.stack([a + 1, a + n, a + n + 1], 1)])
    nz = rng.random(len(V))
    g = [C('#A3B865'), C('#98B05E'), C('#AFBD6C'), C('#B8B266')]       # 가을 잔디 (살짝 누런 초록)
    col = np.stack([g[k] for k in (nz * 4).astype(int).clip(0, 3)])
    d = np.min([seg_dist(V[:, 0], V[:, 2], p, q) for p, q in PATHS], axis=0)
    onp = d < 0.85
    tile = ((np.floor(V[:, 0] * 1.8) + np.floor(V[:, 2] * 1.8)) % 2 == 0)
    col[onp] = np.where(tile[onp, None], C('#D8C7A2'), C('#CDBB93'))
    col[(d >= 0.85) & (d < 1.0)] = C('#A89474')
    rr = np.hypot(V[:, 0], V[:, 2]); pl = rr < 4.4
    col[pl] = np.where((np.floor(rr * 1.6) % 2 == 0)[pl, None], C('#E2D6BE'), C('#D5C8AE'))
    # 낙엽 무늬 (나무 근처는 바닥이 붉게)
    leaf = (rng.random(len(V)) < 0.07) & ~onp & ~pl
    col[leaf] = col[leaf] * 0.55 + np.stack([C(MAPLES[k % 5]) for k in rng.integers(0, 5, leaf.sum())]) * 0.45
    col[V[:, 1] > 1.8] = C('#8E9A58')
    col[np.hypot(V[:, 0] - POND[0], V[:, 2] - POND[1]) < 2.9] = C('#7E8F5A')
    fn = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]); flip = fn[:, 1] < 0; I[flip] = I[flip][:, ::-1]
    fn = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]); Nv = np.zeros_like(V)
    for k in range(3): np.add.at(Nv, I[:, k], fn)
    Nv /= np.linalg.norm(Nv, axis=1, keepdims=True); P.g['toon'].append((V, Nv, col, I))
    # 연못 물
    cyl(P, (POND[0], -0.32, POND[1]), 2.7, 0.06, C('#7FB8D0', 0.85), glow=True)
    for k in range(6):
        a = k * 1.1; p = (POND[0] + math.cos(a) * 1.6, -0.24, POND[1] + math.sin(a) * 1.3)
        cyl(P, p, 0.28, 0.02, C('#5E9A4A'))
        if k % 2 == 0: lotus(P, (p[0] + 0.1, -0.22, p[2]))
    for k in range(14):
        a = 2 * math.pi * k / 14; rock(P, (POND[0] + math.cos(a) * 2.85, -0.15, POND[1] + math.sin(a) * 2.85), 0.8 + 0.3 * (k % 3))


def lotus(P, p):
    for k in range(7):
        a = 2 * math.pi * k / 7
        ell(P, np.array(p) + np.array([math.cos(a) * 0.06, 0.06, math.sin(a) * 0.06]), (0.05, 0.08, 0.03), C('#F7A8C4'), sub=1, R=Ry(-a) @ Rz(0.5))
    ell(P, np.array(p) + np.array([0, 0.08, 0]), 0.03, C('#FFE07A'), sub=1)


# ---------------------------------------------------------------- 나무
def maple(P, p, s=1.0, cols=None):
    cols = cols or MAPLES
    cyl(P, p, 0.13 * s, 1.1 * s, C('#6E4630'), n=8)
    blobs = [((0, 1.55, 0), 0.8), ((0.5, 1.35, 0.2), 0.55), ((-0.5, 1.4, -0.15), 0.58), ((0.1, 2.05, 0.05), 0.55), ((-0.15, 1.6, 0.5), 0.5), ((0.2, 1.6, -0.5), 0.5)]
    base = rng.integers(0, len(cols))
    for k, (o, r) in enumerate(blobs):
        ell(P, np.array(p) + np.array(o) * s, r * s, C(cols[(base + k) % len(cols)]), sub=1)
    for k in range(10):                                   # 떨어진 잎
        a = rng.random() * 6.28; rr = 0.4 + rng.random() * 1.2
        ell(P, np.array(p) + np.array([math.cos(a) * rr * s, 0.015, math.sin(a) * rr * s]), (0.09, 0.01, 0.06), C(cols[k % len(cols)]), sub=0)


def ginkgo(P, p, s=1.0):
    cyl(P, p, 0.12 * s, 1.0 * s, C('#6E4F36'), n=8)
    for k, (y, r) in enumerate(((1.2, 0.75), (1.75, 0.62), (2.25, 0.45), (2.65, 0.28))):
        ell(P, np.array(p) + np.array([0.05 * (k % 2), y, 0]) * s, (r * s, 0.42 * s, r * s), C(GINKGO[k % 3]), sub=1)
    for k in range(8):
        a = rng.random() * 6.28; rr = 0.3 + rng.random() * 1.0
        ell(P, np.array(p) + np.array([math.cos(a) * rr * s, 0.015, math.sin(a) * rr * s]), (0.07, 0.01, 0.06), C(GINKGO[k % 3]), sub=0)


def pine(P, p, s=1.0):
    cyl(P, p, 0.1 * s, 0.55 * s, C('#6A4A30'), n=8)
    for k in range(3): cone(P, np.array(p) + np.array([0, (0.45 + 0.5 * k) * s, 0]), (0.8 - 0.2 * k) * s, 0.95 * s, C(['#3E7A4A', '#46885A', '#539664'][k]))


def bush(P, p, s=1.0, col='#7A9A4A'):
    for o in ((0, 0.25, 0), (0.25, 0.2, 0.1), (-0.22, 0.2, -0.05)): ell(P, np.array(p) + np.array(o) * s, 0.3 * s, C(col), sub=1)


def pumpkin(P, p, s=1.0):
    for k in range(6):
        a = 2 * math.pi * k / 6; ell(P, np.array(p) + np.array([math.cos(a) * 0.08 * s, 0.13 * s, math.sin(a) * 0.08 * s]), (0.1 * s, 0.12 * s, 0.1 * s), C('#E8812A'), sub=1)
    cyl(P, np.array(p) + np.array([0, 0.24 * s, 0]), 0.02 * s, 0.07 * s, C('#5A6A2A'), n=8)


def hay(P, p, ry=0.0):
    P.add(CYL, Ry(ry) @ Rz(math.pi / 2) @ np.diag([0.35, 0.8, 0.35]), np.array(p) + Ry(ry) @ np.array([0.4, 0.35, 0]), C('#E3C46A'))


def lantern_string(P, a, b, n=9, h=2.2):
    cols = ['#FF5A5A', '#FF9AC2', '#FFD25A', '#7FD36A', '#FF7F3A']
    a, b = np.array(a, float), np.array(b, float)
    for k in range(n):
        t = (k + 0.5) / n; q = a + (b - a) * t; q[1] = h - 0.35 * math.sin(math.pi * t)
        ell(P, q, (0.12, 0.15, 0.12), C(cols[k % 5]), sub=1, glow=True)
        cyl(P, q + np.array([0, -0.17, 0]), 0.03, 0.05, C('#F2E6B0'), n=8, glow=True)
    for e in (a, b): cyl(P, (e[0], e[1], e[2]), 0.05, h + 0.1, C('#7A4A2E'), n=8)


# ---------------------------------------------------------------- 오두막 (동물 주민 집)
def cottage(P, wall='#F3E3C3', roof='#B5462E', w=1.7, d=1.5, h=1.25, chimney=True, pots=True):
    box(P, (0, 0.12, 0), (w + 0.1, 0.12, d + 0.1), C('#A89A86'))
    box(P, (0, 0.24 + h, 0), (w, h, d), C(wall))
    for x in (-w, w):
        for z in (-d, d): box(P, (x, 0.24 + h, z), (0.07, h, 0.07), C('#7A4E30'))
    box(P, (0, 0.24 + 2 * h, 0), (w + 0.05, 0.06, d + 0.05), C('#7A4E30'))
    roof_gable(P, (0, 0.3 + 2 * h, 0), 2 * w, 1.15, 2 * d, C(roof), over=0.28)
    box(P, (0, 0.24 + 0.62, d + 0.02), (0.32, 0.62, 0.03), C('#7A4A2E'))       # 문
    ell(P, (0.2, 0.24 + 0.62, d + 0.06), 0.035, C('#F2C14E'), sub=1)
    for x in (-w * 0.6, w * 0.6):                                                # 따뜻한 창문
        box(P, (x, 0.24 + h * 1.15, d + 0.02), (0.28, 0.26, 0.03), C('#FFD98A'), glow=True)
        box(P, (x, 0.24 + h * 1.15, d + 0.05), (0.3, 0.02, 0.02), C('#7A4E30')); box(P, (x, 0.24 + h * 1.15, d + 0.05), (0.02, 0.28, 0.02), C('#7A4E30'))
        if pots:
            box(P, (x, 0.24 + h * 0.82, d + 0.12), (0.3, 0.06, 0.08), C('#8A5A32'))
            for k in range(3): ell(P, (x - 0.18 + 0.18 * k, 0.24 + h * 0.82 + 0.1, d + 0.12), 0.07, C(['#E0483A', '#F2A33A', '#E85A8A'][k]), sub=1)
    box(P, (-w * 0.6, 0.24 + h * 1.15, -d - 0.02), (0.28, 0.26, 0.03), C('#FFD98A'), glow=True)
    if chimney:
        box(P, (w * 0.5, 0.3 + 2 * h + 0.8, -d * 0.3), (0.18, 0.5, 0.18), C('#9A5A44'))
    for k in range(3): box(P, (-w - 0.25, 0.12 + 0.13 * k, -0.3 + 0.1 * (k % 2)), (0.14, 0.06, 0.4), C('#8A5A36'))   # 장작
    return dict(door=(0, 0, d + 0.9))


# ---------------------------------------------------------------- 절 (한국 사찰)
def temple(P):
    ST, RED, GRN, CREAM, TILE = C('#B9B2A6'), C('#9E2F27'), C('#2E7D6B'), C('#F2E8D2'), C('#4C5058')
    # 대웅전
    box(P, (0.6, 0.35, 2.4), (6.2, 0.35, 5.0), C('#C9C1B2'))                   # 경내 돌마당 (높이 0.7)
    for x in np.arange(-5.4, 6.9, 0.9): box(P, (x, 0.705, 2.4), (0.01, 0.002, 5.0), C('#B5AC9C'))
    box(P, (0, 0.85, 0), (3.6, 0.15, 2.6), ST)                                     # 대웅전 기단
    for k in range(4): box(P, (0, 0.09 + 0.175 * k, 8.15 - 0.25 * k), (1.6, 0.09 + 0.088 * k, 0.14), ST)   # 마당 앞 돌계단
    for x in np.linspace(-2.7, 2.7, 6):
        for z in (-1.75, 1.75): cyl(P, (x, 1.0, z), 0.13, 1.8, RED, n=8)
    box(P, (0, 1.9, 0), (2.7, 0.9, 1.65), CREAM)
    for x in np.linspace(-2.25, 2.25, 5):                                       # 꽃살문
        box(P, (x, 1.85, 1.68), (0.4, 0.72, 0.02), C('#B9733A'))
        for y in np.linspace(1.2, 2.5, 6): box(P, (x, y, 1.71), (0.4, 0.015, 0.012), C('#7A3E1E'))
        for xx in np.linspace(x - 0.3, x + 0.3, 4): box(P, (xx, 1.85, 1.71), (0.015, 0.72, 0.012), C('#7A3E1E'))
    box(P, (0, 2.95, 0), (3.0, 0.16, 1.95), GRN)                                 # 단청 공포
    for x in np.linspace(-2.8, 2.8, 15):
        for z in (-2.0, 2.0): box(P, (x, 2.95, z), (0.09, 0.1, 0.03), C(['#E2463A', '#3A6EC2', '#F2C14E'][int((x + 3) * 2) % 3]))
    pagoda_roof(P, (0, 3.08, 0), 5.0, 3.7, 1.55, TILE, lift=0.8)
    box(P, (0, 4.6, 0), (2.0, 0.09, 0.12), C('#3A3E46'))                          # 용마루
    for s in (-1, 1): ell(P, (s * 2.05, 4.72, 0), (0.12, 0.2, 0.08), C('#3A3E46'), sub=1)
    box(P, (0, 2.62, 1.98), (0.75, 0.22, 0.04), C('#2A1E1A'))                     # 현판
    for k in range(3): box(P, (-0.4 + 0.4 * k, 2.62, 2.03), (0.12, 0.13, 0.01), C('#F2C14E'))
    # 삼층 석탑
    tp = np.array([0, 0.7, 4.6])
    box(P, tp + (0, 0.25, 0), (0.75, 0.25, 0.75), ST)
    for k, w in enumerate((0.48, 0.4, 0.33)):
        y0 = 0.5 + k * 0.95
        box(P, tp + (0, y0 + 0.35, 0), (w, 0.35, w), C('#C4BDB1'))
        box(P, tp + (0, y0 + 0.75, 0), (w + 0.28, 0.06, w + 0.28), C('#ABA497'))
    cyl(P, tp + (0, 3.4, 0), 0.05, 0.6, C('#8E8678'), n=8); ell(P, tp + (0, 4.0, 0), 0.08, C('#8E8678'), sub=1)
    # 범종각
    bp = np.array([4.8, 0.7, 3.4])
    for x in (-0.8, 0.8):
        for z in (-0.8, 0.8): cyl(P, bp + (x, 0, z), 0.08, 1.9, RED, n=8)
    pagoda_roof(P, bp + (0, 1.9, 0), 1.6, 1.6, 0.9, TILE, lift=0.8)
    P.add(lathe([(0, 0), (0.42, 0), (0.4, 0.05), (0.33, 0.4), (0.28, 0.75), (0.12, 0.82), (0, 0.84)], 20), np.eye(3), bp + (0, 0.65, 0), C('#5E5A3E'))
    cyl(P, bp + (0, 1.5, 0), 0.03, 0.4, C('#3A3020'), n=8)
    cyl(P, bp + (-0.9, 0.0, 0) + (0, 1.05, 0), 0.06, 0.06, C('#7A5A3A'), n=8)
    # 석등
    for x in (-2.4, 2.4):
        q = np.array([x, 0.7, 3.4])
        cyl(P, q, 0.18, 0.12, ST); cyl(P, q + (0, 0.12, 0), 0.07, 0.7, ST, n=8)
        box(P, q + (0, 0.95, 0), (0.2, 0.17, 0.2), ST); box(P, q + (0, 0.95, 0), (0.1, 0.1, 0.21), C('#FFD98A'), glow=True)
        P.add(PYR4, np.diag([0.32, 0.25, 0.32]), q + (0, 1.12, 0), C('#A8A196'))
    # 연등 줄
    lantern_string(P, (-3.6, 0.7, 6.6), (3.6, 0.7, 6.6), n=11, h=2.9)
    # 일주문 (아래 길가)
    gp = np.array([0, height(TEMPLE[0], TEMPLE[1] + 11.0) - (flat_h(TEMPLE) - 0.02), 11.0])
    for x in (-1.2, 1.2): cyl(P, gp + (x, 0, 0), 0.16, 2.7, RED, n=8)
    box(P, gp + (0, 2.6, 0), (1.5, 0.12, 0.18), GRN)
    pagoda_roof(P, gp + (0, 2.72, 0), 3.4, 1.3, 0.9, TILE, lift=0.9)
    box(P, gp + (0, 2.35, 0.2), (0.6, 0.18, 0.03), C('#2A1E1A'))
    # 경내 마당 모래 + 목탁 치는 자리 방석
    for x, z in ((-1.6, 3.4), (1.6, 3.4), (-2.8, 5.2), (2.8, 5.2), (-4.0, 3.6), (3.4, 6.6)): ell(P, (x, 0.72, z), (0.25, 0.05, 0.25), C('#8E3A5A'), sub=1)
    return dict(door=(0, 0.7, 5.6), name='단풍사 (절)', zone=(0, 0, 3.0), radius=11.0)


# ---------------------------------------------------------------- 교회 (하얀 목조 교회)
def church(P):
    W, ROOF, RED = C('#F5F1E8'), C('#6E3B33'), C('#A8322E')
    box(P, (0, 0.15, 0), (1.5, 0.15, 2.5), C('#B5AA98'))
    box(P, (0, 1.35, 0), (1.35, 1.05, 2.2), W)
    for y in np.arange(0.4, 2.4, 0.18): box(P, (1.36, y, 0), (0.01, 0.012, 2.2), C('#E2DCCF')); box(P, (-1.36, y, 0), (0.01, 0.012, 2.2), C('#E2DCCF'))
    roof_gable(P, (0, 2.4, 0), 2.7, 1.45, 4.4, ROOF, over=0.22)
    for z in (-1.3, 0.0, 1.3):                                                  # 아치 창
        for s in (-1, 1):
            box(P, (s * 1.37, 1.35, z), (0.02, 0.42, 0.22), C('#FFE6A8'), glow=True)
            ell(P, (s * 1.37, 1.77, z), (0.02, 0.22, 0.22), C('#FFE6A8'), sub=1, glow=True)
    # 종탑
    box(P, (0, 1.9, 2.55), (0.65, 1.6, 0.55), W)
    box(P, (0, 0.72, 3.12), (0.36, 0.55, 0.04), RED)                              # 빨간 문
    ell(P, (0, 1.27, 3.12), (0.36, 0.25, 0.04), RED, sub=1)
    P.add(torus(1.0, 0.25, 24, 8), Rx(math.pi / 2) @ np.diag([0.22, 0.22, 0.22]), (0, 1.75, 3.15), C('#2E6B3A'))   # 리스
    for s in (-1, 1): ell(P, (s * 0.05, 1.54, 3.2), (0.06, 0.04, 0.02), C('#D93030'), sub=1)
    box(P, (0, 3.75, 2.55), (0.55, 0.45, 0.45), W)
    box(P, (0, 3.75, 2.55), (0.3, 0.3, 0.47), C('#3A3030'))                        # 종 창
    P.add(lathe([(0, 0), (0.17, 0), (0.15, 0.05), (0.11, 0.2), (0.05, 0.28), (0, 0.29)], 16), np.eye(3), (0, 3.55, 2.55), C('#D9B34A'))
    P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.75, 1.9, 0.75]), (0, 4.2, 2.55), ROOF)
    box(P, (0, 6.45, 2.55), (0.04, 0.32, 0.04), C('#F2E6C0')); box(P, (0, 6.55, 2.55), (0.18, 0.04, 0.04), C('#F2E6C0'))
    # 크리스마스트리
    tp = np.array([2.6, 0, 3.6])
    cyl(P, tp, 0.12, 0.4, C('#6A4A30'), n=8)
    for k in range(4): cone(P, tp + (0, 0.35 + 0.55 * k, 0), 0.95 - 0.2 * k, 0.9, C(['#2E6B3A', '#357A42', '#3E874A', '#48934F'][k]))
    for k in range(26):
        y = 0.5 + rng.random() * 2.0; r = (1.0 - (y - 0.35) / 2.6) * 0.85; a = rng.random() * 6.28
        ell(P, tp + (math.cos(a) * r, y, math.sin(a) * r), 0.06, C(['#FF4A4A', '#FFD54A', '#6AC8FF', '#FFFFFF'][k % 4]), sub=1, glow=True)
    for k in range(5):
        a = math.pi / 2 + 2 * math.pi * k / 5
        ell(P, tp + (math.cos(a) * 0.12, 2.85 + math.sin(a) * 0.12, 0), (0.1, 0.035, 0.03), C('#FFE14D'), sub=1, glow=True, R=Rz(a))
    for k in range(4): box(P, tp + (-0.5 + 0.35 * k, 0.12, 0.7 - 0.2 * (k % 2)), (0.13, 0.12, 0.13), C(['#D93030', '#3A7AD0', '#F2C14E', '#7FBF5A'][k]))
    # 울타리, 벤치
    for z0 in (-2.8, 2.8):
        pass
    fence(P, (-2.2, 0, 4.6), (-0.8, 0, 4.6), '#FFFFFF'); fence(P, (0.8, 0, 4.6), (2.0, 0, 4.6), '#FFFFFF')
    bench(P, (-2.2, 0, 1.0), ry=math.pi / 2)
    return dict(door=(0, 0, 3.9), name='은행나무 교회', zone=(0, 0, 0.8), radius=8.5)


# ---------------------------------------------------------------- 성당 (고딕 석조)
def cathedral(P):
    S, SD, SL = C('#D8CFC0'), C('#BFB5A4'), C('#58637A')
    box(P, (0, 0.18, 0), (2.4, 0.18, 4.4), SD)
    box(P, (0, 1.9, -0.4), (1.9, 1.6, 3.6), S)                                    # 신랑
    roof_gable(P, (0, 3.5, -0.4), 3.8, 1.9, 7.2, SL, over=0.15)
    for z in np.linspace(-3.4, 2.2, 5):                                           # 버트레스 + 뾰족 창
        for s in (-1, 1):
            box(P, (s * 2.05, 1.5, z - 0.35), (0.16, 1.35, 0.14), SD)
            col = C(['#3E6FD0', '#C8384A', '#E0B23A', '#4AA06A', '#8A4AC2'][int(z * 7) % 5])
            box(P, (s * 1.92, 2.0, z + 0.25), (0.02, 0.75, 0.2), col, glow=True)
            P.add(PYR4, Ry(math.pi / 4) @ Rz(s * math.pi / 2 * 0) @ np.diag([0.2, 0.32, 0.03]), (s * 1.92, 2.75, z + 0.25), col, glow=True)
    # 쌍탑
    for s in (-1, 1):
        box(P, (s * 1.45, 2.9, 3.45), (0.75, 2.6, 0.75), S)
        for y in (1.6, 3.2, 4.6): box(P, (s * 1.45, y, 4.21), (0.16, 0.42, 0.02), C('#6A7FB8'), glow=True)
        box(P, (s * 1.45, 5.55, 3.45), (0.82, 0.08, 0.82), SD)
        for x in (-0.65, 0.65):
            for z in (-0.65, 0.65): P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.12, 0.5, 0.12]), (s * 1.45 + x, 5.6, 3.45 + z), SD)
        P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.85, 2.7, 0.85]), (s * 1.45, 5.6, 3.45), SL)
        box(P, (s * 1.45, 8.45, 3.45), (0.03, 0.22, 0.03), C('#E8C86A')); box(P, (s * 1.45, 8.52, 3.45), (0.12, 0.03, 0.03), C('#E8C86A'))
    box(P, (0, 2.6, 3.45), (0.75, 2.3, 0.7), S)                                    # 정면 가운데
    # 장미창
    rc = np.array([0, 3.55, 4.17])
    ell(P, rc, (0.62, 0.62, 0.03), C('#2A3050'), sub=2)
    for k in range(12):
        a = 2 * math.pi * k / 12
        ell(P, rc + (math.cos(a) * 0.38, math.sin(a) * 0.38, 0.02), (0.15, 0.15, 0.02), C(['#3E6FD0', '#C8384A', '#E0B23A', '#4AA06A'][k % 4]), sub=1, glow=True)
    ell(P, rc + (0, 0, 0.03), (0.17, 0.17, 0.02), C('#F2D26A'), sub=1, glow=True)
    # 정문 (뾰족 아치)
    box(P, (0, 1.05, 4.17), (0.48, 0.75, 0.03), C('#4A3428'))
    P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.68, 0.55, 0.04]), (0, 1.8, 4.17), C('#4A3428'))
    for k in range(5): box(P, (0, 0.06 + 0.06 * k, 4.6 + 0.35 * (4 - k) * 0.4), (0.9 + 0.1 * (4 - k), 0.06 + 0.06 * k, 0.18), SD)
    # 성모상과 촛대 정원
    mp = np.array([2.9, 0.0, 5.2])
    box(P, mp + (0, 0.25, 0), (0.3, 0.25, 0.3), SD)
    cone(P, mp + (0, 0.5, 0), 0.22, 0.85, C('#F4F0E8'))
    P.add(CONE, np.diag([0.25, 0.75, 0.25]), mp + (0, 0.52, -0.02), C('#6E8FD0'))
    ell(P, mp + (0, 1.42, 0), 0.11, C('#F4F0E8'), sub=1)
    ell(P, mp + (0, 1.45, -0.02), (0.13, 0.14, 0.12), C('#6E8FD0'), sub=1)
    P.add(torus(1.0, 0.1, 20, 6), Rx(0.2) @ np.diag([0.16, 0.16, 0.16]), mp + (0, 1.62, -0.05), C('#FFE07A'), glow=True)
    for k in range(7):
        q = mp + (-0.6 + 0.2 * k, 0, 0.6)
        cyl(P, q, 0.03, 0.25 + 0.05 * (k % 3), C('#FFF6E0'), n=8)
        ell(P, q + (0, 0.3 + 0.05 * (k % 3), 0), (0.025, 0.05, 0.025), C('#FFB43A'), sub=1, glow=True)
    for x in (-2.8, 2.8): lamp(P, (x, 0, 6.6))
    return dict(door=(0, 0, 5.6), name='별빛 성당', zone=(0, 0, 0.5), radius=10.0)


# ---------------------------------------------------------------- 광장
def plaza(P):
    maple(P, (0, 0, 0), 1.6)                                                    # 마을 한가운데 큰 단풍나무
    cyl(P, (0, 0, 0), 1.4, 0.32, C('#BFB3A0'))
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        if k % 2 == 0: bench(P, (math.cos(a) * 3.2, 0, math.sin(a) * 3.2), ry=-a - math.pi / 2)
        else: lamp(P, (math.cos(a) * 3.7, 0, math.sin(a) * 3.7))
    # 이정표
    cyl(P, (1.8, 0, 3.6), 0.05, 1.7, C('#6E4A30'), n=8)
    for k, (yy, ang, col) in enumerate(((1.55, 1.6, '#E8DCC0'), (1.3, -1.5, '#E8DCC0'), (1.05, 3.1, '#E8DCC0'))):
        box(P, np.array([1.8, yy, 3.6]) + Ry(ang) @ np.array([0.3, 0, 0]), (0.32, 0.08, 0.03), C(col), ry=ang)
    return dict(door=(0, 0, 4.0), name='단풍 광장')


# ---------------------------------------------------------------- 배치
COTTAGES = [  # (x, z, ry, wall, roof, 주인)
    (-6.5, 4.5, 0.6, '#F3E3C3', '#B5462E', 'hamster'), (-9.5, -2.5, 1.35, '#F7D9C4', '#8E5A3A', 'rabbit'),
    (6.8, 5.0, -0.6, '#EFE6D2', '#C06A2E', 'cat'), (9.5, -2.8, -1.4, '#F2DFC0', '#9A3E30', 'dog'),
    (-4.2, 9.5, 0.25, '#E8D8BE', '#6E4A3A', 'bear'), (4.6, 10.2, -0.3, '#F5E6D0', '#B04A3A', 'fox'),
    (-12.8, 8.5, 0.9, '#EDE0C8', '#7A5A3A', 'raccoon'), (12.5, 10.0, -0.9, '#F7E8D2', '#C27A3A', 'squirrel'),
    (0.2, 16.5, 0.0, '#F0E2CA', '#8A3A30', 'deer'), (-6.0, -8.0, 0.4, '#F4E4CC', '#A04A2E', 'panda'),
    (6.5, -8.5, -0.4, '#EFDCC2', '#B85A30', 'lion')]


def scatter(P):
    # 단풍길: 길 양옆 가로수
    for z in np.arange(-11.5, -3.0, 2.2):
        for s in (-1, 1): maple(P, (s * 2.2, height(s * 2.2, z), z), 0.85 + 0.15 * rng.random())
    for x in np.arange(-14.5, -5.0, 2.6):
        ginkgo(P, (x, 0, -1.2 + 0.03 * x), 0.8); ginkgo(P, (x + 1.2, 0, 3.6), 0.75)
    for x in np.arange(6.0, 15.5, 2.6):
        maple(P, (x, 0, 0.7), 0.8, ['#F29A38', '#F2C230', '#E8552E']); maple(P, (x + 1.1, 0, 5.6), 0.75)
    # 절 주변 단풍 숲
    for k in range(26):
        a = rng.random() * 2 * math.pi; r = 9 + rng.random() * 6
        x, z = TEMPLE[0] + math.cos(a) * r * 1.2, TEMPLE[1] + math.sin(a) * r * 0.8
        if z > -13.5 and abs(x) < 3: continue
        maple(P, (x, height(x, z), z), 0.8 + 0.5 * rng.random())
    # 바깥 숲
    placed = 0
    while placed < 120:
        a = rng.random() * 2 * math.pi; r = 22 + rng.random() * 15
        x, z = math.cos(a) * r, math.sin(a) * r
        if math.hypot(x - TEMPLE[0], z - TEMPLE[1]) < 10 or math.hypot(x - CATHEDRAL[0], z - CATHEDRAL[1]) < 8 or math.hypot(x - CHURCH[0], z - CHURCH[1]) < 7: continue
        y = height(x, z); k = rng.random()
        (pine if k < 0.28 else ginkgo if k < 0.45 else maple)(P, (x, y, z), 0.9 + 0.6 * rng.random())
        placed += 1
    # 연못가
    for k in range(5):
        a = 0.6 + k * 1.15; maple(P, (POND[0] + math.cos(a) * 4.2, 0, POND[1] + math.sin(a) * 4.2), 0.85)
    bench(P, (POND[0] + 3.4, 0, POND[1] - 0.5), ry=-math.pi / 2)
    # 가을 소품
    for x, z in ((-2.5, 13.5), (2.6, 13.0), (-1.2, 14.2), (3.5, 14.6), (-7.5, 6.2), (8.2, 6.8), (-11.0, -1.0)):
        pumpkin(P, (x, 0, z), 0.9 + 0.4 * rng.random())
    for x, z, ry in ((-3.5, 15.0, 0.3), (4.5, 15.8, -0.6), (8.0, 13.5, 1.1)): hay(P, (x, 0, z), ry)
    for k in range(40):
        x, z = (rng.random() - 0.5) * 46, (rng.random() - 0.5) * 46
        if min(seg_dist(np.array([x]), np.array([z]), p, q)[0] for p, q in PATHS) < 1.3 or math.hypot(x, z) < 5: continue
        if any(math.hypot(x - c[0], z - c[1]) < 4 for c in (TEMPLE, CHURCH, CATHEDRAL, POND)): continue
        bush(P, (x, height(x, z), z), 0.7 + 0.4 * rng.random(), ['#8A9A4A', '#B0763A', '#9A5A3A', '#7A8A44'][k % 4])
        if k % 3 == 0:
            for j in range(4): flower(P, (x + 0.6 + 0.15 * j, height(x, z), z + 0.3), ['#F2A33A', '#E85A8A', '#F2D24A', '#C2483A'][j])
    for z in np.arange(-13.2, -0.5, 3.0):
        for s in (-1, 1): lamp(P, (s * 1.25, height(s * 1.25, z), z))


BUILD = {
    'temple': (temple, TEMPLE, 0.0), 'church': (church, CHURCH, math.pi / 2), 'cathedral': (cathedral, CATHEDRAL, -math.pi / 2),
    'plaza': (plaza, (0, 0), 0.0),
}


def build_all():
    groups, layout = [], {'buildings': {}, 'homes': {}, 'zones': {}, 'spawn': {}}
    T = mh.Part(); terrain(T); groups.append(('terrain', T, (0, 0, 0), 0.0))
    S = mh.Part(); scatter(S); groups.append(('nature', S, (0, 0, 0), 0.0))
    for name, (fn, (x, z), ry) in BUILD.items():
        P = mh.Part(); info = fn(P); y = flat_h((x, z)) - 0.02 if (x, z) == TEMPLE else 0.0
        groups.append((name, P, (x, y, z), ry))
        door = np.array([x, y, z]) + Ry(ry) @ np.array(info['door'])
        layout['buildings'][name] = dict(name=info['name'], position=[round(float(v), 3) for v in (x, y, z)], rotationY=round(ry, 4), door=[round(float(v), 3) for v in door])
        if 'zone' in info:
            zc = np.array([x, y, z]) + Ry(ry) @ np.array(info['zone'])
            layout['zones'][name] = dict(center=[round(float(v), 3) for v in zc], radius=info['radius'], name=info['name'])
    for k, (x, z, ry, wall, roof, who) in enumerate(COTTAGES):
        P = mh.Part(); info = cottage(P, wall, roof, chimney=k % 3 != 2); y = height(x, z) - 0.03
        groups.append((f'house_{who}', P, (x, y, z), ry))
        door = np.array([x, y, z]) + Ry(ry) @ np.array(info['door'])
        layout['homes'][who] = [round(float(v), 3) for v in door]
    layout['spawn']['plaza'] = [0.0, 0.0, 4.6]
    for n in ('temple', 'church', 'cathedral'): layout['spawn'][n] = layout['buildings'][n]['door']
    # 걸을 수 있는 높이 정보 (격자)
    n = 81; xs = np.linspace(-R_WORLD, R_WORLD, n)
    layout['heightmap'] = dict(size=R_WORLD * 2, n=n, h=[round(height(x, z), 3) for z in xs for x in xs])
    # 막힌 곳 (건물 사각형: 중심, 반폭, 회전)
    blk = [dict(c=[TEMPLE[0], TEMPLE[1]], h=[3.75, 2.75], r=0.0), dict(c=[TEMPLE[0], TEMPLE[1] + 4.6], h=[0.8, 0.8], r=0.0), dict(c=[TEMPLE[0] - 1.2, TEMPLE[1] + 11.0], h=[0.25, 0.25], r=0.0), dict(c=[TEMPLE[0] + 1.2, TEMPLE[1] + 11.0], h=[0.25, 0.25], r=0.0), dict(c=[TEMPLE[0] + 4.8, TEMPLE[1] + 3.4], h=[0.9, 0.9], r=0.0),
           dict(c=[CHURCH[0], CHURCH[1]], h=[1.6, 3.2], r=math.pi / 2), dict(c=[CATHEDRAL[0] - 0.4, CATHEDRAL[1]], h=[2.4, 4.4], r=-math.pi / 2),
           dict(c=[0, 0], h=[1.45, 1.45], r=0.0), dict(c=[POND[0], POND[1]], h=[2.6, 2.6], r=0.0)]
    for x, z, ry, *_ in COTTAGES: blk.append(dict(c=[x, z], h=[1.9, 1.7], r=ry))
    ty = flat_h(TEMPLE) - 0.02
    layout['platforms'] = [dict(c=[TEMPLE[0] + 0.6, TEMPLE[1] + 2.4], h=[6.2, 5.0], r=0.0, y0=ty + 0.7, y1=ty + 0.7),
                           dict(c=[TEMPLE[0], TEMPLE[1] + 7.9], h=[1.6, 0.5], r=0.0, y0=ty, y1=ty + 0.7),
                           dict(c=[CHURCH[0], CHURCH[1]], h=[1.5, 2.5], r=math.pi / 2, y0=0.3, y1=0.3),
                           dict(c=[CATHEDRAL[0], CATHEDRAL[1]], h=[2.4, 4.4], r=-math.pi / 2, y0=0.36, y1=0.36)]
    layout['blockers'] = [{k: ([round(float(t), 3) for t in v] if isinstance(v, list) else round(float(v), 4)) for k, v in b.items()} for b in blk]
    return groups, layout


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    groups, layout = build_all()
    data, tris = v1.glb_bytes(groups); open(os.path.join(out, 'village.glb'), 'wb').write(data)
    with open(os.path.join(out, 'village_layout.js'), 'w') as f:
        f.write('// 단풍마을 배치: 건물, 주민 집, 음악 구역, 스폰, 높이맵, 막힌 곳 (미터)\n')
        f.write('export default ' + json.dumps(layout, ensure_ascii=False) + ';\n')
    print('village tris', tris, 'bytes', len(data))
    if 'check' in sys.argv:
        v1.render_parts(groups, os.path.join(out, '_view.png'), 0.5, 0.55, (0, 0, -4.0), 0.017, size=1200)
        v1.render_parts(groups, os.path.join(out, '_temple.png'), 0.35, 0.32, (0, 2.0, -21.0), 0.06, size=900)
        v1.render_parts(groups, os.path.join(out, '_church.png'), 2.2, 0.3, (-18.0, 2.0, 2.5), 0.075, size=900)
        v1.render_parts(groups, os.path.join(out, '_cathedral.png'), -2.0, 0.3, (19.0, 3.0, 3.0), 0.055, size=900)
        print('renders saved')
