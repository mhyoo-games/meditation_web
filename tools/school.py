"""별빛 마법학교 — 성(대강당·도서관·탑) + 안뜰 + 천문대 + 호수 + 소나무 숲. 몽환적인 밤.
사용법: python3 school.py <출력폴더>
출력: school.glb, school_layout.js, splat.png, props_used.json
"""
import sys, os, json, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hamster as mh
from make_hamster import C, Rx, Ry, Rz, lathe
import village as v1
from village import box, cyl, cone, ell, PYR4
import village_autumn as va

rng = np.random.default_rng(11)
R_WORLD, BOUND = 52, 40
ST, ST_D, ST_L = C('#8C889A'), C('#6E6A80'), C('#A9A4B6')      # 성 돌 (보랏빛 회색)
SLATE, SLATE_D = C('#3C4262'), C('#2C3050')
WIN, WIN2 = C('#FFCF86'), C('#9CC8FF')
WOOD, WOOD_D, WOOD_L = C('#6A4228'), C('#4A2C18'), C('#8A5A36')
GOLD = C('#E8C060')
LAKE = (25.0, 9.0)
PATHS = [((0, 22), (0, 9)), ((0, 9), (0, -6)), ((0, -2), (-9.5, -12)), ((3, 0), (15, 6)), ((6, 6), (19, 10)), ((-3, 3), (-12, 4))]
props, blockers, lights, spots, plats, interiors = [], [], [], {}, [], []


def height(x, z):
    r = math.hypot(x, z); h = 0.0
    if r > 30: h += min(4.0, (r - 30) * 0.28) * (0.7 + 0.3 * math.sin(x * 0.2) * math.cos(z * 0.17))
    d = math.hypot(x - LAKE[0], z - LAKE[1]); k = max(0.0, 1 - d / 7.5)
    h -= 1.3 * k * k * (3 - 2 * k)
    return h


def blk(cx, cz, hx, hz, r=0.0): blockers.append(dict(c=[round(cx, 3), round(cz, 3)], h=[round(hx, 3), round(hz, 3)], r=round(r, 4)))
def spot(kind, x, z, fx, fz): spots.setdefault(kind, []).append([round(x, 3), round(z, 3), round(math.atan2(fx - x, fz - z), 4)])
def wall(P, x0, z0, x1, z1, h, col=ST, t=0.5, y0=0.0, block=True):
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; hx, hz = max(abs(x1 - x0) / 2, t / 2), max(abs(z1 - z0) / 2, t / 2)
    box(P, (cx, y0 + h / 2, cz), (hx, h / 2, hz), col)
    if block: blk(cx, cz, hx, hz)


def prism_roof(P, cx, cz, hx, hz, y0, h, col, along='z'):
    """맞배 지붕 (뾰족한 고딕 지붕)"""
    if along == 'z':
        V = np.array([[-hx, 0, -hz], [hx, 0, -hz], [0, h, -hz], [-hx, 0, hz], [hx, 0, hz], [0, h, hz]], float)
    else:
        V = np.array([[-hx, 0, -hz], [-hx, 0, hz], [-hx, h, 0], [hx, 0, -hz], [hx, 0, hz], [hx, h, 0]], float)
    F = np.array([[0, 2, 1], [3, 4, 5], [0, 3, 5], [0, 5, 2], [1, 2, 5], [1, 5, 4], [0, 1, 4], [0, 4, 3]])
    P.add((V, F), np.eye(3), (cx, y0, cz), col)


def gothic_window(P, c, w, h, normal, col=WIN):
    """뾰족 아치 창 (빛남)"""
    c = np.array(c, float); n = np.array(normal, float); xn = abs(n[0]) > 0.5
    box(P, c, (0.03, h / 2, w / 2) if xn else (w / 2, h / 2, 0.03), col, glow=True)
    M = np.diag([0.06, w * 0.75, w * 0.7071]) if xn else np.diag([w * 0.7071, w * 0.75, 0.06])
    P.add(PYR4, M @ Ry(math.pi / 4), c + (0, h / 2, 0), col, glow=True)
    box(P, c + n * 0.04, (0.02, h / 2, 0.04) if xn else (0.04, h / 2, 0.02), ST_D)


