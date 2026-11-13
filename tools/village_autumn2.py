"""단풍마을 v2 — 큰 실내가 있는 절(기요미즈데라풍)·교회·성당(노트르담풍), 걸을 수 있는 바닥/벽 정보 포함.
사용법: python3 village_autumn2.py <출력폴더> [check]
"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hamster as mh
from make_hamster import C, Rx, Ry, Rz, torus, lathe, CONE
import village as v1
from village import box, cyl, cone, ell, roof_gable, CYL, CYL8, PYR4, PRISM, bench, lamp, fence, flower, rock
import village_autumn as va
from village_autumn import maple, ginkgo, pine, bush, pumpkin, hay, lantern_string, cottage, lotus, plaza, MAPLES, GINKGO

R_WORLD = 52.0; BOUND = 41.0
TEMPLE = (0.0, -31.0); CHURCH = (-27.0, 2.0); CATHEDRAL = (26.0, 2.0); POND = (-7.5, 12.5)
ROT = {'temple': 0.0, 'church': math.pi / 2, 'cathedral': -math.pi / 2}
rng = np.random.default_rng(11)


def to_world(name, x, z):
    c = {'temple': TEMPLE, 'church': CHURCH, 'cathedral': CATHEDRAL}[name]; r = ROT[name]
    v = Ry(r) @ np.array([x, 0.0, z]); return c[0] + v[0], c[1] + v[2]


def to_local(name, wx, wz):
    c = {'temple': TEMPLE, 'church': CHURCH, 'cathedral': CATHEDRAL}[name]; r = ROT[name]
    v = Ry(-r) @ np.array([wx - c[0], 0.0, wz - c[1]]); return v[0], v[2]


# ---------------------------------------------------------------- 지형
PATHS = [((0, 4), (0, -14.5)), ((0, 0), (-16.0, 2.0)), ((0, 0), (17.5, 2.0)),
         ((0, 0), (0, 14)), ((0, 6), (-6, 9.5)), ((-3, 0.5), (-4, 6)), ((3, 0.5), (5, 7))]


def height(x, z):
    h = 0.16 * math.sin(x * 0.31) * math.cos(z * 0.27)
    r = math.hypot(x, z); h += 4.0 * max(0.0, min(1.0, (r - 42.0) / 8.0)) ** 2
    h -= 0.5 * math.exp(-((x - POND[0]) ** 2 + (z - POND[1]) ** 2) / 7.0)
    lx, lz = to_local('temple', x, z)
    # 절 뒤로 솟은 산과, 무대 아래 단풍 골짜기
    if lz < -15: h += 4.5 * smooth((-15 - lz) / 12) * (1 - smooth((abs(lx) - 16) / 10))
    h -= 3.0 * math.exp(-(((lx - 11.0) / 5.5) ** 2 + ((lz + 1.0) / 6.0) ** 2))
    for nm, rect in FLATS.items():
        cx, cz, hx, hz, y = rect; ax, az = to_local(nm[0], x, z) if nm[0] != 'plaza' else (x, z)
        dx, dz = max(0, abs(ax - cx) - hx), max(0, abs(az - cz) - hz); d = math.hypot(dx, dz)
        if d < 3.5: k = smooth(d / 3.5); h = y * (1 - k) + h * k
    return h


def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


FLATS = {('temple', 'yard'): (0, 9, 9.5, 8.5, 0.0), ('church', 'yard'): (0, 0, 6.5, 12.0, 0.0), ('cathedral', 'yard'): (0, -3, 9.5, 14.0, 0.0), ('plaza',): (0, 0, 5, 5, 0.0)}


def terrain(P, R=R_WORLD, n=200):
    xs = np.linspace(-R, R, n); X, Z = np.meshgrid(xs, xs)
    Hh = np.vectorize(height)(X, Z); V = np.stack([X, Hh, Z], -1).reshape(-1, 3)
    i, j = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (i * n + j).reshape(-1)
    I = np.concatenate([np.stack([a, a + n, a + 1], 1), np.stack([a + 1, a + n, a + n + 1], 1)])
    nz = rng.random(len(V)); g = [C('#A3B865'), C('#98B05E'), C('#AFBD6C'), C('#B8B266')]
    col = np.stack([g[k] for k in (nz * 4).astype(int).clip(0, 3)])
    d = np.min([va.seg_dist(V[:, 0], V[:, 2], p, q) for p, q in PATHS], axis=0)
    onp = d < 0.95; tile = ((np.floor(V[:, 0] * 1.8) + np.floor(V[:, 2] * 1.8)) % 2 == 0)
    col[onp] = np.where(tile[onp, None], C('#D8C7A2'), C('#CDBB93')); col[(d >= 0.95) & (d < 1.1)] = C('#A89474')
    rr = np.hypot(V[:, 0], V[:, 2]); pl = rr < 4.4
    col[pl] = np.where((np.floor(rr * 1.6) % 2 == 0)[pl, None], C('#E2D6BE'), C('#D5C8AE'))
    leaf = (rng.random(len(V)) < 0.07) & ~onp & ~pl
    col[leaf] = col[leaf] * 0.55 + np.stack([C(MAPLES[k % 5]) for k in rng.integers(0, 5, leaf.sum())]) * 0.45
    col[V[:, 1] > 2.2] = C('#8E9A58'); col[V[:, 1] < -1.2] = C('#B0763A') * 0.6 + C('#8E9A58') * 0.4
    col[np.hypot(V[:, 0] - POND[0], V[:, 2] - POND[1]) < 2.9] = C('#7E8F5A')
    fn = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]); flip = fn[:, 1] < 0; I[flip] = I[flip][:, ::-1]
    fn = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]); Nv = np.zeros_like(V)
    for k in range(3): np.add.at(Nv, I[:, k], fn)
    Nv /= np.linalg.norm(Nv, axis=1, keepdims=True); P.g['toon'].append((V, Nv, col, I))
    cyl(P, (POND[0], -0.32, POND[1]), 2.7, 0.06, C('#7FB8D0', 0.85), glow=True)
    for k in range(6):
        a = k * 1.1; p = (POND[0] + math.cos(a) * 1.6, -0.24, POND[1] + math.sin(a) * 1.3)
        cyl(P, p, 0.28, 0.02, C('#5E9A4A'))
        if k % 2 == 0: lotus(P, (p[0] + 0.1, -0.22, p[2]))
    for k in range(14):
        a = 2 * math.pi * k / 14; rock(P, (POND[0] + math.cos(a) * 2.85, -0.15, POND[1] + math.sin(a) * 2.85), 0.8 + 0.3 * (k % 3))


# ---------------------------------------------------------------- 건물 도우미 (벽 = 보이는 상자 + 막힌 곳)
class Bld:
    def __init__(s):
        s.body, s.roof = mh.Part(), mh.Part(); s.blk, s.plat, s.spots, s.inside = [], [], {}, []
    def wall(s, x0, z0, x1, z1, h, col, t=0.25, y0=0.0, block=True, P=None):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; hx, hz = max(abs(x1 - x0) / 2, t / 2), max(abs(z1 - z0) / 2, t / 2)
        box(P or s.body, (cx, y0 + h / 2, cz), (hx, h / 2, hz), col)
        if block: s.blk.append((cx, cz, hx, hz))
    def solid(s, cx, cz, hx, hz): s.blk.append((cx, cz, hx, hz))
    def floor(s, cx, cz, hx, hz, y0, y1=None): s.plat.append((cx, cz, hx, hz, y0, y0 if y1 is None else y1))
    def spot(s, kind, x, z, face=None, y=None): s.spots.setdefault(kind, []).append((x, z, face))


def door_leaf(P, hinge, w, h, ang, col, side=1):
    c = np.array(hinge) + Ry(ang) @ np.array([side * w / 2, h / 2, 0])
    box(P, c, (w / 2, h / 2, 0.04), C(col), ry=ang)


# ---------------------------------------------------------------- 절 (기요미즈데라풍)
VERM, VERM_D, WHITE, CYP, GOLD = C('#C8402E'), C('#9E2C22'), C('#F4EEE2'), C('#6E5A4C'), C('#E8B84A')
STONE, STONE_D, WOOD, WOOD_D = C('#C6BEAF'), C('#AFA696'), C('#A8764A'), C('#7A5232')


def curved_roof(P, c, w, d, h, col, eave=0.6, layers=1):
    """처마가 들린 우진각 지붕"""
    prof = [(1.0, 0.0), (0.96, 0.04), (0.86, 0.14), (0.66, 0.36), (0.42, 0.64), (0.22, 0.86), (0.08, 0.97), (0, 1.0)]
    V, F = lathe(prof, 4); V = V.copy()
    rr = np.sqrt(V[:, 0] ** 2 + V[:, 2] ** 2); V[:, 1] += eave * 0.18 * (rr > 0.95)
    P.add((V, F), Ry(math.pi / 4) @ np.diag([w * 0.7071, h, d * 0.7071]), c, col)
    box(P, (c[0], c[1] + h * 0.98, c[2]), (w * 0.28, 0.12, 0.14), C('#4A3E36'))


def pagoda3(P, base):
    b = np.array(base, float)
    box(P, b + (0, 0.25, 0), (1.8, 0.25, 1.8), STONE)
    y = 0.5
    for k, (w, hh) in enumerate(((1.3, 1.6), (1.1, 1.35), (0.95, 1.2))):
        box(P, b + (0, y + hh / 2, 0), (w, hh / 2, w), VERM)
        for s in (-1, 1): box(P, b + (s * w * 0.55, y + hh * 0.5, w + 0.01), (w * 0.25, hh * 0.35, 0.02), WHITE); box(P, b + (w + 0.01, y + hh * 0.5, s * w * 0.55), (0.02, hh * 0.35, w * 0.25), WHITE)
        box(P, b + (0, y + hh + 0.1, 0), (w + 0.15, 0.1, w + 0.15), C('#E7C35A'))
        curved_roof(P, b + (0, y + hh + 0.18, 0), (w + 1.1) * 2, (w + 1.1) * 2, 0.75, CYP, eave=1.2)
        y += hh + 0.75
    cyl(P, b + (0, y, 0), 0.07, 2.4, C('#B89A3A'), n=8)
    for k in range(7): cyl(P, b + (0, y + 0.4 + 0.25 * k, 0), 0.18 - 0.012 * k, 0.05, C('#C9A84A'), n=8)
    ell(P, b + (0, y + 2.5, 0), 0.12, GOLD, sub=1)


def buddha(P, base, s=1.0):
    b = np.array(base, float)
    for k in range(10):                                             # 연꽃 대좌
        a = 2 * math.pi * k / 10
        ell(P, b + (math.cos(a) * 0.95 * s, 0.35 * s, math.sin(a) * 0.95 * s), (0.42 * s, 0.32 * s, 0.22 * s), C('#E39AB0'), sub=1, R=Ry(-a))
    cyl(P, b, 1.0 * s, 0.45 * s, C('#C9A13A'))
    g = C('#E2B348'); gd = C('#C8962E')
    ell(P, b + (0, 0.75 * s, 0), (0.95 * s, 0.32 * s, 0.7 * s), gd, sub=2)             # 결가부좌 다리
    ell(P, b + (0, 1.35 * s, -0.05 * s), (0.62 * s, 0.75 * s, 0.45 * s), g, sub=2)      # 몸
    for x in (-1, 1): ell(P, b + (x * 0.55 * s, 1.35 * s, 0.05 * s), (0.2 * s, 0.55 * s, 0.22 * s), gd, sub=1, R=Rz(x * 0.25))
    ell(P, b + (0, 0.98 * s, 0.38 * s), (0.36 * s, 0.14 * s, 0.18 * s), g, sub=1)       # 모은 손
    ell(P, b + (0, 2.35 * s, 0), (0.42 * s, 0.46 * s, 0.4 * s), g, sub=2)                # 머리
    for k in range(18): a = 2 * math.pi * k / 18; ell(P, b + (math.cos(a) * 0.3 * s, 2.62 * s, math.sin(a) * 0.3 * s - 0.03), 0.09 * s, gd, sub=0)
    ell(P, b + (0, 2.85 * s, -0.02), (0.18 * s, 0.16 * s, 0.18 * s), gd, sub=1)
    for x in (-1, 1): ell(P, b + (x * 0.42 * s, 2.3 * s, 0), (0.07 * s, 0.22 * s, 0.08 * s), gd, sub=1)
    ell(P, b + (0, 2.4 * s, 0.39 * s), (0.05 * s, 0.05 * s, 0.02 * s), C('#FFF2C0'), sub=0, glow=True)
    P.add(torus(1.0, 0.04, 40, 6), np.diag([1.2 * s, 1.2 * s, 1.2 * s]), b + (0, 2.4 * s, -0.5 * s), C('#F2CF6A'), glow=True)   # 광배
    ell(P, b + (0, 2.4 * s, -0.55 * s), (1.15 * s, 1.15 * s, 0.03 * s), C('#E8B84A', 0.6), sub=2)


def temple():
    B = Bld(); P, Rf = B.body, B.roof
    # 아래 돌계단과 인왕문 (z +16 → +11)
    for k in range(8): box(P, (0, 0.075 + 0.15 * k, 16.4 - 0.5 * k), (2.2, 0.075 + 0.075 * k, 0.26), STONE)
    B.floor(0, 14.65, 2.2, 1.95, 0.0, 1.2)
    B.solid(-2.45, 14.65, 0.25, 2.0); B.solid(2.45, 14.65, 0.25, 2.0)
    g = np.array([0, 1.2, 11.6])
    box(P, g + (0, -0.6, 0), (11.0, 0.6, 9.4 - 0.4), STONE) if False else None
    # 넓은 돌마당 (y 1.2): z +12.6 .. -1.0, x -10 .. +3
    box(P, (-3.5, 0.6, 5.8), (6.5, 0.6, 6.8), STONE)
    B.floor(-3.5, 5.8, 6.5, 6.8, 1.2)
    for x in np.arange(-9.5, 3.0, 1.0): box(P, (x, 1.205, 5.8), (0.01, 0.003, 6.8), STONE_D)
    # 마당 가장자리 난간(막힘), 계단 자리만 열림
    for (x0, z0, x1, z1) in ((-10, 12.6, -2.3, 12.6), (2.3, 12.6, 3.0, 12.6), (-10, -1.0, -10, 12.6), (3.0, 1.0, 3.0, 12.6)):
        B.wall(x0, z0, x1, z1, 0.45, VERM, t=0.12, y0=1.2)
    # 인왕문 (2층 주홍 문)
    for x in (-2.2, -0.9, 0.9, 2.2):
        for z in (-0.9, 0.9): cyl(P, g + (x, 0, z), 0.18, 3.4, VERM, n=8)
    for x in (-1.55, 1.55):
        box(P, g + (x * 1.0, 1.7, 0), (0.6, 1.7, 0.35), WHITE); B.solid(x * 1.0, 11.6, 0.65, 0.45)
    box(P, g + (0, 3.4, 0), (2.6, 0.18, 1.2), VERM_D)
    box(P, g + (0, 4.0, 0), (2.0, 0.55, 0.85), VERM)
    curved_roof(P, g + (0, 3.55, 0), 7.4, 4.2, 1.1, CYP, eave=1.0)
    curved_roof(P, g + (0, 4.55, 0), 5.8, 3.4, 1.5, CYP, eave=1.2)
    box(P, g + (0, 2.9, 0.95), (0.8, 0.3, 0.05), C('#2A1E1A'))
    # 삼층탑
    pagoda3(P, (-7.5, 1.2, 7.0)); B.solid(-7.5, 7.0, 1.85, 1.85)
    # 향로 (향 피우기)
    q = np.array([-2.0, 1.2, 3.6])
    cyl(P, q, 0.55, 0.15, C('#5A5440')); P.add(lathe([(0, 0), (0.62, 0), (0.7, 0.35), (0.6, 0.7), (0.66, 0.78), (0, 0.78)], 20), np.eye(3), q + (0, 0.15, 0), C('#6E6246'))
    for x in (-0.4, 0.4): cyl(P, q + (x, 0.95, 0), 0.05, 0.5, C('#6E6246'), n=8)
    curved_roof(P, q + (0, 1.45, 0), 1.5, 1.5, 0.6, C('#6E6246'), eave=0.6)
    B.solid(-2.0, 3.6, 0.75, 0.75); B.spot('incense', -2.0, 4.7, (-2.0, 3.6))
    # 시주함 (나무 함, 돈 넣는 구멍)
    dq = np.array([1.5, 1.2, 2.2])
    box(P, dq + (0, 0.42, 0), (0.42, 0.42, 0.32), C('#7A3A22')); box(P, dq + (0, 0.86, 0), (0.46, 0.03, 0.36), C('#5A2414'))
    box(P, dq + (0, 0.89, 0), (0.2, 0.004, 0.03), C('#1A0E08')); box(P, dq + (0, 0.5, 0.325), (0.26, 0.16, 0.005), C('#E8C86A'))
    for k, ch in enumerate((0.1, -0.1)): box(P, dq + (0, 0.5 + ch, 0.33), (0.18, 0.012, 0.004), C('#7A3A22'))
    B.solid(1.5, 2.2, 0.48, 0.38); B.spot('donate', 1.5, 3.05, (1.5, 2.2))
    # 나무 계단 (마당 1.2 → 본당 2.4), z -1.0 .. +1.6
    for k in range(6): box(P, (-3.5, 1.3 + 0.2 * k, 1.4 - 0.4 * k), (2.0, 0.1, 0.22), WOOD)
    B.floor(-3.5, 0.3, 2.0, 1.3, 1.2, 2.4)
    B.solid(-5.65, 0.3, 0.15, 1.3); B.solid(-1.35, 0.3, 0.15, 1.3)
    # 본당 바닥 + 무대 (y 2.4): 본당 x -10..3, z -14..-1 / 무대 x 3..13, z -9..1
    box(P, (-3.5, 1.15, -7.5), (6.6, 1.15, 6.6), STONE)
    box(P, (-3.5, 2.3, -7.5), (6.5, 0.1, 6.5), WOOD_D); B.floor(-3.5, -7.5, 6.5, 6.5, 2.4)
    for (x0, x1) in ((-10, -5.6), (-1.4, 3.0)): B.wall(x0, -1.0, x1, -1.0, 0.5, VERM, t=0.1, y0=2.4)
    B.wall(3.0, -1.0, 3.0, 1.0, 0.55, VERM, t=0.1, y0=2.4)
    box(P, (8.0, 2.3, -4.0), (5.0, 0.1, 5.0), WOOD); B.floor(8.0, -4.0, 5.0, 5.0, 2.4)
    for x in np.arange(3.2, 13.0, 0.7): box(P, (x, 2.405, -4.0), (0.012, 0.004, 5.0), WOOD_D)
    for x in np.arange(3.6, 13.1, 1.6):                               # 무대 받치는 기둥 격자
        for z in np.arange(-8.6, 1.2, 1.6):
            lx, lz = x, z; wx, wz = to_world('temple', lx, lz); y0 = height(wx, wz) - 0.3
            cyl(P, (lx, y0, lz), 0.13, 2.3 - y0, WOOD_D, n=8)
        for yy in (0.6, 1.5):
            box(P, (x, yy, -4.0), (0.06, 0.06, 5.0), WOOD_D)
    for z in np.arange(-8.6, 1.2, 1.6):
        for yy in (0.6, 1.5): box(P, (8.0, yy, z), (5.0, 0.06, 0.06), WOOD_D)
    for (x0, z0, x1, z1) in ((3.0, 1.0, 13.0, 1.0), (13.0, -9.0, 13.0, 1.0), (3.0, -9.0, 13.0, -9.0)):   # 무대 난간
        B.wall(x0, z0, x1, z1, 0.55, VERM, t=0.1, y0=2.4)
        n = int(math.hypot(x1 - x0, z1 - z0) / 0.6)
        for k in range(n + 1):
            t = k / n; cyl(P, (x0 + (x1 - x0) * t, 2.4, z0 + (z1 - z0) * t), 0.04, 0.55, VERM, n=8)
    # 본당 벽 (앞은 열림, 기둥만): 뒤·옆 벽, 높이 4.2
    H = 4.2
    B.wall(-10, -14, 3, -14, H, VERM_D, y0=2.4); B.wall(-10, -14, -10, -1, H, VERM_D, y0=2.4)
    B.wall(3, -14, 3, -9.2, H, VERM_D, y0=2.4)
    for x in np.linspace(-10, 3, 8):
        for z in (-1.0, -14.0): cyl(P, (x, 2.4, z), 0.2, H, VERM, n=8)
    for z in (-5.5, -10.0):
        for x in (-10, 3): cyl(P, (x, 2.4, z), 0.2, H, VERM, n=8)
    for x in np.linspace(-9.4, 2.4, 7):                               # 앞쪽 위 들어 올린 격자 덧문
        box(P, (x, 2.4 + H - 0.55, -1.0), (0.85, 0.5, 0.05), C('#8E5A34'))
        for yy in np.linspace(2.4 + H - 1.0, 2.4 + H - 0.1, 5): box(P, (x, yy, -0.96), (0.85, 0.012, 0.01), C('#5A3A20'))
    for z in (-14.02,): box(P, (-3.5, 2.4 + 2.4, z + 0.15), (5.8, 1.4, 0.02), C('#7A2420'))   # 뒤 벽 안쪽 휘장
    # 불상과 불단
    box(P, (-3.5, 2.4 + 0.45, -12.0), (3.2, 0.45, 1.6), C('#5A2E1E')); B.solid(-3.5, -12.0, 3.3, 1.7)
    box(P, (-3.5, 2.4 + 0.92, -10.3), (3.2, 0.03, 0.12), GOLD)
    buddha(P, (-3.5, 3.3, -12.2), 1.2)
    for x in (-6.0, -1.0):                                              # 촛대·꽃병
        cyl(P, (x, 3.3, -10.9), 0.08, 0.9, GOLD, n=8); ell(P, (x, 4.27, -10.9), (0.05, 0.09, 0.05), C('#FFB43A'), sub=1, glow=True)
        P.add(lathe([(0, 0), (0.18, 0), (0.24, 0.2), (0.12, 0.45), (0.15, 0.55), (0, 0.55)], 14), np.eye(3), (x + (0.8 if x < -3 else -0.8), 3.3, -11.0), GOLD)
        for k in range(4): ell(P, (x + (0.8 if x < -3 else -0.8) + 0.1 * (k - 1.5), 4.0 + 0.08 * (k % 2), -11.0), 0.1, C(['#F7A8C4', '#FFFFFF', '#F7D04A', '#F7A8C4'][k]), sub=1)
    cyl(P, (-3.5, 2.4, -9.6), 0.45, 0.35, C('#6E6246')); ell(P, (-3.5, 2.95, -9.6), (0.12, 0.25, 0.12), C('#C8C0B0', 0.5), sub=1, glow=True)   # 향로
    # 목탁과 방석 (절하는 자리 4×3)
    # 목탁 (방석 위 앞에 놓임) + 목탁 치는 자리
    MK = np.array([0.6, 2.4, -9.5])
    box(P, MK + (0, 0.14, 0), (0.32, 0.14, 0.26), C('#5A2E1E')); cyl(P, MK + (0, 0.28, 0), 0.2, 0.05, C('#7A2420'))
    ell(P, MK + (0, 0.46, 0), (0.24, 0.17, 0.2), C('#A4683A'), sub=2); box(P, MK + (0, 0.46, 0.2), (0.12, 0.012, 0.01), C('#3A2014'))
    box(P, (0.6, 2.43, -8.75), (0.42, 0.03, 0.42), C('#8E2E4A')); box(P, (0.6, 2.47, -8.75), (0.36, 0.015, 0.36), C('#B04466'))
    B.solid(0.6, -9.5, 0.34, 0.28); B.spot('moktak', 0.6, -8.75, (0.6, -9.5))
    for r_ in range(3):
        for c_ in range(4):
            x = -6.75 + 1.5 * c_ + 0.75 * (c_ >= 2) * 0 ; x = -5.8 + 1.55 * c_; z = -7.4 + 1.9 * r_
            box(P, (x, 2.43, z), (0.42, 0.03, 0.42), C('#8E2E4A')); box(P, (x, 2.47, z), (0.36, 0.015, 0.36), C('#B04466'))
            B.spot('bow', x, z, (x, -12.0))
    # 지붕 (실내에 들어가면 숨김)
    box(Rf, (-3.5, 2.4 + H + 0.1, -7.5), (6.9, 0.18, 6.9), VERM_D)
    curved_roof(Rf, (-3.5, 2.4 + H + 0.25, -7.5), 18.0, 17.5, 5.4, CYP, eave=1.8)
    curved_roof(Rf, (8.0, 2.4 + 3.2, -9.6), 5.5, 2.6, 1.0, CYP, eave=0.8)            # 무대 옆 작은 처마
    # 등롱·연등
    lantern_string(P, (-9.5, 1.2, 10.6), (2.5, 1.2, 10.6), n=13, h=3.0)
    for x in (-9.0, 2.0):
        q = np.array([x, 1.2, 2.0]); cyl(P, q, 0.2, 0.15, STONE); cyl(P, q + (0, 0.15, 0), 0.08, 0.8, STONE, n=8)
        box(P, q + (0, 1.1, 0), (0.22, 0.2, 0.22), STONE); box(P, q + (0, 1.1, 0), (0.12, 0.12, 0.23), C('#FFD98A'), glow=True)
        P.add(PYR4, np.diag([0.36, 0.28, 0.36]), q + (0, 1.3, 0), STONE_D); B.solid(x, 2.0, 0.3, 0.3)
    B.inside.append(dict(c=(-3.5, -7.5), h=(6.6, 6.6), roof='temple_roof'))
    B.door = (0, 0, 17.5); B.name = '단풍사 (절)'; B.zone = ((-2.0, 0, 0.0), 19.0)
    return B


# ---------------------------------------------------------------- 교회 (하얀 목조, 큰 실내)
def church():
    B = Bld(); P, Rf = B.body, B.roof
    W, WD, ROOF, RED = C('#F5F1E8'), C('#E4DED2'), C('#6E3B33'), C('#A8322E')
    HW, L0, L1, H = 4.2, -8.0, 7.0, 4.6          # 반폭, 뒤·앞 z, 벽 높이
    box(P, (0, 0.15, (L0 + L1) / 2), (HW + 0.3, 0.15, (L1 - L0) / 2 + 0.3), C('#B5AA98'))
    box(P, (0, 0.31, (L0 + L1) / 2), (HW - 0.1, 0.01, (L1 - L0) / 2 - 0.1), C('#B88A5A'))
    B.floor(0, (L0 + L1) / 2, HW + 0.3, (L1 - L0) / 2 + 0.3, 0.3)
    for s in (-1, 1):
        B.wall(s * HW, L0, s * HW, L1, H, W, y0=0.3)
        for y in np.arange(0.6, H, 0.22): box(P, (s * (HW + 0.13), 0.3 + y, (L0 + L1) / 2), (0.01, 0.012, (L1 - L0) / 2), WD)
        for z in np.arange(L0 + 1.6, L1 - 1.0, 2.6):              # 아치 창
            for d in (-1, 1):
                box(P, (s * (HW + d * 0.14), 2.4, z), (0.02, 0.8, 0.42), C('#FFE6A8'), glow=True)
                ell(P, (s * (HW + d * 0.14), 3.2, z), (0.02, 0.42, 0.42), C('#FFE6A8'), sub=1, glow=True)
    B.wall(-HW, L0, HW, L0, H, W, y0=0.3)
    B.wall(-HW, L1, -0.9, L1, H, W, y0=0.3); B.wall(0.9, L1, HW, L1, H, W, y0=0.3)
    box(P, (0, 0.3 + 2.9 + (H - 2.9) / 2, L1), (0.9, (H - 2.9) / 2, 0.12), W)
    # 종탑 (정문 위)
    for s in (-1, 1): box(P, (s * 1.05, 0.3 + 3.6, L1 + 0.9), (0.25, 3.6, 0.9), W); B.solid(s * 1.05, L1 + 0.9, 0.25, 0.9)
    box(P, (0, 0.3 + 5.9, L1 + 0.9), (1.3, 1.3, 1.0), W)
    box(P, (0, 0.3 + 3.25, L1 + 1.82), (0.85, 0.12, 0.05), W)
    box(P, (0, 0.3 + 6.0, L1 + 1.92), (0.5, 0.6, 0.03), C('#3A3030'))
    P.add(lathe([(0, 0), (0.3, 0), (0.26, 0.08), (0.2, 0.36), (0.09, 0.5), (0, 0.52)], 16), np.eye(3), (0, 0.3 + 5.6, L1 + 0.9), C('#D9B34A'))
    P.add(PYR4, Ry(math.pi / 4) @ np.diag([1.75, 3.6, 1.75]), (0, 0.3 + 7.2, L1 + 0.9), ROOF)
    box(P, (0, 0.3 + 11.2, L1 + 0.9), (0.06, 0.5, 0.06), C('#F2E6C0')); box(P, (0, 0.3 + 11.35, L1 + 0.9), (0.28, 0.06, 0.06), C('#F2E6C0'))
    # 열린 빨간 문
    for s in (-1, 1): door_leaf(P, (s * 0.85, 0.3, L1 + 1.8), 0.82, 2.8, -s * 1.9, '#A8322E', side=-s)
    P.add(torus(1.0, 0.25, 24, 8), Rx(math.pi / 2) @ np.diag([0.35, 0.35, 0.35]), (0, 0.3 + 3.6, L1 + 1.86), C('#2E6B3A'))
    B.floor(0, L1 + 0.9, 0.8, 0.9, 0.3)
    # 실내: 신자석, 강대상, 제단, 십자가, 파이프오르간
    for r_ in range(7):
        z = L1 - 2.2 - 1.25 * r_
        for s in (-1, 1):
            x = s * 2.15
            box(P, (x, 0.3 + 0.24, z), (1.45, 0.05, 0.24), C('#8A5A36')); box(P, (x, 0.3 + 0.55, z + 0.26), (1.45, 0.3, 0.04), C('#7A4E30'))
            for e in (-1, 1): box(P, (x + e * 1.45, 0.3 + 0.35, z + 0.05), (0.04, 0.35, 0.3), C('#6A4228'))
            B.solid(x, z + 0.27, 1.5, 0.06)
            for k in (-0.8, 0.0, 0.8): B.spot('pew', x + k, z, (x + k, L0))
    box(P, (0, 0.3 + 0.2, L0 + 1.6), (HW - 0.2, 0.2, 1.6), C('#9A6A42')); B.floor(0, L0 + 1.6, HW - 0.2, 1.6, 0.5)
    box(P, (0, 0.5 + 0.45, L0 + 1.2), (1.1, 0.45, 0.45), C('#F4EEE2')); box(P, (0, 0.5 + 0.92, L0 + 1.2), (1.15, 0.03, 0.5), C('#E8C86A'))
    B.solid(0, L0 + 1.2, 1.15, 0.5)
    for x in (-0.7, 0.7): cyl(P, (x, 1.45, L0 + 1.2), 0.04, 0.35, C('#FFF6E0'), n=8); ell(P, (x, 1.85, L0 + 1.2), (0.03, 0.06, 0.03), C('#FFB43A'), sub=1, glow=True)
    box(P, (0, 2.9, L0 + 0.16), (0.1, 1.2, 0.06), C('#7A4E30')); box(P, (0, 3.3, L0 + 0.16), (0.6, 0.1, 0.06), C('#7A4E30'))
    box(P, (2.6, 0.5 + 0.6, L0 + 2.6), (0.4, 0.6, 0.35), C('#7A4E30')); B.solid(2.6, L0 + 2.6, 0.45, 0.4)
    # 성가대 자리: 제단 앞 단 위 한 줄 + 그 앞 바닥 한 줄 (신자석을 바라봄), 악보대
    for x in (-2.3, -1.5, -0.7, 0.1, 0.9, 1.7): B.spot('choir', x, L0 + 2.75, (x, L1))
    for x in (-2.7, -1.9, -1.1, 1.1, 1.9, 2.7): B.spot('choir', x, L0 + 3.85, (x, L1))
    for x in (-3.3, 3.3):
        cyl(P, (x, 0.3, L0 + 3.85), 0.03, 1.0, C('#3A3030'), n=6); box(P, (x, 1.32, L0 + 3.75), (0.22, 0.16, 0.02), C('#2A2424')); B.solid(x, L0 + 3.85, 0.2, 0.2)
    for k in range(9):                                                         # 파이프오르간
        h = 1.2 + 0.25 * (4 - abs(k - 4)); cyl(P, (-3.6 + 0.0, 0.5 + 0.9, L0 + 0.6 + 0.28 * k), 0.1, h, C('#D8C07A'), n=8)
    box(P, (-3.5, 0.5 + 0.45, L0 + 1.7), (0.45, 0.45, 1.2), C('#6A4228')); B.solid(-3.5, L0 + 1.7, 0.5, 1.3)
    # 크리스마스트리 (안쪽 앞 구석) 와 바깥 트리
    for tp, sc in ((np.array([3.3, 0.3, L1 - 1.0]), 0.6), (np.array([4.6, 0.0, L1 + 3.2]), 1.0)):
        cyl(P, tp, 0.12 * sc, 0.4 * sc, C('#6A4A30'), n=8)
        for k in range(4): cone(P, tp + (0, (0.35 + 0.55 * k) * sc, 0), (0.95 - 0.2 * k) * sc, 0.9 * sc, C(['#2E6B3A', '#357A42', '#3E874A', '#48934F'][k]))
        for k in range(24):
            y = (0.5 + rng.random() * 2.0) * sc; r = (1.0 - (y / sc - 0.35) / 2.6) * 0.85 * sc; a = rng.random() * 6.28
            ell(P, tp + (math.cos(a) * r, y, math.sin(a) * r), 0.06 * sc ** 0.5, C(['#FF4A4A', '#FFD54A', '#6AC8FF', '#FFFFFF'][k % 4]), sub=1, glow=True)
        ell(P, tp + (0, 2.85 * sc, 0), 0.12 * sc, C('#FFE14D'), sub=1, glow=True)
        B.solid(tp[0], tp[2], 0.8 * sc, 0.8 * sc)
    # 지붕
    roof_gable(Rf, (0, 0.3 + H, (L0 + L1) / 2), 2 * HW, 2.6, L1 - L0, ROOF, over=0.4)
    B.inside.append(dict(c=(0, (L0 + L1) / 2), h=(HW, (L1 - L0) / 2), roof='church_roof'))
    B.door = (0, 0, L1 + 3.2); B.name = '은행나무 교회'; B.zone = ((0, 0, -0.5), 12.5)
    return B


# ---------------------------------------------------------------- 성당 (노트르담풍 고딕)
def cathedral():
    B = Bld(); P, Rf = B.body, B.roof
    S, SD, SL, LEAD = C('#D9CFBE'), C('#BDB2A0'), C('#58637A'), C('#6E7480')
    HW, L0, L1, H = 5.0, -13.0, 6.0, 7.5          # 신랑 반폭, 뒤(제단)·앞(정면) z, 벽 높이
    box(P, (0, 0.18, (L0 + L1) / 2), (HW + 0.4, 0.18, (L1 - L0) / 2 + 0.4), SD)
    box(P, (0, 0.37, (L0 + L1) / 2), (HW - 0.1, 0.01, (L1 - L0) / 2 - 0.1), C('#C8BCA6'))
    for x in np.arange(-HW + 0.5, HW, 1.0):
        for z in np.arange(L0 + 0.5, L1, 1.0):
            if (int(x + 10) + int(z + 20)) % 2: box(P, (x, 0.375, z), (0.48, 0.003, 0.48), C('#A89C86'))
    B.floor(0, (L0 + L1) / 2, HW + 0.4, (L1 - L0) / 2 + 0.4, 0.36)
    # 옆벽 + 색유리 창 + 날개 버팀벽
    for s in (-1, 1):
        B.wall(s * HW, L0, s * HW, L1, H, S, t=0.35, y0=0.36)
        for k, z in enumerate(np.arange(L0 + 1.6, L1 - 0.8, 2.6)):
            col = C(['#3E6FD0', '#C8384A', '#E0B23A', '#4AA06A', '#8A4AC2', '#3E9AD0'][k % 6])
            for d in (-1, 1):
                box(P, (s * (HW + d * 0.19), 3.6, z), (0.02, 1.7, 0.45), col, glow=True)
                P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.45, 0.6, 0.03]) if False else np.diag([0.03, 0.6, 0.45]), (s * (HW + d * 0.19), 5.3, z), col, glow=True)
            box(P, (s * (HW + 0.45), 2.6, z + 1.3), (0.28, 2.6, 0.22), SD)                                 # 버팀벽
            box(P, (s * (HW + 2.2), 2.0, z + 1.3), (0.35, 2.0, 0.3), SD)
            P.add(mh.box(), Rz(s * -0.62) @ np.diag([1.2, 0.12, 0.14]), (s * (HW + 1.35), 5.6, z + 1.3), SD, flat=True)   # 날개 버팀
            P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.35, 0.9, 0.35]), (s * (HW + 2.2), 4.0, z + 1.3), SD)
    B.wall(-HW, L0, HW, L0, H, S, t=0.35, y0=0.36)
    for k in range(5): box(P, (-3.2 + 1.6 * k, 4.0, L0 - 0.19), (0.3, 1.8, 0.02), C(['#3E6FD0', '#C8384A', '#E0B23A', '#C8384A', '#3E6FD0'][k]), glow=True)
    # 정면: 쌍탑(평평한 윗면), 장미창, 왕의 회랑, 세 개의 아치 문
    FW = 7.6; FZ = L1
    B.wall(-FW, FZ, -1.3, FZ, 11.0, S, t=0.6, y0=0.36); B.wall(1.3, FZ, FW, FZ, 11.0, S, t=0.6, y0=0.36)
    box(P, (0, 0.36 + 4.3 + 3.35, FZ), (1.3, 3.35, 0.3), S)
    for s in (-1, 1):
        cx = s * 5.3
        box(P, (cx, 0.36 + 7.5, FZ + 0.1), (2.3, 7.5, 2.4), S); B.solid(cx, FZ + 0.1, 2.3, 2.4)
        for y in (11.5, 13.2):
            for d in (-0.8, 0.8): box(P, (cx + d, y, FZ + 2.52), (0.32, 1.2, 0.03), C('#4A5070'))
        box(P, (cx, 15.0, FZ + 0.1), (2.45, 0.2, 2.55), SD)
        for x in (-2.2, 2.2):
            for z in (-2.3, 2.5): P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.18, 0.9, 0.18]), (cx + x, 15.2, FZ + 0.1 + z), SD)
        for k in range(9): box(P, (cx - 2.2 + 0.55 * k, 15.4, FZ + 2.6), (0.14, 0.2, 0.05), SD)
        # 옆 아치 문 (장식)
        box(P, (cx, 0.36 + 1.7, FZ + 2.52), (0.85, 1.7, 0.03), C('#4A3428'))
        P.add(PYR4, Ry(math.pi / 4) @ np.diag([1.2, 1.0, 0.04]), (cx, 0.36 + 3.4, FZ + 2.52), C('#4A3428'))
        for k in range(4): box(P, (cx, 0.36 + 3.6 + 0.0, FZ + 2.56 - 0.05 * k), (1.0 + 0.15 * k, 0.04, 0.02), SD)
    box(P, (0, 0.36 + 8.5, FZ + 1.3), (3.1, 2.4, 1.3), S)                       # 가운데 정면
    rc = np.array([0, 0.36 + 8.6, FZ + 2.62])
    ell(P, rc, (2.0, 2.0, 0.05), C('#2A3050'), sub=2)
    for ring, n, rr in ((0, 16, 1.55), (1, 8, 0.85)):
        for k in range(n):
            a = 2 * math.pi * k / n + ring * 0.2
            ell(P, rc + (math.cos(a) * rr, math.sin(a) * rr, 0.03), (0.32 - 0.08 * ring, 0.32 - 0.08 * ring, 0.02), C(['#3E6FD0', '#C8384A', '#E0B23A', '#4AA06A', '#8A4AC2'][k % 5]), sub=1, glow=True)
    ell(P, rc + (0, 0, 0.05), (0.35, 0.35, 0.02), C('#F2D26A'), sub=1, glow=True)
    P.add(torus(1.0, 0.06, 48, 6), np.diag([2.05, 2.05, 2.05]), rc + (0, 0, 0.04), SD)
    for k in range(13): box(P, (-2.9 + 0.48 * k, 0.36 + 5.75, FZ + 2.62), (0.14, 0.38, 0.06), C('#CFC4B0'))   # 왕의 회랑
    box(P, (0, 0.36 + 5.3, FZ + 2.62), (3.1, 0.07, 0.08), SD); box(P, (0, 0.36 + 6.2, FZ + 2.62), (3.1, 0.07, 0.08), SD)
    box(P, (0, 0.36 + 10.95, FZ + 1.3), (3.1, 0.1, 1.35), SD)
    for k in range(13): box(P, (-2.9 + 0.48 * k, 0.36 + 11.2, FZ + 2.6), (0.12, 0.18, 0.04), SD)
    # 가운데 정문 (열림, 뾰족 아치)
    for k in range(4): box(P, (0, 0.36 + 4.35 + 0.0, FZ + 2.64 - 0.0), (1.4 + 0.18 * k, 0.05, 0.03), SD)
    P.add(PYR4, Ry(math.pi / 4) @ np.diag([1.75, 1.2, 0.04]), (0, 0.36 + 3.2, FZ + 2.66), C('#E0D6C4'))
    for s in (-1, 1): door_leaf(P, (s * 1.25, 0.36, FZ + 2.4), 1.2, 3.1, -s * 1.85, '#5A3A28', side=-s)
    B.floor(0, FZ + 1.3, 1.25, 1.3, 0.36)
    for s in (-1, 1): B.solid(s * 2.2, FZ + 1.3, 0.85, 1.3)
    for k in range(5): box(P, (0, 0.06 + 0.06 * k, FZ + 2.7 + 0.35 * (4 - k) * 0.5), (2.8 + 0.1 * (4 - k), 0.06 + 0.06 * k, 0.2), SD)
    # 실내: 기둥 두 줄, 신자석, 제단, 십자고상, 봉헌 촛대
    for s in (-1, 1):
        for z in np.arange(L0 + 2.2, L1 - 1.0, 2.6):
            x = s * 2.9; cyl(P, (x, 0.36, z), 0.32, H - 0.2, C('#CFC4B0'), n=8); cyl(P, (x, 0.36, z), 0.45, 0.3, SD, n=8)
            cyl(P, (x, 0.36 + H - 0.5, z), 0.45, 0.3, SD, n=8); B.solid(x, z, 0.42, 0.42)
    for r_ in range(6):
        z = L1 - 3.0 - 1.35 * r_
        for s in (-1, 1):
            x = s * 1.6
            box(P, (x, 0.36 + 0.24, z), (0.95, 0.05, 0.24), C('#7A4E30')); box(P, (x, 0.36 + 0.55, z + 0.26), (0.95, 0.3, 0.04), C('#6A4228'))
            box(P, (x, 0.36 + 0.1, z - 0.42), (0.95, 0.04, 0.08), C('#5A3A20'))
            B.solid(x, z + 0.27, 1.0, 0.06)
            for k in (-0.45, 0.45): B.spot('pew', x + k, z, (x + k, L0))
    box(P, (0, 0.36 + 0.3, L0 + 2.4), (3.5, 0.3, 2.2), C('#B8AC96')); B.floor(0, L0 + 2.4, 3.5, 2.2, 0.66)
    for k in range(3): box(P, (0, 0.36 + 0.1 * k, L0 + 4.75 + 0.25 * k), (3.0, 0.1 * (k + 1) * 0.5 + 0.05, 0.14), SD)
    box(P, (0, 0.66 + 0.5, L0 + 1.6), (1.4, 0.5, 0.55), C('#F4EEE2')); box(P, (0, 0.66 + 1.02, L0 + 1.6), (1.45, 0.03, 0.6), C('#E8C86A'))
    B.solid(0, L0 + 1.6, 1.45, 0.6)
    for x in (-1.0, -0.5, 0.5, 1.0): cyl(P, (x, 1.7, L0 + 1.6), 0.04, 0.4, C('#FFF6E0'), n=8); ell(P, (x, 2.15, L0 + 1.6), (0.03, 0.07, 0.03), C('#FFB43A'), sub=1, glow=True)
    box(P, (0, 4.3, L0 + 0.3), (0.12, 1.9, 0.08), C('#6A4228')); box(P, (0, 5.2, L0 + 0.3), (0.9, 0.12, 0.08), C('#6A4228'))
    ell(P, (0, 5.0, L0 + 0.42), (0.14, 0.4, 0.08), C('#E8D8B8'), sub=1)
    # 성모상 (오른쪽 앞) + 봉헌 촛대 (촛불 켜기)
    mp = np.array([3.9, 0.36, L1 - 2.4])
    box(P, mp + (0, 0.35, 0), (0.4, 0.35, 0.4), SD); cone(P, mp + (0, 0.7, 0), 0.3, 1.1, C('#F4F0E8'))
    P.add(CONE, np.diag([0.34, 1.0, 0.34]), mp + (0, 0.72, -0.03), C('#6E8FD0')); ell(P, mp + (0, 1.85, 0), 0.14, C('#F4F0E8'), sub=1)
    ell(P, mp + (0, 1.88, -0.03), (0.17, 0.18, 0.16), C('#6E8FD0'), sub=1)
    P.add(torus(1.0, 0.1, 20, 6), Rx(0.2) @ np.diag([0.2, 0.2, 0.2]), mp + (0, 2.1, -0.06), C('#FFE07A'), glow=True)
    B.solid(mp[0], mp[2], 0.45, 0.45)
    # 세례대 (돌 그릇에 물, 왼쪽 앞)
    fp = np.array([-4.1, 0.36, L1 - 1.1])
    cyl(P, fp, 0.42, 0.12, SD, n=12); cyl(P, fp + (0, 0.12, 0), 0.16, 0.6, S, n=10)
    P.add(lathe([(0, 0), (0.25, 0), (0.48, 0.18), (0.56, 0.34), (0.5, 0.36), (0, 0.3)], 18), np.eye(3), fp + (0, 0.7, 0), S)
    cyl(P, fp + (0, 1.0, 0), 0.47, 0.02, C('#8EC8E8'), n=18, glow=True)
    B.solid(fp[0], fp[2], 0.55, 0.55); B.spot('baptism', fp[0], fp[2] - 1.05, (fp[0], fp[2]))
    cp = np.array([3.6, 0.36, L1 - 4.4])
    box(P, cp + (0, 0.45, 0), (0.8, 0.45, 0.35), C('#4A3A30'))
    for k in range(3):
        for j in range(5): cyl(P, cp + (-0.6 + 0.3 * j, 0.9 + 0.12 * k * 0, -0.2 + 0.2 * k), 0.035, 0.12, C('#FFF6E0'), n=8)
    B.solid(cp[0], cp[2], 0.85, 0.4); B.spot('candle', cp[0] - 1.0, cp[2], (cp[0], cp[2]))
    B.candle_rack = [(float(cp[0] - 0.6 + 0.3 * j), float(cp[2] - 0.2 + 0.2 * k)) for k in range(3) for j in range(5)]
    B.candle_y = 0.36 + 0.9 + 0.12
    # 지붕 + 첨탑 (실내에 들어가면 숨김)
    roof_gable(Rf, (0, 0.36 + H, (L0 + L1) / 2), 2 * HW, 4.2, L1 - L0, SL, over=0.35)
    fz = (L0 + L1) / 2 - 1.5
    box(Rf, (0, 0.36 + H + 4.6, fz), (0.6, 0.8, 0.6), LEAD)
    P_ = Rf; P_.add(PYR4, Ry(math.pi / 4) @ np.diag([0.75, 6.0, 0.75]), (0, 0.36 + H + 5.4, fz), LEAD)
    box(Rf, (0, 0.36 + H + 11.6, fz), (0.04, 0.4, 0.04), C('#E8C86A')); box(Rf, (0, 0.36 + H + 11.7, fz), (0.2, 0.04, 0.04), C('#E8C86A'))
    B.inside.append(dict(c=(0, (L0 + L1) / 2), h=(HW, (L1 - L0) / 2), roof='cathedral_roof'))
    B.door = (0, 0, FZ + 4.6); B.name = '별빛 성당'; B.zone = ((0, 0, -2.0), 16.0)
    return B


# ---------------------------------------------------------------- 마을 배치
COTTAGES = va.COTTAGES


def scatter(P):
    for z in np.arange(-13.0, -3.0, 2.2):
        for s in (-1, 1): maple(P, (s * 2.2, height(s * 2.2, z), z), 0.85 + 0.15 * rng.random())
    for x in np.arange(-14.5, -5.0, 2.6): ginkgo(P, (x, 0, -1.0 + 0.03 * x), 0.8); ginkgo(P, (x + 1.2, 0, 4.0), 0.75)
    for x in np.arange(6.0, 16.0, 2.6): maple(P, (x, 0, 0.0), 0.8, ['#F29A38', '#F2C230', '#E8552E']); maple(P, (x + 1.1, 0, 5.0), 0.75)
    # 절 무대 아래 단풍 골짜기, 절 둘레 숲
    for k in range(34):
        lx, lz = 5 + rng.random() * 13, -11 + rng.random() * 14
        if 3 < lx < 13.6 and -9.6 < lz < 1.6: lx += 0 if rng.random() < 0.4 else 0
        wx, wz = to_world('temple', lx, lz); y = height(wx, wz)
        if 2.6 < lx < 13.5 and -9.5 < lz < 1.5 and y > -0.6: continue
        maple(P, (wx, y, wz), 0.9 + 0.6 * rng.random())
    placed = 0
    while placed < 150:
        a = rng.random() * 2 * math.pi; r = 21 + rng.random() * 22
        x, z = math.cos(a) * r, math.sin(a) * r
        if any(abs(to_local(n, x, z)[0]) < hx and hz0 < to_local(n, x, z)[1] < hz1 for n, hx, hz0, hz1 in (('temple', 15, -17, 19), ('church', 8, -11, 13), ('cathedral', 11, -16, 12))): continue
        if min(va.seg_dist(np.array([x]), np.array([z]), p, q)[0] for p, q in PATHS) < 1.6: continue
        y = height(x, z); k = rng.random()
        (pine if k < 0.25 else ginkgo if k < 0.42 else maple)(P, (x, y, z), 0.9 + 0.7 * rng.random()); placed += 1
    for k in range(5): a = 0.6 + k * 1.15; maple(P, (POND[0] + math.cos(a) * 4.2, 0, POND[1] + math.sin(a) * 4.2), 0.85)
    bench(P, (POND[0] + 3.4, 0, POND[1] - 0.5), ry=-math.pi / 2)
    for x, z in ((-2.5, 13.5), (2.6, 13.0), (-1.2, 14.2), (3.5, 14.6), (-7.5, 6.2), (8.2, 6.8), (-11.0, -1.0)): pumpkin(P, (x, 0, z), 0.9 + 0.4 * rng.random())
    for x, z, ry in ((-3.5, 15.0, 0.3), (4.5, 15.8, -0.6), (8.0, 13.5, 1.1)): hay(P, (x, 0, z), ry)
    for k in range(40):
        x, z = (rng.random() - 0.5) * 40, (rng.random() - 0.5) * 34 + 3
        if min(va.seg_dist(np.array([x]), np.array([z]), p, q)[0] for p, q in PATHS) < 1.3 or math.hypot(x, z) < 5: continue
        if abs(x) > 14 or math.hypot(x - POND[0], z - POND[1]) < 4: continue
        bush(P, (x, height(x, z), z), 0.7 + 0.4 * rng.random(), ['#8A9A4A', '#B0763A', '#9A5A3A', '#7A8A44'][k % 4])
    for z in np.arange(-13.2, -0.5, 3.0):
        for s in (-1, 1): lamp(P, (s * 1.25, height(s * 1.25, z), z))


def rect_world(name, cx, cz, hx, hz):
    wx, wz = to_world(name, cx, cz); return [round(float(wx), 3), round(float(wz), 3)], [round(hx, 3), round(hz, 3)], round(ROT[name], 5)


def build_all():
    groups, layout = [], {'buildings': {}, 'homes': {}, 'zones': {}, 'spawn': {}, 'platforms': [], 'blockers': [], 'interiors': [], 'actions': {}, 'bound': BOUND}
    T = mh.Part(); terrain(T); groups.append(('terrain', T, (0, 0, 0), 0.0))
    S = mh.Part(); scatter(S); groups.append(('nature', S, (0, 0, 0), 0.0))
    Pz = mh.Part(); plaza(Pz); groups.append(('plaza', Pz, (0, 0, 0), 0.0))
    for name, fn in (('temple', temple), ('church', church), ('cathedral', cathedral)):
        B = fn(); c = {'temple': TEMPLE, 'church': CHURCH, 'cathedral': CATHEDRAL}[name]; ry = ROT[name]
        groups.append((name, B.body, (c[0], 0.0, c[1]), ry)); groups.append((name + '_roof', B.roof, (c[0], 0.0, c[1]), ry))
        door = to_world(name, B.door[0], B.door[2])
        layout['buildings'][name] = dict(name=B.name, position=[c[0], 0.0, c[1]], rotationY=round(ry, 5), door=[round(door[0], 3), 0.0, round(door[1], 3)])
        zc = to_world(name, B.zone[0][0], B.zone[0][2]); layout['zones'][name] = dict(center=[round(zc[0], 3), 0, round(zc[1], 3)], radius=B.zone[1], name=B.name)
        for (cx, cz, hx, hz) in B.blk:
            cc, hh, r = rect_world(name, cx, cz, hx, hz); layout['blockers'].append(dict(c=cc, h=hh, r=r))
        for (cx, cz, hx, hz, y0, y1) in B.plat:
            cc, hh, r = rect_world(name, cx, cz, hx, hz); layout['platforms'].append(dict(c=cc, h=hh, r=r, y0=round(y0, 3), y1=round(y1, 3)))
        for it in B.inside:
            cc, hh, r = rect_world(name, it['c'][0], it['c'][1], it['h'][0], it['h'][1]); layout['interiors'].append(dict(c=cc, h=hh, r=r, roof=it['roof']))
        for kind, lst in B.spots.items():
            out = []
            for (x, z, face) in lst:
                wx, wz = to_world(name, x, z); fx, fz = to_world(name, *face); yaw = math.atan2(fx - wx, fz - wz)
                out.append([round(wx, 3), round(wz, 3), round(yaw, 4)])
            layout['actions'][f'{name}_{kind}'] = out
        if hasattr(B, 'candle_rack'):
            layout['candles'] = dict(y=B.candle_y, p=[list(map(lambda v: round(v, 3), to_world(name, x, z))) for x, z in B.candle_rack])
    for k, (x, z, ry, wall, roof, who) in enumerate(COTTAGES):
        P = mh.Part(); info = cottage(P, wall, roof, chimney=k % 3 != 2); y = height(x, z) - 0.03
        groups.append((f'house_{who}', P, (x, y, z), ry))
        door = np.array([x, y, z]) + Ry(ry) @ np.array(info['door']); layout['homes'][who] = [round(float(v), 3) for v in door]
        layout['blockers'].append(dict(c=[x, z], h=[1.9, 1.7], r=round(ry, 4)))
    layout['blockers'] += [dict(c=[0, 0], h=[1.45, 1.45], r=0.0), dict(c=[POND[0], POND[1]], h=[2.6, 2.6], r=0.0)]
    layout['spawn']['plaza'] = [0.0, 0.0, 4.6]
    for n in ('temple', 'church', 'cathedral'): layout['spawn'][n] = layout['buildings'][n]['door']
    n = 105; xs = np.linspace(-R_WORLD, R_WORLD, n)
    layout['heightmap'] = dict(size=R_WORLD * 2, n=n, h=[round(height(x, z), 3) for z in xs for x in xs])
    return groups, layout


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    groups, layout = build_all()
    data, tris = v1.glb_bytes(groups); open(os.path.join(out, 'village.glb'), 'wb').write(data)
    with open(os.path.join(out, 'village_layout.js'), 'w') as f:
        f.write('// 단풍마을 배치: 건물·집, 소리 구역, 실내(지붕 숨김), 행동 자리, 높이맵, 걸을 수 있는 단, 막힌 곳 (미터)\n')
        f.write('export default ' + json.dumps(layout, ensure_ascii=False) + ';\n')
    print('village tris', tris, 'bytes', len(data), 'blockers', len(layout['blockers']))
    if 'check' in sys.argv:
        nr = [g for g in groups if not g[0].endswith('_roof')]
        v1.render_parts(groups, os.path.join(out, '_view.png'), 0.5, 0.6, (0, 0, -6.0), 0.0125, size=1300)
        v1.render_parts(groups, os.path.join(out, '_temple.png'), 0.55, 0.38, (0, 3.0, -28.0), 0.035, size=1000)
        v1.render_parts(nr, os.path.join(out, '_temple_in.png'), 0.3, 0.75, (-3.5, 2.5, -38.0), 0.06, size=900)
        v1.render_parts(groups, os.path.join(out, '_church.png'), 2.0, 0.3, (-26.0, 3.0, 2.0), 0.045, size=900)
        v1.render_parts(nr, os.path.join(out, '_church_in.png'), 1.57, 0.8, (-27.0, 0.5, 2.0), 0.06, size=900)
        v1.render_parts(groups, os.path.join(out, '_cathedral.png'), -1.9, 0.22, (22.0, 6.0, 2.0), 0.03, size=1000)
        v1.render_parts(nr, os.path.join(out, '_cathedral_in.png'), -1.57, 0.8, (29.0, 0.5, 2.0), 0.045, size=900)
        print('renders saved')
