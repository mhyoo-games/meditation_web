"""단풍마을 v3 — 땅은 높이맵+바닥 무늬 지도(브라우저에서 만듦), 나무·바위·풀·집은 Quaternius(CC0) 소품 배치 목록.
사용법: python3 village_autumn3.py <출력폴더> [check]
출력: village.glb (건물·연못·등불), village_layout.js (배치·막힘·높이맵·소품·등불), splat.png
"""
import sys, os, json, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hamster as mh
from make_hamster import C, Rx, Ry, Rz, torus, lathe
import village as v1
from village import box, cyl, cone, ell, bench, PYR4
import village_autumn as va
import village_autumn2 as v2
from village_autumn2 import to_world, to_local, TEMPLE, CHURCH, CATHEDRAL, POND, R_WORLD, BOUND, PATHS, ROT

rng = np.random.default_rng(7)


def height(x, z):   # v2 땅 + 연못을 더 넓고 깊게
    r = math.hypot(x - POND[0], z - POND[1]); k = max(0.0, 1 - r / 3.4)
    return v2.height(x, z) - 0.55 * k * k * (3 - 2 * k)

TREES_AUTUMN = [f'CommonTree_Autumn_{i}' for i in range(1, 6)] + [f'BirchTree_Autumn_{i}' for i in range(1, 6)]
WILLOWS = [f'Willow_Autumn_{i}' for i in range(1, 4)]
PINES = [f'PineTree_Autumn_{i}' for i in range(1, 4)] + [f'PineTree_{i}' for i in range(1, 4)]
ROCKS = [f'Rock_Moss_{i}' for i in range(1, 8)]
SMALL = ['Grass', 'Grass_2', 'Grass_Short', 'Flowers', 'Plant_1', 'Plant_2', 'Plant_3', 'Plant_5']
HOUSES = {'hamster': 'House_1', 'rabbit': 'House_2', 'cat': 'Inn', 'dog': 'House_3', 'bear': 'House_1', 'fox': 'House_2',
          'raccoon': 'House_4', 'squirrel': 'House_1', 'deer': 'House_2', 'panda': 'House_3', 'lion': 'Mill'}
HOUSE_BOX = {'House_1': (1.07, 1.34), 'House_2': (1.12, 2.07), 'House_3': (0.98, 1.07), 'House_4': (0.97, 1.07), 'Inn': (2.02, 2.01), 'Mill': (1.7, 1.39)}
HS = 1.3   # 집 배율
props, blockers, lights = [], [], []


def free_spot(x, z, pad):
    if math.hypot(x, z) > BOUND - 1: return False
    for (cx, cz, hx, hz, r) in OCC:
        lx, lz = rot_local(x - cx, z - cz, r)
        if abs(lx) < hx + pad and abs(lz) < hz + pad: return False
    if min(va.seg_dist(np.array([x]), np.array([z]), p, q)[0] for p, q in PATHS) < 1.2 + pad * 0.5: return False
    if math.hypot(x - POND[0], z - POND[1]) < 3.4 + pad: return False
    return True


def rot_local(dx, dz, r): c, s = math.cos(r), math.sin(r); return dx * c - dz * s, dx * s + dz * c


OCC = []   # 건물·집 자리 (cx, cz, hx, hz, r)


def place(model, x, z, s=1.0, ry=None, y=None, block=None):
    ry = rng.random() * 2 * math.pi if ry is None else ry
    y = height(x, z) - 0.02 if y is None else y
    props.append([model, round(x, 3), round(y, 3), round(z, 3), round(ry, 4), round(s, 3)])
    if block: blockers.append(dict(c=[round(x, 3), round(z, 3)], h=[round(block[0], 3), round(block[1], 3)], r=round(ry if len(block) < 3 else block[2], 4)))


# ---------------------------------------------------------------- 등불 (종이등, 석등, 연등)
def paper_lantern_post(P, x, z, col='#FFB35A'):
    y = height(x, z)
    cyl(P, (x, y, z), 0.05, 1.5, C('#4A3426'), n=8)
    box(P, (x + 0.18, y + 1.45, z), (0.22, 0.03, 0.03), C('#4A3426'))
    cyl(P, (x + 0.36, y + 1.2, z), 0.12, 0.22, C(col), n=8, glow=True)
    cyl(P, (x + 0.36, y + 1.18, z), 0.13, 0.03, C('#3A2A20'), n=8); cyl(P, (x + 0.36, y + 1.42, z), 0.13, 0.03, C('#3A2A20'), n=8)
    lights.append([round(x + 0.36, 3), round(y + 1.3, 3), round(z, 3), 1])
    blockers.append(dict(c=[x, z], h=[0.12, 0.12], r=0.0))