def round_tower(P, x, z, r, h, roof_h, win=True, col=ST, roofcol=SLATE):
    y0 = height(x, z) - 0.2
    cyl(P, (x, y0, z), r, h, col, n=16)
    for k in range(int(h // 1.2)):    # 돌 줄눈
        cyl(P, (x, y0 + 1.2 * (k + 1) - 0.04, z), r + 0.02, 0.06, ST_D, n=16)
    for k in range(12):               # 성가퀴
        a = 2 * math.pi * k / 12
        box(P, (x + math.cos(a) * (r + 0.05), y0 + h + 0.25, z + math.sin(a) * (r + 0.05)), (0.25, 0.25, 0.25), ST_L, ry=-a)
    cyl(P, (x, y0 + h, z), r + 0.25, 0.25, ST_L, n=16)
    cone(P, (x, y0 + h + 0.2, z), r + 0.45, roof_h, roofcol)
    ell(P, (x, y0 + h + roof_h + 0.3, z), 0.14, GOLD, sub=1, glow=True)
    if win:
        for k in range(3):
            for j in range(int(h // 3.5)):
                a = 2 * math.pi * (k / 3 + j * 0.17); yy = y0 + 2.5 + j * 3.3
                wx, wz = x + math.cos(a) * (r + 0.02), z + math.sin(a) * (r + 0.02)
                box(P, (wx, yy, wz), (0.03 if abs(math.cos(a)) > 0.7 else 0.22, 0.45, 0.22 if abs(math.cos(a)) > 0.7 else 0.03), WIN, glow=True)
    blk(x, z, r * 0.92, r * 0.92)


# ---------------------------------------------------------------- 대강당
HALL = dict(x0=-6.5, x1=6.5, z0=-27.0, z1=-7.0, H=8.5)
def great_hall(P, R, Cd):
    x0, x1, z0, z1, H = HALL['x0'], HALL['x1'], HALL['z0'], HALL['z1'], HALL['H']
    box(P, ((x0 + x1) / 2, 0.1, (z0 + z1) / 2), ((x1 - x0) / 2, 0.1, (z1 - z0) / 2), C('#5A5468'))
    for zz in np.arange(z0 + 1, z1, 2.0):    # 바닥 무늬
        box(P, (0, 0.205, zz), ((x1 - x0) / 2 - 0.3, 0.005, 0.04), C('#4A4458'))
    plats.append(dict(c=[0, (z0 + z1) / 2], h=[(x1 - x0) / 2, (z1 - z0) / 2], r=0.0, y0=0.2, y1=0.2))
    wall(P, x0, z0, x0, z1, H); wall(P, x1, z0, x1, z1, H); wall(P, x0, z0, x1, z0, H)
    wall(P, x0, z1, -1.6, z1, H); wall(P, 1.6, z1, x1, z1, H); box(P, (0, 4.6 + (H - 4.6) / 2, z1), (1.6, (H - 4.6) / 2, 0.25), ST)
    # 문틀 아치 + 열린 문
    for s in (-1, 1): box(P, (s * 1.75, 2.3, z1 + 0.3), (0.2, 2.3, 0.2), ST_L)
    P.add(PYR4, np.diag([1.4, 1.2, 0.3]) @ Ry(math.pi / 4), (0, 4.6, z1 + 0.3), ST_L)
    for s in (-1, 1): box(P, (s * 2.4, 2.2, z1 + 0.9), (0.8, 2.2, 0.06), WOOD_D, ry=s * 0.9)
    # 버팀벽 + 뾰족 창 (양옆)
    for zz in np.arange(z0 + 2, z1 - 1, 3.2):
        for s, xx in ((-1, x0), (1, x1)):
            box(P, (xx + s * 0.45, 3.0, zz - 1.6), (0.35, 3.0, 0.35), ST_D)
            gothic_window(P, (xx + s * 0.27, 4.4, zz), 1.0, 3.6, (s, 0, 0)); gothic_window(P, (xx - s * 0.27, 4.4, zz), 1.0, 3.6, (-s, 0, 0))
    # 북쪽 큰 장미창
    for k in range(16):
        a = 2 * math.pi * k / 16; box(P, (math.cos(a) * 1.1, 6.0 + math.sin(a) * 1.1, z0 + 0.27), (0.3, 0.3, 0.03), [WIN2, WIN, C('#E89AD0')][k % 3], glow=True)
    ell(P, (0, 6.0, z0 + 0.3), (0.5, 0.5, 0.05), WIN, sub=1, glow=True)
    # 지붕 (실내에서 숨김)
    prism_roof(R, 0, (z0 + z1) / 2, (x1 - x0) / 2 + 0.6, (z1 - z0) / 2 + 0.4, H, 5.0, SLATE, 'z')
    for zz in np.arange(z0 + 3, z1 - 2, 4.5): box(R, (0, H + 5.0, zz), (0.15, 0.4, 0.15), GOLD)
    interiors.append(dict(c=[0, (z0 + z1) / 2], h=[(x1 - x0) / 2 - 0.2, (z1 - z0) / 2 - 0.2], r=0.0, roof='hall_roof'))
    # 긴 식탁 4줄 + 의자
    for tx in (-3.9, -1.3, 1.3, 3.9):
        box(P, (tx, 0.95, -16.0), (0.45, 0.05, 5.6), WOOD)
        for zz in (-21.3, -16, -10.7): box(P, (tx, 0.55, zz), (0.3, 0.4, 0.06), WOOD_D)
        blk(tx, -16.0, 0.5, 5.6)
        for s in (-1, 1):
            box(P, (tx + s * 0.85, 0.5, -16.0), (0.2, 0.04, 5.6), WOOD_L); box(P, (tx + s * 0.85, 0.3, -16.0), (0.15, 0.2, 5.5), WOOD_D)
            for zz in np.arange(-20.8, -10.9, 1.65): spot('hall_sit', tx + s * 0.85, zz, tx, zz)
        for zz in np.arange(-21.0, -10.5, 1.2):   # 접시·잔·음식
            for s in (-1, 1):
                cyl(P, (tx + s * 0.25, 1.0, zz), 0.13, 0.02, C('#F0EAD8'), n=10)
                if rng.random() < 0.5: ell(P, (tx + s * 0.25, 1.06, zz), (0.07, 0.04, 0.07), [C('#E8A040'), C('#C8402E'), C('#8EB850')][int(rng.integers(0, 3))], sub=1)
                cyl(P, (tx + s * 0.25, 1.0, zz + 0.35), 0.04, 0.12, GOLD, n=6)
    # 교수 단상
    box(P, (0, 0.45, -24.7), (5.8, 0.25, 1.6), C('#5A5468')); plats.append(dict(c=[0, -24.7], h=[5.8, 1.6], r=0.0, y0=0.7, y1=0.7))
    box(P, (0, 1.45, -24.6), (4.6, 0.05, 0.5), WOOD); blk(0, -24.6, 4.6, 0.5)
    for xx in np.arange(-4, 4.1, 1.0): box(P, (xx, 1.3, -25.4), (0.25, 0.6, 0.06), C('#6A2A3A'))
    # 촛불 띄우는 자리 (단상 앞 촛대)
    cyl(P, (0, 0.2, -22.4), 0.06, 1.2, GOLD, n=8); cyl(P, (0, 1.4, -22.4), 0.22, 0.04, GOLD, n=10); ell(P, (0, 1.6, -22.4), (0.05, 0.09, 0.05), WIN, sub=1, glow=True)
    blk(0, -22.4, 0.2, 0.2); spot('hall_candle', 0, -21.6, 0, -22.4); spot('hall_candle', -0.9, -21.7, 0, -22.4); spot('hall_candle', 0.9, -21.7, 0, -22.4)
    # 기숙사 깃발
    for k, (xx, col) in enumerate(((-6.2, '#B03040'), (-6.2, '#3060B0'), (6.2, '#C8A030'), (6.2, '#3A8A4A'))):
        zz = -20 if k % 2 == 0 else -13
        box(P, (xx + (0.3 if xx < 0 else -0.3), 5.5, zz), (0.04, 1.4, 0.55), C(col)); P.add(PYR4, np.diag([0.04, 0.5, 0.55]) @ Ry(math.pi / 4) @ Rx(math.pi), (xx + (0.3 if xx < 0 else -0.3), 4.1, zz), C(col))
    # 떠 있는 촛불 (지붕이 사라지면 밤하늘 아래 떠 있음)
    for k in range(90):
        x, z, y = rng.uniform(x0 + 0.8, x1 - 0.8), rng.uniform(z0 + 1, z1 - 1), rng.uniform(5.3, 7.3)
        cyl(Cd, (x, y, z), 0.045, 0.28, C('#F6EFD8'), n=6); ell(Cd, (x, y + 0.36, z), (0.035, 0.07, 0.035), WIN, sub=1, glow=True)
    for xx, zz in ((-3, -20), (3, -20), (-3, -12), (3, -12), (0, -16)): lights.append([xx, 6.2, zz, 1.0])


# ---------------------------------------------------------------- 도서관
LIB = dict(x0=-26.0, x1=-11.0, z0=-26.0, z1=-6.0, H=10.0)
BOOKC = [C(h) for h in ('#7A2E2E', '#2E4E7A', '#3A6A3A', '#8A6A2A', '#5A3A6A', '#2E5A5A', '#9A4A2A', '#4A3A2A', '#C8A060', '#6A2A4A')]
def shelf(P, x0, z0, x1, z1, h, face, rows=5):
    """책장 하나 (face: 책이 보이는 방향 벡터)"""
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; L = max(abs(x1 - x0), abs(z1 - z0)); ax = 'x' if abs(x1 - x0) > abs(z1 - z0) else 'z'
    d = 0.42
    hx, hz = (L / 2, d / 2) if ax == 'x' else (d / 2, L / 2)
    box(P, (cx, h / 2, cz), (hx, h / 2, hz), WOOD_D)
    fx, fz = face
    for r in range(rows):
        y = 0.25 + r * (h - 0.4) / rows
        box(P, (cx + fx * 0.2, y, cz + fz * 0.2), (hx if ax == 'x' else 0.03, 0.03, hz if ax == 'z' else 0.03), WOOD_L)
        t = -L / 2 + 0.06
        while t < L / 2 - 0.1:
            w = rng.uniform(0.08, 0.17); bh = rng.uniform(0.3, (h - 0.4) / rows * 0.85)
            if rng.random() < 0.06: t += w; continue
            px, pz = (cx + t + w / 2, cz + fz * 0.23) if ax == 'x' else (cx + fx * 0.23, cz + t + w / 2)
            box(P, (px, y + 0.03 + bh / 2, pz), (w / 2 if ax == 'x' else 0.13, bh / 2, 0.13 if ax == 'x' else w / 2), BOOKC[int(rng.integers(0, len(BOOKC)))])
            t += w + 0.005
    blk(cx, cz, hx + 0.05, hz + 0.05)


def library(P, R, Fl):
    x0, x1, z0, z1, H = LIB['x0'], LIB['x1'], LIB['z0'], LIB['z1'], LIB['H']
    box(P, ((x0 + x1) / 2, 0.1, (z0 + z1) / 2), ((x1 - x0) / 2, 0.1, (z1 - z0) / 2), C('#9A7652'))
    for xx in np.arange(x0 + 0.5, x1, 1.0): box(P, (xx, 0.205, (z0 + z1) / 2), (0.02, 0.005, (z1 - z0) / 2 - 0.3), C('#5A3A26'))
    plats.append(dict(c=[(x0 + x1) / 2, (z0 + z1) / 2], h=[(x1 - x0) / 2, (z1 - z0) / 2], r=0.0, y0=0.2, y1=0.2))
    dz = -16.0   # 문 (동쪽 벽)
    wall(P, x0, z0, x0, z1, H); wall(P, x0, z0, x1, z0, H); wall(P, x0, z1, x1, z1, H)
    wall(P, x1, z0, x1, dz - 1.6, H); wall(P, x1, dz + 1.6, x1, z1, H); box(P, (x1, 4.6 + (H - 4.6) / 2, dz), (0.25, (H - 4.6) / 2, 1.6), ST)
    for s in (-1, 1): box(P, (x1 + 0.3, 2.3, dz + s * 1.75), (0.2, 2.3, 0.2), ST_L); box(P, (x1 + 0.9, 2.2, dz + s * 2.4), (0.06, 2.2, 0.8), WOOD_D, ry=s * 0.9 + math.pi / 2)
    P.add(PYR4, np.diag([0.3, 1.2, 1.4]) @ Ry(math.pi / 4), (x1 + 0.3, 4.6, dz), ST_L)
    for zz in np.arange(z0 + 2, z1 - 1, 3.0):
        gothic_window(P, (x0 - 0.27, 6.8, zz), 0.9, 3.0, (-1, 0, 0)); gothic_window(P, (x0 + 0.27, 6.8, zz), 0.9, 3.0, (1, 0, 0), col=WIN2)
    for xx in np.arange(x0 + 2, x1 - 1, 3.0):
        gothic_window(P, (xx, 6.8, z0 - 0.27), 0.9, 3.0, (0, 0, -1)); gothic_window(P, (xx, 6.8, z0 + 0.27), 0.9, 3.0, (0, 0, 1), col=WIN2)
    prism_roof(R, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2 + 0.6, (z1 - z0) / 2 + 0.4, H, 5.5, SLATE, 'z')
    interiors.append(dict(c=[(x0 + x1) / 2, (z0 + z1) / 2], h=[(x1 - x0) / 2 - 0.2, (z1 - z0) / 2 - 0.2], r=0.0, roof='library_roof'))
    # 벽 책장 (창 아래 높이 5.0)
    shelf(P, x0 + 0.5, z0 + 0.6, x0 + 0.5, z1 - 0.6, 5.0, (1, 0)); shelf(P, x0 + 0.8, z0 + 0.5, x1 - 0.8, z0 + 0.5, 5.0, (0, 1))
    shelf(P, x0 + 0.8, z1 - 0.5, x1 - 4.0, z1 - 0.5, 5.0, (0, -1))
    # 가운데 책장 줄 (양면) — 통로를 남김
    for zz in (-22.5, -19.0):
        for xx0, xx1 in ((-24.6, -19.6),):
            shelf(P, xx0, zz, xx1, zz, 4.2, (0, 1)); shelf(P, xx0, zz - 0.43, xx1, zz - 0.43, 4.2, (0, -1))
    for zz in (-12.5, -9.0):
        shelf(P, -24.6, zz, -19.6, zz, 4.2, (0, 1)); shelf(P, -24.6, zz + 0.43, -19.6, zz + 0.43, 4.2, (0, -1))
    # 사다리
    for zz in (-20.5, -11.0):
        for k in (0, 1): box(P, (x0 + 0.95, 2.6, zz + k * 0.5), (0.03, 2.6, 0.03), WOOD_L)
        for y in np.arange(0.4, 5.0, 0.4): box(P, (x0 + 0.95, y, zz + 0.25), (0.02, 0.02, 0.25), WOOD_L)
    # 읽는 책상 (초록 등) — 가운데 통로
    for k, zz in enumerate((-21.0, -16.0, -11.0)):
        xx = -15.8
        box(P, (xx, 0.95, zz), (0.7, 0.05, 1.3), WOOD); blk(xx, zz, 0.75, 1.35)
        for s in (-1, 1): box(P, (xx, 0.55, zz + s * 1.1), (0.6, 0.4, 0.06), WOOD_D)
        for dz2 in (-0.6, 0.6):
            cyl(P, (xx, 1.0, zz + dz2), 0.03, 0.4, GOLD, n=6); ell(P, (xx, 1.42, zz + dz2), (0.16, 0.08, 0.12), C('#3A8A5A'), sub=1, glow=True)
            lights.append([xx, 1.6, zz + dz2, 0.6])
            box(P, (xx + 0.3, 1.02, zz + dz2), (0.14, 0.02, 0.2), C('#F0E6CC'))
        for s in (-1, 1):
            for dz2 in (-0.6, 0.6):
                cx2 = xx + s * 1.05; box(P, (cx2, 0.48, zz + dz2), (0.24, 0.04, 0.24), WOOD_L); box(P, (cx2 + s * 0.22, 0.85, zz + dz2), (0.03, 0.38, 0.24), WOOD_D)
                spot('library_read', cx2, zz + dz2, xx, zz + dz2)
    for xx, zz, fx, fz in ((-24.9, -14.5, -26, -14.5), (-24.9, -17.5, -26, -17.5), (-22, -24.9, -22, -26), (-17, -24.9, -17, -26), (-22, -18.4, -22, -19.0), (-22, -13.2, -22, -12.5)):
        spot('library_shelf', xx + (0.6 if fx < xx else 0), zz + (0.6 if fz < zz and abs(fz - zz) > 0.3 else -0.6 if fz > zz and abs(fz - zz) > 0.3 else 0), fx, fz)
    # 떠다니는 책 (빛나는 페이지) + 샹들리에
    for k in range(26):
        x, z, y = rng.uniform(x0 + 2, x1 - 2), rng.uniform(z0 + 2, z1 - 2), rng.uniform(4.5, 8.0)
        a = rng.uniform(0, 6.28)
        box(Fl, (x, y, z), (0.16, 0.025, 0.12), BOOKC[k % len(BOOKC)], ry=a)
        for s in (-1, 1): box(Fl, (x + math.cos(a) * s * 0.08, y + 0.05, z - math.sin(a) * s * 0.08), (0.07, 0.008, 0.11), C('#FFF2C8'), ry=a + s * 0.3, glow=True)
    for zz in (-21, -11):
        cyl(P, (-18.5, 7.0, zz), 0.02, 3.0, C('#3A3028'), n=4); cyl(P, (-18.5, 6.9, zz), 0.8, 0.06, GOLD, n=16)
        for k in range(10): a = 2 * math.pi * k / 10; ell(P, (-18.5 + math.cos(a) * 0.75, 7.08, zz + math.sin(a) * 0.75), (0.04, 0.08, 0.04), WIN, sub=1, glow=True)
        lights.append([-18.5, 6.8, zz, 1.0])
    for xx in (-22.0, -15.5):
        for zz in (-22.0, -16.0, -10.0): lights.append([xx, 4.5, zz, 1.1])
    # 지구본
    cyl(P, (-13.0, 0.2, -23.5), 0.05, 0.9, WOOD_D, n=6); ell(P, (-13.0, 1.4, -23.5), 0.36, C('#4A7AA8'), sub=2); blk(-13, -23.5, 0.35, 0.35)


# ---------------------------------------------------------------- 성벽·탑·안뜰·천문대·문
def castle(P):
    # 대강당과 도서관을 잇는 성벽 + 탑
    wall(P, -11.0, -6.6, -6.5, -6.6, 6.0, t=0.8)
    round_tower(P, -7.2, -27.8, 2.2, 13, 6); round_tower(P, 7.2, -27.8, 2.2, 13, 6)
    round_tower(P, 7.4, -6.2, 1.8, 10, 5); round_tower(P, -26.6, -26.6, 2.0, 14, 6.5); round_tower(P, -26.6, -5.6, 1.8, 11, 5)
    round_tower(P, 12.5, -20.0, 3.0, 21, 8.5)            # 높은 탑
    round_tower(P, -10.2, -5.2, 1.4, 8, 4)
    # 성의 바깥 큰 벽 (북쪽 배경)
    wall(P, -26.0, -29.5, 12.0, -29.5, 9.0, col=ST_D, t=1.0)
    for xx in np.arange(-25, 12, 1.4): box(P, (xx, 9.3, -29.5), (0.35, 0.3, 0.55), ST_D)
    # 남문 (아치)
    for s in (-1, 1):
        box(P, (s * 2.4, 3.2, 12.0), (0.8, 3.2, 0.8), ST); cone(P, (s * 2.4, 6.4, 12.0), 1.1, 2.5, SLATE); blk(s * 2.4, 12.0, 0.8, 0.8)
        wall(P, s * 3.2, 12.0, s * 11.0, 12.0, 3.2, t=0.6)
        round_tower(P, s * 11.6, 12.0, 1.4, 6, 3.2)
    box(P, (0, 5.6, 12.0), (1.6, 0.6, 0.6), ST); P.add(PYR4, np.diag([1.2, 0.8, 0.4]) @ Ry(math.pi / 4), (0, 6.2, 12.0), ST_L)
    for s in (-1, 1): box(P, (s * 1.7, 5.0, 12.65), (0.12, 0.25, 0.12), GOLD)
    # 안뜰 분수
    cyl(P, (0, 0, 2.0), 2.2, 0.55, ST_L, n=20); cyl(P, (0, 0.55, 2.0), 1.95, 0.02, C('#5A8AC8'), n=20, glow=True)
    cyl(P, (0, 0.5, 2.0), 0.3, 1.4, ST, n=10); cyl(P, (0, 1.9, 2.0), 0.9, 0.12, ST_L, n=14); ell(P, (0, 2.3, 2.0), (0.25, 0.4, 0.25), C('#9CD8FF'), sub=1, glow=True)
    blk(0, 2.0, 2.2, 2.2); lights.append([0, 2.4, 2.0, 1.2])
    # 마법진 (안뜰 동쪽) — 바닥에 빛나는 원
    mc = (7.0, -1.0)
    for k in range(48):
        a = 2 * math.pi * k / 48
        for rr in (1.7, 1.2):
            box(P, (mc[0] + math.cos(a) * rr, 0.03, mc[1] + math.sin(a) * rr), (0.12 if rr > 1.5 else 0.09, 0.01, 0.03), C('#9CC8FF'), ry=-a + math.pi / 2, glow=True)
    for k in range(6):
        a = 2 * math.pi * k / 6; b = a + 2 * math.pi / 6
        p0 = np.array([math.cos(a), math.sin(a)]) * 1.2; p1 = np.array([math.cos(b), math.sin(b)]) * 1.2; m = (p0 + p1) / 2; L = np.linalg.norm(p1 - p0)
        box(P, (mc[0] + m[0], 0.03, mc[1] + m[1]), (L / 2, 0.01, 0.025), C('#C8A8FF'), ry=-math.atan2(p1[1] - p0[1], p1[0] - p0[0]), glow=True)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4; spot('magic_cast', mc[0] + math.cos(a) * 2.3, mc[1] + math.sin(a) * 2.3, mc[0], mc[1])
    lights.append([mc[0], 0.6, mc[1], 0.8])
    # 천문대 테라스 (동쪽 언덕) + 망원경
    tc = (16.0, 4.0)
    cyl(P, (tc[0], -0.1, tc[1]), 3.4, 0.5, ST_L, n=20); plats.append(dict(c=[tc[0], tc[1]], h=[2.4, 2.4], r=0.0, y0=0.4, y1=0.4))
    for k in range(10):
        a = 2 * math.pi * k / 10
        if k in (6, 7): continue
        box(P, (tc[0] + math.cos(a) * 3.2, 0.75, tc[1] + math.sin(a) * 3.2), (0.12, 0.35, 0.12), ST)
    for k, a in enumerate((0.3, 2.4, 4.4)):
        px, pz = tc[0] + math.cos(a) * 1.4, tc[1] + math.sin(a) * 1.4
        cyl(P, (px, 0.4, pz), 0.05, 1.0, WOOD_D, n=6)
        ang = a + math.pi
        c0 = np.array([px, 1.55, pz]); d = np.array([math.cos(ang) * 0.5, 0.55, math.sin(ang) * 0.5])
        for j in range(7): ell(P, c0 + d * (j / 6 - 0.5) * 1.2, 0.09 - j * 0.004, GOLD if j % 3 else C('#8A6A30'), sub=1)
        blk(px, pz, 0.2, 0.2)
        spot('stars', px + math.cos(a) * 0.6, pz + math.sin(a) * 0.6, px, pz)
    lights.append([tc[0], 1.2, tc[1], 0.6])


# ---------------------------------------------------------------- 등불 기둥
def lamp_post(P, x, z):
    y = height(x, z)
    cyl(P, (x, y, z), 0.07, 2.1, C('#2A2A36'), n=8); box(P, (x, y + 2.3, z), (0.16, 0.2, 0.16), C('#2A2A36'))
    box(P, (x, y + 2.3, z), (0.12, 0.16, 0.17), WIN, glow=True); box(P, (x, y + 2.3, z), (0.17, 0.16, 0.12), WIN, glow=True)
    P.add(PYR4, np.diag([0.28, 0.2, 0.28]) @ Ry(math.pi / 4), (x, y + 2.5, z), C('#2A2A36'))
    lights.append([round(x, 3), round(y + 2.3, 3), round(z, 3), 0.9]); blk(x, z, 0.12, 0.12)


def float_lantern(P, x, z, y):
    box(P, (x, y + 0.1, z), (0.12, 0.12, 0.12), C('#FFD08A'), glow=True); box(P, (x, y - 0.03, z), (0.14, 0.02, 0.14), WOOD_D)
    lights.append([round(x, 3), round(y + 0.3, 3), round(z, 3), 0.4])


def place(model, x, z, s=1.0, ry=None, y=None, block=None):
    ry = rng.random() * 2 * math.pi if ry is None else ry
    y = height(x, z) - 0.02 if y is None else y
    props.append([model, round(x, 3), round(y, 3), round(z, 3), round(ry, 4), round(s, 3)])
    if block: blk(x, z, block[0], block[1], ry)


OCC = [(-10.0, -18.5, 19.0, 14.0), (0, 3, 14, 11.5), (16, 4, 5.5, 5.5), (0, 14, 14, 3.5), (12.5, -20, 5, 5), (0, 19, 5, 5)]
def free(x, z, pad):
    if math.hypot(x, z) > BOUND - 1: return False
    for cx, cz, hx, hz in OCC:
        if abs(x - cx) < hx + pad and abs(z - cz) < hz + pad: return False
    if min(va.seg_dist(np.array([x]), np.array([z]), p, q)[0] for p, q in PATHS) < 1.3 + pad: return False
    if math.hypot(x - LAKE[0], z - LAKE[1]) < 7.2 + pad: return False
    return True


def scatter(P):
    PINES = [f'PineTree_{i}' for i in range(1, 4)] + [f'PineTree_Autumn_{i}' for i in range(1, 3)]
    n = 0; t = 0
    while n < 230 and t < 8000:
        t += 1; a = rng.random() * 6.283; r = 18 + rng.random() * 32; x, z = math.cos(a) * r, math.sin(a) * r
        if not free(x, z, 2.8): continue
        place(PINES[int(rng.integers(0, len(PINES)))], x, z, 1.6 + rng.random() * 1.1, block=(0.3, 0.3) if r < BOUND else None); n += 1
    for k in range(120):
        x, z = (rng.random() - 0.5) * 80, (rng.random() - 0.5) * 80
        if not free(x, z, 0.3): continue
        q = rng.random()
        if q < 0.35: place(f'Rock_Moss_{1 + k % 7}', x, z, 1.1 + rng.random(), block=(0.3, 0.3))
        elif q < 0.55: place(['Bush_1', 'Bush_2'][k % 2], x, z, 1.0, block=(0.45, 0.45))
        else:
            for j in range(3): place(['Grass', 'Grass_2', 'Grass_Short', 'Plant_1'][(k + j) % 4], x + rng.random(), z + rng.random(), 1.0 + rng.random() * 0.5)
    for k in range(300):
        x, z = (rng.random() - 0.5) * 80, (rng.random() - 0.5) * 80
        if free(x, z, 0.0): place(['Grass_Short', 'Grass'][k % 2], x, z, 1.0 + rng.random() * 0.6)
    for k in range(12): place('Lilypad', LAKE[0] + math.cos(k * 0.9) * (1.5 + k % 4), LAKE[1] + math.sin(k * 0.9) * (1.2 + k % 3), 0.9, y=-0.62)
    for k in range(9): float_lantern(P, LAKE[0] + math.cos(k * 0.7 + 0.3) * (1.0 + (k % 3) * 1.4), LAKE[1] + math.sin(k * 0.7 + 0.3) * (1.0 + (k % 3) * 1.1), -0.66)
    for k in range(18): a = 2 * math.pi * k / 18; place(f'Rock_Moss_{1 + k % 7}', LAKE[0] + math.cos(a) * 7.0, LAKE[1] + math.sin(a) * 7.0, 1.2, y=height(LAKE[0] + math.cos(a) * 7, LAKE[1] + math.sin(a) * 7) - 0.15)
    blk(LAKE[0], LAKE[1], 6.4, 6.4)
    for z in np.arange(19, 13, -3.0):
        for s in (-1, 1): lamp_post(P, s * 1.8, z)
    for z in np.arange(8, -5, -4.0):
        for s in (-1, 1): lamp_post(P, s * 3.2, z) if abs(z - 2) > 2.5 else None
    for x, z in ((-6.0, -4.5), (-9.0, -8.5), (5.5, 3.5), (10.0, 5.0), (13.0, 7.0), (-6.5, 4.0), (-11.0, 4.0)): lamp_post(P, x, z)
    # 벤치 (주민의 자리)
    homes = {}
    keys = ['hamster', 'rabbit', 'cat', 'dog', 'lion', 'bear', 'panda', 'fox', 'raccoon', 'squirrel', 'deer']
    seats = [(-5.5, 7.5), (5.5, 7.5), (-7.5, 0.5), (8.0, 3.5), (-4.0, -4.0), (4.0, -4.0), (-12.0, 6.0), (12.0, 9.5), (19.5, 6.5), (-2.5, 16), (2.5, 16)]
    for k, (x, z) in zip(keys, seats):
        v1.bench(P, (x, height(x, z), z), ry=math.atan2(-x, -z)); blk(x, z, 0.55, 0.3, math.atan2(-x, -z))
        homes[k] = [x + 0.6 * math.sin(math.atan2(-x, -z)), 0.0, z + 0.6 * math.cos(math.atan2(-x, -z))]
    return homes


def splat(n=512):
    xs = np.linspace(-R_WORLD, R_WORLD, n); X, Z = np.meshgrid(xs, xs)
    d = np.min([va.seg_dist(X.ravel(), Z.ravel(), p, q) for p, q in PATHS], axis=0).reshape(n, n)
    noise = (np.sin(X * 1.7) * np.cos(Z * 1.3) + np.sin(X * 0.53 + Z * 0.71)) * 0.25
    R = np.clip((1.3 + noise * 0.5 - d) / 0.5, 0, 1)
    G = np.zeros_like(R)
    G = np.maximum(G, np.clip(1 - np.maximum(np.abs(X - 0.5) - 11.5, np.abs(Z - 2.5) - 9.5) / 0.4, 0, 1))   # 안뜰 돌바닥
    G = np.maximum(G, np.clip((3.6 - np.hypot(X - 16, Z - 4)) / 0.3, 0, 1))
    G = np.maximum(G, np.clip(1 - np.maximum(np.abs(X) - 2.2, np.abs(Z - 17) - 6) / 0.3, 0, 1))
    R = R * (1 - G)
    lake = np.hypot(X - LAKE[0], Z - LAKE[1]); R = np.maximum(R, np.clip((7.8 - lake) / 0.6, 0, 1) * 0.8)
    B = np.zeros_like(R)
    return Image.fromarray((np.stack([R, G, B, np.ones_like(R)], -1) * 255).astype(np.uint8), 'RGBA')


def build_all():
    P, R1, R2, Cd, Fl, W = (mh.Part() for _ in range(6))
    great_hall(P, R1, Cd); library(P, R2, Fl); castle(P)
    homes = scatter(P)
    cyl(W, (LAKE[0], -0.55, LAKE[1]), 7.3, 0.04, C('#24365A'))
    groups = [('castle', P, (0, 0, 0), 0.0), ('hall_roof', R1, (0, 0, 0), 0.0), ('library_roof', R2, (0, 0, 0), 0.0), ('candles', Cd, (0, 0, 0), 0.0), ('books', Fl, (0, 0, 0), 0.0), ('water', W, (0, 0, 0), 0.0)]
    n = 241; xs = np.linspace(-R_WORLD, R_WORLD, n)
    layout = {
        'buildings': {'hall': dict(name='대강당', position=[0, 0, -17], rotationY=0, door=[0.0, 0.0, -5.2]),
                      'library': dict(name='도서관', position=[-18.5, 0, -16], rotationY=0, door=[-9.2, 0.0, -16.0]),
                      'stars': dict(name='천문대', position=[16, 0, 4], rotationY=0, door=[13.4, 0.0, 5.6]),
                      'courtyard': dict(name='안뜰', position=[0, 0, 5], rotationY=0, door=[0.0, 0.0, 6.0]),
                      'lake': dict(name='별빛 호수', position=[LAKE[0], 0, LAKE[1]], rotationY=0, door=[18.0, 0.0, 12.0])},
        'zones': {'hall': dict(center=[0, 0, -17], radius=10.5, name='대강당'), 'library': dict(center=[-18.5, 0, -16], radius=10.5, name='도서관'),
                  'tower': dict(center=[16, 0, 4], radius=5.5, name='천문대')},
        'spawn': {'plaza': [0.0, 0.0, 18.0]}, 'homes': homes, 'platforms': plats, 'blockers': blockers, 'interiors': interiors,
        'actions': spots, 'bound': BOUND, 'props': props, 'lights': lights,
        'heightmap': dict(size=R_WORLD * 2, n=n, h=[round(height(x, z), 2) for z in xs for x in xs]),
    }
    return groups, layout


def glb_small(groups):
    """village.glb_bytes 와 같지만 정점 색을 8비트로 (파일 크기 줄이기)"""
    import struct
    b, views, accs = bytearray(), [], []
    def push(arr, typ, comp=5126, target=None, mm=False, norm=False):
        while len(b) % 4: b.append(0)
        raw = np.ascontiguousarray(arr).tobytes(); views.append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw), **({'target': target} if target else {})}); b.extend(raw)
        a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': int(arr.shape[0]), 'type': typ}
        if norm: a['normalized'] = True
        if mm: a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
        accs.append(a); return len(accs) - 1
    nodes = [{'name': 'root', 'children': []}]; meshes = []; tris = 0
    for name, P, t, ry in groups:
        prims = []
        for kind, mat in (('toon', 0), ('glow', 1)):
            g = P.merged(kind, np.zeros(3))
            if g is None: continue
            Pp, Nn, Cc, I = g; tris += len(I)
            c8 = np.round(np.clip(Cc, 0, 1) * 255).astype(np.uint8)
            prims.append({'attributes': {'POSITION': push(Pp.astype(np.float32), 'VEC3', target=34962, mm=True), 'NORMAL': push(Nn.astype(np.float32), 'VEC3', target=34962), 'COLOR_0': push(c8, 'VEC4', 5121, 34962, norm=True)},
                          'indices': push(I.reshape(-1).astype(np.uint32), 'SCALAR', 5125, 34963), 'material': mat})
        meshes.append({'name': name, 'primitives': prims})
        nodes.append({'name': name, 'mesh': len(meshes) - 1, 'translation': list(map(float, t)), 'rotation': mh.quat_of(Ry(ry))})
        nodes[0]['children'].append(len(nodes) - 1)
    while len(b) % 4: b.append(0)
    g = {'asset': {'version': '2.0', 'generator': 'claude-procedural magic school'}, 'extensionsUsed': ['KHR_materials_unlit'], 'scene': 0,
         'scenes': [{'name': '별빛 마법학교', 'nodes': [0]}], 'nodes': nodes, 'meshes': meshes,
         'materials': [{'name': 'Toon', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.9}},
                       {'name': 'Glow', 'alphaMode': 'BLEND', 'extensions': {'KHR_materials_unlit': {}}, 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1]}}],
         'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(b)}]}
    js = json.dumps(g, separators=(',', ':'), ensure_ascii=False).encode(); js += b' ' * (-len(js) % 4)
    return struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(b), 0x004E4942) + bytes(b), tris


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    groups, layout = build_all()
    data, tris = glb_small(groups); open(os.path.join(out, 'school.glb'), 'wb').write(data)
    splat().save(os.path.join(out, 'splat.png'), optimize=True)
    with open(os.path.join(out, 'school_layout.js'), 'w') as f:
        f.write('// 별빛 마법학교 배치: 건물·구역·실내·행동 자리·높이맵·단·막힌 곳·소품·등불\n')
        f.write('export default ' + json.dumps(layout, ensure_ascii=False, separators=(',', ':')) + ';\n')
    json.dump(sorted(set(p[0] for p in props)), open(os.path.join(out, 'props_used.json'), 'w'))
    print('tris', tris, 'bytes', len(data), 'props', len(props), 'blockers', len(blockers), 'lights', len(lights), {k: len(v) for k, v in spots.items()})