def stone_lantern(P, x, z, y=None):
    y = height(x, z) if y is None else y; S = C('#A9A398'); SD = C('#8E887E')
    cyl(P, (x, y, z), 0.26, 0.12, SD, n=8); cyl(P, (x, y + 0.12, z), 0.09, 0.55, S, n=8)
    cyl(P, (x, y + 0.67, z), 0.24, 0.08, SD, n=6)
    box(P, (x, y + 0.9, z), (0.18, 0.16, 0.18), S); box(P, (x, y + 0.9, z), (0.1, 0.1, 0.19), C('#FFC46A'), glow=True); box(P, (x, y + 0.9, z), (0.19, 0.1, 0.1), C('#FFC46A'), glow=True)
    P.add(PYR4, Ry(math.pi / 4) @ np.diag([0.38, 0.26, 0.38]), (x, y + 1.06, z), SD); ell(P, (x, y + 1.36, z), 0.06, SD, sub=1)
    lights.append([round(x, 3), round(y + 0.9, 3), round(z, 3), 0.8])
    blockers.append(dict(c=[x, z], h=[0.25, 0.25], r=0.0))


def float_lotus_lantern(P, x, z, y):
    for k in range(8):
        a = 2 * math.pi * k / 8
        ell(P, (x + math.cos(a) * 0.12, y + 0.05, z + math.sin(a) * 0.12), (0.09, 0.07, 0.05), C('#FFB0C8'), sub=1, glow=True, R=Ry(-a) @ Rz(0.6))
    ell(P, (x, y + 0.08, z), 0.07, C('#FFE7A0'), sub=1, glow=True)
    lights.append([round(x, 3), round(y + 0.15, 3), round(z, 3), 0.5])


# ---------------------------------------------------------------- 바닥 무늬 지도 (R 흙길, G 돌바닥, B 낙엽)
def splat(n=512):
    xs = np.linspace(-R_WORLD, R_WORLD, n); X, Z = np.meshgrid(xs, xs)
    d = np.min([va.seg_dist(X.ravel(), Z.ravel(), p, q) for p, q in PATHS], axis=0).reshape(n, n)
    noise = (np.sin(X * 1.7) * np.cos(Z * 1.3) + np.sin(X * 0.53 + Z * 0.71)) * 0.25
    R = np.clip((1.35 + noise * 0.6 - d) / 0.5, 0, 1)                              # 흙길 (가장자리 울퉁불퉁)
    rr = np.hypot(X, Z); G = np.clip((4.6 - rr) / 0.3, 0, 1)                         # 광장 돌바닥
    for nm, (cx, cz, hx, hz) in (('temple', (0, 16.0, 2.4, 1.2)), ('church', (0, 11.0, 1.6, 1.6)), ('cathedral', (0, 10.5, 3.2, 1.6))):
        wx, wz = to_world(nm, cx, cz); r = ROT[nm]
        lx = (X - wx) * math.cos(r) - (Z - wz) * math.sin(r); lz = (X - wx) * math.sin(r) + (Z - wz) * math.cos(r)
        G = np.maximum(G, np.clip(1 - np.maximum(np.abs(lx) - hx, np.abs(lz) - hz) / 0.3, 0, 1))
    rnd = np.random.default_rng(3).random((n, n))
    B = np.clip((rnd - 0.55) * 2.2 + 0.35 * np.sin(X * 0.21 + 1) * np.sin(Z * 0.17), 0, 1) * (1 - R) * (1 - G)
    pond = np.hypot(X - POND[0], Z - POND[1]); R = np.maximum(R, np.clip((3.3 - pond) / 0.4, 0, 1) * 0.8)
    img = np.stack([R, G, B, np.ones_like(R)], -1)
    return Image.fromarray((img * 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- 배치
def scatter(P):
    global OCC
    # 건물 자리
    OCC = [(TEMPLE[0], TEMPLE[1] - 2.0, 15.0, 18.5, 0.0), (CHURCH[0], CHURCH[1], 12.5, 6.5, 0.0), (CATHEDRAL[0], CATHEDRAL[1], 15.0, 10.0, 0.0), (0, 0, 5.2, 5.2, 0.0)]
    for x, z, ry, wall, roof, who in v2.COTTAGES: hx, hz = HOUSE_BOX[HOUSES[who]]; OCC.append((x, z, hx * HS + 0.8, hz * HS + 1.6, ry))
    # 광장 큰 단풍나무
    place('CommonTree_Autumn_2', 0, 0, 2.2, 0.4, y=0.32, block=(0.5, 0.5))
    # 길가 가로수 (단풍길)
    for z in np.arange(-12.0, -3.5, 3.1):
        for s in (-1, 1): place(TREES_AUTUMN[int(rng.integers(0, 5))], s * (3.7 + rng.random() * 0.4), z + rng.random() * 0.6, 1.9 + rng.random() * 0.4, block=(0.3, 0.3))
    for x in np.arange(-14.5, -5.0, 2.8):
        place('BirchTree_Autumn_%d' % int(rng.integers(1, 6)), x, -2.0, 2.0, block=(0.25, 0.25)); place('BirchTree_Autumn_%d' % int(rng.integers(1, 6)), x + 1.3, 5.4, 2.0, block=(0.25, 0.25))
    for x in np.arange(6.0, 16.0, 2.8):
        place(TREES_AUTUMN[int(rng.integers(0, 5))], x, -0.6, 2.0, block=(0.3, 0.3)); place(TREES_AUTUMN[int(rng.integers(0, 5))], x + 1.2, 5.6, 1.9, block=(0.3, 0.3))
    # 절 아래 골짜기와 둘레 숲
    for k in range(40):
        lx, lz = 3 + rng.random() * 16, -12 + rng.random() * 16
        wx, wz = to_world('temple', lx, lz); y = height(wx, wz)
        if 2.6 < lx < 13.5 and -9.5 < lz < 1.5 and y > -0.8: continue
        place(TREES_AUTUMN[int(rng.integers(0, 10))], wx, wz, 2.0 + rng.random() * 0.9, block=(0.3, 0.3))
    for k in range(26):
        a = rng.random() * math.pi * 2; r = 17 + rng.random() * 6; wx, wz = TEMPLE[0] + math.cos(a) * r, TEMPLE[1] - 2 + math.sin(a) * r * 0.9
        if wz > -17 and abs(wx) < 4: continue
        if not free_spot(wx, wz, 0.6): continue
        place((TREES_AUTUMN + PINES)[int(rng.integers(0, 16))], wx, wz, 2.0 + rng.random() * 1.0, block=(0.3, 0.3))
    # 바깥 숲 (빽빽하게)
    placed = 0; tries = 0
    while placed < 260 and tries < 6000:
        tries += 1; a = rng.random() * 2 * math.pi; r = 14 + rng.random() * 30
        x, z = math.cos(a) * r, math.sin(a) * r
        if not free_spot(x, z, 0.8): continue
        k = rng.random(); m = (PINES if k < 0.22 else WILLOWS if k < 0.3 else TREES_AUTUMN)[int(rng.integers(0, 10)) % (6 if k < 0.22 else 3 if k < 0.3 else 10)]
        place(m, x, z, 1.9 + rng.random() * 1.2, block=(0.3, 0.3) if r < BOUND else None); placed += 1
    # 덤불, 바위, 풀, 꽃
    for k in range(160):
        x, z = (rng.random() - 0.5) * 78, (rng.random() - 0.5) * 78
        if not free_spot(x, z, 0.4): continue
        q = rng.random()
        if q < 0.3: place(['Bush_1', 'Bush_2', 'BushBerries_1', 'BushBerries_2'][k % 4], x, z, 0.9 + rng.random() * 0.5, block=(0.45, 0.45))
        elif q < 0.55: place(ROCKS[k % 7], x, z, 1.2 + rng.random() * 1.0, block=(0.3, 0.3))
        elif q < 0.65: place(['TreeStump_Moss', 'WoodLog_Moss'][k % 2], x, z, 1.1, block=(0.45, 0.6) if k % 2 else (0.45, 0.45))
        else:
            for j in range(4): place(SMALL[(k + j) % len(SMALL)], x + rng.random() * 1.4, z + rng.random() * 1.4, 1.0 + rng.random() * 0.6)
    for k in range(420):                                     # 풀 무더기 (막지 않음)
        x, z = (rng.random() - 0.5) * 80, (rng.random() - 0.5) * 80
        if not free_spot(x, z, 0.0): continue
        place(['Grass_Short', 'Grass', 'Grass_2'][k % 3], x, z, 1.0 + rng.random() * 0.8)
    # 연못: 연잎, 버드나무, 바위, 떠 있는 연등
    for k in range(9):
        a = k * 0.7 + 0.3; rr = 0.8 + (k % 3) * 0.6
        place('Lilypad', POND[0] + math.cos(a) * rr, POND[1] + math.sin(a) * rr * 0.9, 0.8 + 0.2 * (k % 2), y=-0.27)
    for a in (0.5, 2.3, 4.0): place('Willow_Autumn_%d' % (1 + int(a) % 3), POND[0] + math.cos(a) * 4.6, POND[1] + math.sin(a) * 4.6, 2.2, block=(0.3, 0.3))
    for k in range(5): float_lotus_lantern(P, POND[0] + math.cos(k * 1.3) * 1.5, POND[1] + math.sin(k * 1.3) * 1.2, -0.28)
    for k in range(16):
        a = 2 * math.pi * k / 16; place(ROCKS[k % 7], POND[0] + math.cos(a) * 3.0, POND[1] + math.sin(a) * 3.0, 0.9 + 0.4 * (k % 3), y=-0.12)
    blockers.append(dict(c=[POND[0], POND[1]], h=[2.8, 2.8], r=0.0))
    # 마을 소품
    place('Well', -4.6, -4.4, 1.6, 0.6, block=(0.55, 0.55)); place('Bonfire_Lit', 4.2, 7.6, 1.6, 0.0, block=(0.35, 0.35)); lights.append([4.2, 0.4, 7.6, 1.4])
    place('MarketStand_1', -3.4, 7.2, 1.5, 0.4, block=(0.75, 0.9)); place('MarketStand_2', 3.0, 9.8, 1.5, -0.5, block=(0.75, 0.9))
    place('Gazebo', -10.5, 14.5, 1.8, 0.9, block=(0.15, 0.15))
    for x, z, ry in ((-3.6, 15.0, 0.3), (4.5, 15.8, -0.6), (8.0, 13.5, 1.1)): place('Hay', x, z, 4.0, ry, block=(0.25, 0.25))
    for x, z in ((-6.5, -5.4), (-6.8, -5.9), (7.2, -5.8), (7.5, -5.3)): place('Barrel', x, z, 1.8, block=(0.15, 0.15))
    for x, z in ((6.6, -6.6), (6.9, -6.9)): place('Crate', x, z, 2.0, block=(0.16, 0.16))
    place('Cart', 9.0, 9.0, 1.6, 2.2, block=(0.4, 0.6))
    # 등불: 길가 종이등, 절 앞 석등
    for z in np.arange(-12.0, -1.0, 3.2):
        for s in (-1, 1): paper_lantern_post(P, s * 1.55, z)
    for x in np.arange(-14.0, -4.0, 3.4): paper_lantern_post(P, x, 1.0 + 0.11 * x * 0.0 + (-1.0 if int(x) % 2 else 1.1) * 0.0 + 1.3)
    for x in np.arange(6.0, 16.0, 3.4): paper_lantern_post(P, x, 3.2)
    for z in np.arange(6.5, 14.0, 3.2): paper_lantern_post(P, 1.4, z)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        if k % 2: stone_lantern(P, math.cos(a) * 3.9, math.sin(a) * 3.9)
    for wx, wz in [to_world('temple', x, z) for x, z in ((-2.6, 15.6), (2.6, 15.6), (-2.6, 17.4), (2.6, 17.4))]: stone_lantern(P, wx, wz)
    for wx, wz in [to_world('church', x, z) for x, z in ((-1.8, 10.6), (1.8, 10.6))] + [to_world('cathedral', x, z) for x, z in ((-3.2, 10.8), (3.2, 10.8))]: stone_lantern(P, wx, wz)
    for k in range(6): a = 0.3 + k * 1.05; bench(P, (POND[0] + math.cos(a) * 3.9, 0, POND[1] + math.sin(a) * 3.9), ry=-a - math.pi / 2) if k in (1, 4) else None
    # 집 (Quaternius) — 오두막 자리에
    homes = {}
    for x, z, ry, wall, roof, who in v2.COTTAGES:
        m = HOUSES[who]; hx, hz = HOUSE_BOX[m]
        y = height(x, z) - 0.02
        props.append([m, x, round(y, 3), z, round(ry, 4), HS])
        blockers.append(dict(c=[x, z], h=[round(hx * HS * 0.95, 3), round(hz * HS * 0.95, 3)], r=round(ry, 4)))
        d = Ry(ry) @ np.array([0, 0, hz * HS + 0.9]); homes[who] = [round(x + d[0], 3), round(y, 3), round(z + d[2], 3)]
        paper_lantern_post(P, x + (Ry(ry) @ np.array([hx * HS * 0.7, 0, hz * HS + 0.5]))[0], z + (Ry(ry) @ np.array([hx * HS * 0.7, 0, hz * HS + 0.5]))[2], '#FFC878')
    return homes


def plaza(P):
    cyl(P, (0, 0, 0), 1.4, 0.32, C('#BFB3A0'))
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        if k % 2 == 0: bench(P, (math.cos(a) * 3.2, 0, math.sin(a) * 3.2), ry=-a - math.pi / 2); blockers.append(dict(c=[round(math.cos(a) * 3.2, 3), round(math.sin(a) * 3.2, 3)], h=[0.55, 0.25], r=round(a + math.pi / 2, 4)))
    cyl(P, (1.8, 0, 3.6), 0.05, 1.7, C('#6E4A30'), n=8)
    for yy, ang in ((1.55, 1.6), (1.3, -1.5), (1.05, 3.1)): box(P, np.array([1.8, yy, 3.6]) + Ry(ang) @ np.array([0.3, 0, 0]), (0.32, 0.08, 0.03), C('#E8DCC0'), ry=ang)
    blockers.append(dict(c=[1.8, 3.6], h=[0.1, 0.1], r=0.0))


def build_all():
    groups, layout = [], {'buildings': {}, 'homes': {}, 'zones': {}, 'spawn': {}, 'platforms': [], 'blockers': [], 'interiors': [], 'actions': {}, 'bound': BOUND}
    N = mh.Part(); W = mh.Part()
    cyl(W, (POND[0], -0.32, POND[1]), 2.85, 0.06, C('#3E6A8A'))
    groups.append(('water', W, (0, 0, 0), 0.0))
    homes = scatter(N); groups.append(('lights', N, (0, 0, 0), 0.0))
    Pz = mh.Part(); plaza(Pz); groups.append(('plaza', Pz, (0, 0, 0), 0.0))
    for name, fn in (('temple', v2.temple), ('church', v2.church), ('cathedral', v2.cathedral)):
        B = fn(); c = {'temple': TEMPLE, 'church': CHURCH, 'cathedral': CATHEDRAL}[name]; ry = ROT[name]
        groups.append((name, B.body, (c[0], 0.0, c[1]), ry)); groups.append((name + '_roof', B.roof, (c[0], 0.0, c[1]), ry))
        door = to_world(name, B.door[0], B.door[2])
        layout['buildings'][name] = dict(name=B.name, position=[c[0], 0.0, c[1]], rotationY=round(ry, 5), door=[round(door[0], 3), 0.0, round(door[1], 3)])
        zc = to_world(name, B.zone[0][0], B.zone[0][2]); layout['zones'][name] = dict(center=[round(zc[0], 3), 0, round(zc[1], 3)], radius=B.zone[1], name=B.name)
        for (cx, cz, hx, hz) in B.blk:
            cc, hh, r = v2.rect_world(name, cx, cz, hx, hz); layout['blockers'].append(dict(c=cc, h=hh, r=r))
        for (cx, cz, hx, hz, y0, y1) in B.plat:
            cc, hh, r = v2.rect_world(name, cx, cz, hx, hz); layout['platforms'].append(dict(c=cc, h=hh, r=r, y0=round(y0, 3), y1=round(y1, 3)))
        for it in B.inside:
            cc, hh, r = v2.rect_world(name, it['c'][0], it['c'][1], it['h'][0], it['h'][1]); layout['interiors'].append(dict(c=cc, h=hh, r=r, roof=it['roof']))
        for kind, lst in B.spots.items():
            out = []
            for (x, z, face) in lst:
                wx, wz = to_world(name, x, z); fx, fz = to_world(name, *face); out.append([round(wx, 3), round(wz, 3), round(math.atan2(fx - wx, fz - wz), 4)])
            layout['actions'][f'{name}_{kind}'] = out
        if hasattr(B, 'candle_rack'):
            layout['candles'] = dict(y=B.candle_y, p=[[round(v, 3) for v in to_world(name, x, z)] for x, z in B.candle_rack])
    # 실내 등불: 절 안 연등(천장에 매단 종이등), 교회·성당 샹들리에
    H = mh.Part(); cols = ['#FF7A9A', '#FFB45A', '#FFE07A', '#FF6A5A', '#FFA0C8', '#FFC870']
    for i, lx in enumerate((-7.2, -4.8, -2.2, 0.2)):
        for j, lz in enumerate((-9.6, -6.4, -3.4)):
            wx, wz = to_world('temple', lx, lz); y = 5.0 + 0.15 * ((i + j) % 2)
            cyl(H, (wx, y + 0.3, wz), 0.01, 0.9, C('#3A2A20'), n=4)
            ell(H, (wx, y, wz), (0.2, 0.24, 0.2), C(cols[(i * 3 + j) % 6]), sub=2, glow=True)
            cyl(H, (wx, y - 0.27, wz), 0.07, 0.06, C('#C8A040'), n=8)
            if (i + j) % 2 == 0: lights.append([round(wx, 3), round(y - 0.2, 3), round(wz, 3), 0.9])
    for nm, xs, y in (('church', (-4.0, 0.5, 5.0), 3.7), ('cathedral', (-8.0, -2.0, 4.0), 5.6)):
        for lz in xs:
            wx, wz = to_world(nm, 0, lz)
            cyl(H, (wx, y + 0.35, wz), 0.015, 1.4, C('#3A3028'), n=4); torus_ring = cyl(H, (wx, y, wz), 0.55, 0.05, C('#8A6A3A'), n=16)
            for k in range(8):
                a = 2 * math.pi * k / 8; ell(H, (wx + math.cos(a) * 0.5, y + 0.12, wz + math.sin(a) * 0.5), (0.04, 0.08, 0.04), C('#FFD27A'), sub=1, glow=True)
            lights.append([round(wx, 3), round(y - 0.1, 3), round(wz, 3), 1.0])
    groups.append(('hanging', H, (0, 0, 0), 0.0))
    # 실내 등불 (불단 촛불, 성당 촛대, 교회 제단)
    for x, z, y in ((-6.0, -10.9, 4.3), (-1.0, -10.9, 4.3), (-3.5, -9.6, 3.0)): wx, wz = to_world('temple', x, z); lights.append([round(wx, 3), y, round(wz, 3), 0.9])
    wx, wz = to_world('church', 0, -6.8); lights.append([round(wx, 3), 1.9, round(wz, 3), 0.9])
    wx, wz = to_world('cathedral', 0, -11.4); lights.append([round(wx, 3), 2.2, round(wz, 3), 1.0])
    layout['homes'] = homes
    layout['blockers'] += blockers
    layout['spawn']['plaza'] = [0.0, 0.0, 4.6]
    for n in ('temple', 'church', 'cathedral'): layout['spawn'][n] = layout['buildings'][n]['door']
    n = 241; xs = np.linspace(-R_WORLD, R_WORLD, n)
    layout['heightmap'] = dict(size=R_WORLD * 2, n=n, h=[round(height(x, z), 2) for z in xs for x in xs])
    layout['props'] = props; layout['lights'] = lights
    return groups, layout


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    groups, layout = build_all()
    data, tris = v1.glb_bytes(groups); open(os.path.join(out, 'village.glb'), 'wb').write(data)
    splat().save(os.path.join(out, 'splat.png'), optimize=True)
    with open(os.path.join(out, 'village_layout.js'), 'w') as f:
        f.write('// 단풍마을 배치 v3: 건물·집·소리 구역·실내·행동 자리·높이맵·걸을 수 있는 단·막힌 곳·소품(Quaternius)·등불\n')
        f.write('export default ' + json.dumps(layout, ensure_ascii=False, separators=(',', ':')) + ';\n')
    used = sorted(set(p[0] for p in props))
    json.dump(used, open(os.path.join(out, 'props_used.json'), 'w'))
    print('village tris', tris, 'bytes', len(data), 'props', len(props), 'models', len(used), 'blockers', len(layout['blockers']), 'lights', len(lights))
